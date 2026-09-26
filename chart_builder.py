import os
import struct
import zlib


DIGIT = {
    "0": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00110", "01000", "10000", "11111"],
    "3": ["01110", "10001", "00001", "00110", "00001", "10001", "01110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["01110", "10000", "11110", "10001", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00001", "01110"],
    ":": ["00000", "00100", "00100", "00000", "00100", "00100", "00000"],
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    "@": ["01110", "10001", "10101", "10101", "10110", "10000", "01110"],
    "_": ["00000", "00000", "00000", "00000", "00000", "00000", "11111"],
}


def _put(pixels, width, height, x, y, color):
    if 0 <= x < width and 0 <= y < height:
        pixels[y * width + x] = color


def _text(pixels, width, height, x, y, text, color, scale=2):
    cursor = x
    for char in str(text).upper():
        glyph = DIGIT.get(char)
        if glyph is None:
            cursor += 6 * scale
            continue
        for row, line in enumerate(glyph):
            for col, bit in enumerate(line):
                if bit == "1":
                    for dy in range(scale):
                        for dx in range(scale):
                            _put(pixels, width, height, cursor + col * scale + dx, y + row * scale + dy, color)
        cursor += 6 * scale
    return cursor


def _png(path, width, height, pixels):
    raw = b""
    for y in range(height):
        raw += b"\x00"
        start = y * width
        for r, g, b in pixels[start:start + width]:
            raw += bytes((r, g, b))
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "wb") as file:
        file.write(png)
    return path


def render_stats_image(report, out_path):
    width, height = 900, 720
    bg = (15, 23, 42)
    panel = (17, 24, 39)
    line = (51, 65, 85)
    text = (248, 250, 252)
    muted = (148, 163, 184)
    gold = (251, 191, 36)
    bar_color = (56, 189, 248)
    pixels = [bg] * (width * height)

    def fill(x1, y1, x2, y2, color):
        for y in range(y1, y2):
            for x in range(x1, x2):
                _put(pixels, width, height, x, y, color)

    fill(20, 20, width - 20, 210, panel)
    _text(pixels, width, height, 40, 40, str(report["channel_id"]), text, 3)
    clock = report["now"].strftime("%H:%M")
    _text(pixels, width, height, 40, 90, f"00:00 - {clock}", (147, 197, 253), 2)

    cards = [
        ("TODAY", report["users_today"]),
        ("7D", report["users_7"]),
        ("30D", report["users_30"]),
        ("MEMBERS", report["members"]),
        ("POSTS", report["messages_today"]),
    ]
    for index, (label, value) in enumerate(cards):
        x = 40 + index * 170
        _text(pixels, width, height, x, 140, label, muted, 2)
        _text(pixels, width, height, x, 170, str(value), gold, 3)

    chart_x1, chart_y1, chart_x2, chart_y2 = 50, 250, width - 40, height - 50
    fill(chart_x1, chart_y1, chart_x2, chart_y2, panel)
    for y in range(chart_y1, chart_y2, 50):
        fill(chart_x1, y, chart_x2, y + 1, line)

    hours = report["hours"] or [0]
    values = report["hourly"] or [0]
    max_value = max(values) if max(values) > 0 else 1
    count = len(hours)
    usable = chart_x2 - chart_x1 - 20
    bar_w = max(8, usable // max(count, 1) - 6)
    for index, (hour, value) in enumerate(zip(hours, values)):
        x = chart_x1 + 12 + index * (bar_w + 6)
        bar_h = int((value / max_value) * (chart_y2 - chart_y1 - 70))
        y = chart_y2 - 40 - bar_h
        fill(x, y, x + bar_w, chart_y2 - 40, bar_color)
        _text(pixels, width, height, x, chart_y2 - 30, f"{hour:02d}", muted, 1)
        if value:
            _text(pixels, width, height, x, y - 18, str(value), text, 1)

    return _png(out_path, width, height, pixels)


def render_stats_text(report):
    now = report["now"]
    clock = now.strftime("%H:%M")
    lines = [
        f"📊 آمار {report['channel_id']}",
        f"⏰ از ۰۰:۰۰ تا {clock}",
        "",
        f"👥 کاربرای امروز: {report['users_today']}",
        f"📅 7 روز: {report['users_7']}",
        f"📆 30 روز: {report['users_30']}",
        f"📢 کل اعضا: {report['members']}",
        f"💬 پیام‌های امروز: {report['messages_today']}",
        "",
        "📈 پیام هر ساعت:",
    ]
    max_value = max(report["hourly"] or [0]) or 1
    for hour, value in zip(report["hours"], report["hourly"]):
        blocks = int(round((value / max_value) * 10)) if value else 0
        bar = "█" * blocks or "·"
        lines.append(f"{hour:02d}:00  {bar}  {value}")
    return "\n".join(lines)
