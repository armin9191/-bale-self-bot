"""GIF / animation caption overlay with Persian/RTL support."""
from __future__ import annotations

import io
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont, ImageSequence

from config import settings

log = logging.getLogger("POSSIBLY.gif")

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_ARABIC = True
except ImportError:
    HAS_ARABIC = False


def _reshape(text: str) -> str:
    if not HAS_ARABIC:
        return text
    try:
        return get_display(arabic_reshaper.reshape(text))
    except Exception:
        return text


def _font(size: int) -> ImageFont.ImageFont:
    path = Path(settings.FONT_PATH)
    if not path.is_file():
        # try relative to cwd and package
        for cand in (
            Path("assets/fonts/Vazirmatn-Regular.ttf"),
            Path(__file__).resolve().parents[2] / "assets/fonts/Vazirmatn-Regular.ttf",
        ):
            if cand.is_file():
                path = cand
                break
    if path.is_file():
        try:
            return ImageFont.truetype(str(path), size=size)
        except Exception as e:
            log.warning("font load failed: %s", e)
    return ImageFont.load_default()


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_w: int) -> list[str]:
    words = text.split()
    if not words:
        return [text]
    lines: list[str] = []
    cur = words[0]
    for w in words[1:]:
        trial = f"{cur} {w}"
        bbox = draw.textbbox((0, 0), trial, font=font)
        if bbox[2] - bbox[0] <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def _magic(data: bytes) -> str:
    if len(data) < 12:
        return "unknown"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:3] == b"\xff\xd8\xff":
        return "jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    if data[4:8] == b"ftyp":
        return "mp4"
    # HTML/JSON error pages from bad download
    head = data[:200].lstrip().lower()
    if head.startswith(b"<") or head.startswith(b"{") or head.startswith(b"<!doctype"):
        return "text"
    return "unknown"


def _mp4_to_gif_bytes(data: bytes) -> bytes:
    """Convert MP4 animation to GIF via ffmpeg if available."""
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "in.mp4"
        dst = Path(td) / "out.gif"
        src.write_bytes(data)
        cmd = [
            "ffmpeg", "-y", "-i", str(src),
            "-vf", "fps=12,scale=min(480\\,iw):-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
            "-loop", "0",
            str(dst),
        ]
        proc = subprocess.run(cmd, capture_output=True, timeout=60)
        if proc.returncode != 0 or not dst.is_file() or dst.stat().st_size == 0:
            raise ValueError(
                "این فایل گیف واقعی نیست (احتمالاً MP4 است) و تبدیل با ffmpeg ممکن نشد. "
                "یک GIF معمولی بفرست یا ffmpeg را روی سرور نصب کن."
            )
        return dst.read_bytes()


def _draw_caption_on_rgba(im: Image.Image, caption: str) -> Image.Image:
    w, h = im.size
    if max(w, h) > settings.MAX_GIF_DIMENSION:
        ratio = settings.MAX_GIF_DIMENSION / max(w, h)
        im = im.resize((int(w * ratio), int(h * ratio)), Image.Resampling.LANCZOS)
        w, h = im.size

    draw = ImageDraw.Draw(im)
    size = max(18, min(w, h) // 10)
    font = _font(size)
    margin = max(8, w // 20)
    lines = _wrap(draw, caption, font, w - 2 * margin)

    line_heights = []
    total_h = 0
    for line in lines:
        bb = draw.textbbox((0, 0), line, font=font)
        lh = bb[3] - bb[1]
        line_heights.append(lh)
        total_h += lh + 4

    y = int(h * 0.55) - total_h // 2
    y = max(margin, min(y, h - total_h - margin))

    for line, lh in zip(lines, line_heights):
        bb = draw.textbbox((0, 0), line, font=font)
        tw = bb[2] - bb[0]
        x = (w - tw) // 2
        for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1)):
            draw.text((x + ox, y + oy), line, font=font, fill=(0, 0, 0, 220))
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
        y += lh + 4
    return im


def process_gif(gif_bytes: bytes, caption: str) -> Optional[bytes]:
    if not gif_bytes:
        raise ValueError("فایل خالی دریافت شد")
    if len(gif_bytes) > settings.MAX_GIF_BYTES:
        raise ValueError("حجم فایل بیش از حد مجاز است (حداکثر ۸ مگابایت)")

    kind = _magic(gif_bytes)
    log.info("media magic=%s size=%s", kind, len(gif_bytes))

    if kind == "text":
        raise ValueError("دانلود فایل ناموفق بود (پاسخ متنی از سرور بله). file_id را بررسی کن.")
    if kind == "mp4":
        gif_bytes = _mp4_to_gif_bytes(gif_bytes)
        kind = "gif"
    if kind == "unknown":
        # still try Pillow; may work for some formats
        pass

    caption = _reshape(caption.strip())
    if not caption:
        raise ValueError("متن خالی است")

    try:
        src = Image.open(io.BytesIO(gif_bytes))
    except Exception as e:
        raise ValueError(
            f"فرمت فایل پشتیبانی نمی‌شود ({kind}). یک GIF واقعی بفرست. جزئیات: {e}"
        ) from e

    frames_out: list[Image.Image] = []
    durations: list[int] = []
    count = 0

    try:
        iterator = ImageSequence.Iterator(src)
        for frame in iterator:
            count += 1
            if count > settings.MAX_GIF_FRAMES:
                break
            im = _draw_caption_on_rgba(frame.convert("RGBA"), caption)
            frames_out.append(im.convert("P", palette=Image.Palette.ADAPTIVE))
            durations.append(int(frame.info.get("duration", 80) or 80))
    except Exception:
        # single-frame image (png/jpeg/webp)
        im = _draw_caption_on_rgba(src.convert("RGBA"), caption)
        frames_out.append(im.convert("P", palette=Image.Palette.ADAPTIVE))
        durations.append(100)

    if not frames_out:
        raise ValueError("فریم معتبری پیدا نشد")

    out = io.BytesIO()
    frames_out[0].save(
        out,
        format="GIF",
        save_all=True,
        append_images=frames_out[1:] if len(frames_out) > 1 else [],
        duration=durations,
        loop=0,
        optimize=False,
    )
    return out.getvalue()
