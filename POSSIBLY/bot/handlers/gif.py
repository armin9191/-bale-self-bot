"""GIF caption overlay with Persian/RTL support."""
from __future__ import annotations

import io
import logging
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
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except Exception:
        return text


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    path = Path(settings.FONT_PATH)
    if path.exists():
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


def process_gif(gif_bytes: bytes, caption: str) -> Optional[bytes]:
    if len(gif_bytes) > settings.MAX_GIF_BYTES:
        raise ValueError("حجم فایل بیش از حد مجاز است")

    caption = _reshape(caption.strip())
    if not caption:
        raise ValueError("متن خالی است")

    src = Image.open(io.BytesIO(gif_bytes))
    frames_out = []
    durations = []
    count = 0

    for frame in ImageSequence.Iterator(src):
        count += 1
        if count > settings.MAX_GIF_FRAMES:
            break
        im = frame.convert("RGBA")
        w, h = im.size
        if max(w, h) > settings.MAX_GIF_DIMENSION:
            ratio = settings.MAX_GIF_DIMENSION / max(w, h)
            im = im.resize((int(w * ratio), int(h * ratio)), Image.Resampling.LANCZOS)
            w, h = im.size

        draw = ImageDraw.Draw(im)
        size = max(18, min(w, h) // 10)
        font = _font(size)
        margin = max(8, w // 20)
        max_text_w = w - 2 * margin
        lines = _wrap(draw, caption, font, max_text_w)

        line_heights = []
        total_h = 0
        for line in lines:
            bb = draw.textbbox((0, 0), line, font=font)
            lh = bb[3] - bb[1]
            line_heights.append(lh)
            total_h += lh + 4

        # slightly below center
        y = int(h * 0.55) - total_h // 2
        y = max(margin, min(y, h - total_h - margin))

        for line, lh in zip(lines, line_heights):
            bb = draw.textbbox((0, 0), line, font=font)
            tw = bb[2] - bb[0]
            x = (w - tw) // 2
            # outline for readability
            for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1)):
                draw.text((x + ox, y + oy), line, font=font, fill=(0, 0, 0, 220))
            draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
            y += lh + 4

        frames_out.append(im.convert("P", palette=Image.Palette.ADAPTIVE))
        durations.append(frame.info.get("duration", 80) or 80)

    if not frames_out:
        raise ValueError("فریم معتبری پیدا نشد")

    out = io.BytesIO()
    frames_out[0].save(
        out,
        format="GIF",
        save_all=True,
        append_images=frames_out[1:],
        duration=durations,
        loop=0,
        optimize=False,
    )
    return out.getvalue()
