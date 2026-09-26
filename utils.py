import re

CHANNEL_SIGNATURE = "- [x] *@akhbartareek*"

CATEGORY_EMOJI = {
    "جنگ": "🚨",
    "آب‌وهوا": "🌬",
    "اقتصاد": "💵",
    "ورزش": "⚽",
    "فناوری": "💻",
    "سیاسی": "🏛",
}


def clean_text(text):
    if not isinstance(text, str):
        return ""
    return re.sub(r"\s+", " ", text).strip()


def add_emoji(title, category=None):
    title = clean_text(title)
    emoji = CATEGORY_EMOJI.get(category, "📰")
    if title.startswith(emoji):
        return title
    return f"{emoji} {title}"


def format_news(title):
    title = clean_text(title)
    return f"{title}\n{CHANNEL_SIGNATURE}"
