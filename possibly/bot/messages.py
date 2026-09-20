# POSSIBLY
# GIF caption processing

from __future__ import annotations

import io
import logging
import os
import tempfile

from PIL import Image, ImageDraw, ImageFont


logger = logging.getLogger("POSSIBLY.gif")


MAX_GIF_SIZE = 8 * 1024 * 1024
MAX_FRAMES = 120
MAX_TEXT_LENGTH = 250


def register(bot) -> None:
    logger.info("GIF handler registered")


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    font_candidates = [
        "C:/Windows/Fonts/tahoma.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf",
    ]

    for path in font_candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size=size)
            except OSError:
                continue

    return ImageFont.load_default()


def _fit_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    image_width: int,
    image_height: int,
) -> ImageFont.FreeTypeFont:
    max_width = int(image_width * 0.86)
    max_height = int(image_height * 0.25)

    size = max(
        18,
        min(
            72,
            image_width // 10,
        ),
    )

    while size > 14:
        font = _load_font(size)

        bbox = draw.multiline_textbbox(
            (0, 0),
            text,
            font=font,
            spacing=max(4, size // 5),
            align="center",
        )

        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]

        if width <= max_width and height <= max_height:
            return font

        size -= 2

    return _load_font(14)


def _wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
) -> str:
    words = text.split()

    if not words:
        return ""

    lines: list[str] = []
    current = ""

    for word in words:
        candidate = (
            word
            if not current
            else f"{current} {word}"
        )

        bbox = draw.textbbox(
            (0, 0),
            candidate,
            font=font,
        )

        width = bbox[2] - bbox[0]

        if width <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)

            current = word

    if current:
        lines.append(current)

    return "\n".join(lines)


def _draw_caption(
    image: Image.Image,
    text: str,
) -> Image.Image:
    image = image.convert("RGBA")

    draw = ImageDraw.Draw(image)

    font = _fit_font(
        draw,
        text,
        image.width,
        image.height,
    )

    text = _wrap_text(
        draw,
        text,
        font,
        int(image.width * 0.86),
    )

    bbox = draw.multiline_textbbox(
        (0, 0),
        text,
        font=font,
        spacing=max(4, font.size // 5),
        align="center",
        stroke_width=2,
    )

    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (image.width - text_width) / 2

    y = (
        image.height / 2
        - text_height / 2
        + image.height * 0.08
    )

    draw.multiline_text(
        (x, y),
        text,
        font=font,
        fill="white",
        stroke_width=2,
        stroke_fill="black",
        spacing=max(4, font.size // 5),
        align="center",
    )

    return image


def add_caption_to_gif(
    data: bytes,
    text: str,
) -> bytes:
    if len(data) > MAX_GIF_SIZE:
        raise ValueError(
            "GIF file is too large."
        )

    text = text.strip()

    if not text:
        raise ValueError(
            "Caption cannot be empty."
        )

    if len(text) > MAX_TEXT_LENGTH:
        raise ValueError(
            "Caption is too long."
        )

    source = Image.open(
        io.BytesIO(data)
    )

    frame_count = getattr(
        source,
        "n_frames",
        1,
    )

    frame_count = min(
        frame_count,
        MAX_FRAMES,
    )

    frames: list[Image.Image] = []
    durations: list[int] = []

    for index in range(frame_count):
        source.seek(index)

        frame = source.convert("RGBA")

        frame = _draw_caption(
            frame,
            text,
        )

        frames.append(frame)

        durations.append(
            source.info.get(
                "duration",
                100,
            )
        )

    if not frames:
        raise ValueError(
            "GIF contains no frames."
        )

    output = io.BytesIO()

    first = frames[0]

    first.save(
        output,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=source.info.get("loop", 0),
        disposal=2,
        optimize=False,
    )

    output.seek(0)

    return output.getvalue()


def save_processed_gif(
    data: bytes,
) -> str:
    """
    Save a processed GIF to a temporary file.

    The caller is responsible for deleting the file
    after the Bale upload has completed.
    """

    file = tempfile.NamedTemporaryFile(
        suffix=".gif",
        delete=False,
    )

    try:
        file.write(data)
        file.flush()
        return file.name
    finally:
        file.close()
