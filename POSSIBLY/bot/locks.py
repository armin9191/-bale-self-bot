"""Group content locks + profanity filter."""
from __future__ import annotations

import re
import time
from typing import Optional

# Canonical lock keys → display label
LOCK_LABELS: dict[str, str] = {
    "عکس": "📸 عکس",
    "ویدیو": "🎞️ ویدیو",
    "آهنگ": "🎧 آهنگ",
    "ویس": "🎼 ویس",
    "استیکر": "🎟️ استیکر",
    "گیف": "🎬 گیف",
    "لینک": "🌐 لینک",
    "فوروارد": "📥 فوروارد",
    "متن": "📝 متن",
    "مکان": "📍 مکان",
    "اسپم": "💢 اسپم",
    "یوزرنیم": "🆔 یوزرنیم",
    "هشتگ": "✳️ هشتگ",
    "ریپلای": "🔄 ریپلای",
    "مخاطب": "👥 مخاطب",
    "فحش": "🤬 فحش",
    "بازی": "🎮 بازی",
    "انگلیسی": "🔠 انگلیسی",
}

# Aliases → canonical key
_ALIASES: dict[str, str] = {
    "عکس": "عکس", "photo": "عکس", "تصویر": "عکس", "عکس‌ها": "عکس",
    "ویدیو": "ویدیو", "ویدئو": "ویدیو", "video": "ویدیو", "فیلم": "ویدیو",
    "آهنگ": "آهنگ", "موزیک": "آهنگ", "music": "آهنگ", "audio": "آهنگ", "صدا": "آهنگ",
    "ویس": "ویس", "voice": "ویس", "صوت": "ویس",
    "استیکر": "استیکر", "sticker": "استیکر", "استیکر‌ها": "استیکر",
    "گیف": "گیف", "gif": "گیف", "انیمیشن": "گیف", "animation": "گیف",
    "لینک": "لینک", "link": "لینک", "url": "لینک", "آدرس": "لینک",
    "فوروارد": "فوروارد", "forward": "فوروارد", "فور": "فوروارد",
    "متن": "متن", "text": "متن", "پیام": "متن",
    "مکان": "مکان", "لوکیشن": "مکان", "location": "مکان",
    "اسپم": "اسپم", "spam": "اسپم",
    "یوزرنیم": "یوزرنیم", "یوزر": "یوزرنیم", "username": "یوزرنیم", "آیدی": "یوزرنیم",
    "هشتگ": "هشتگ", "هشتگ‌ها": "هشتگ", "hashtag": "هشتگ",
    "ریپلای": "ریپلای", "reply": "ریپلای", "پاسخ": "ریپلای",
    "مخاطب": "مخاطب", "کانتکت": "مخاطب", "contact": "مخاطب",
    "فحش": "فحش", "ناسزا": "فحش", "بدزبانی": "فحش", "profanity": "فحش",
    "بازی": "بازی", "game": "بازی", "گیم": "بازی",
    "انگلیسی": "انگلیسی", "english": "انگلیسی", "اینگلیش": "انگلیسی",
}


def resolve_lock_key(raw: str) -> Optional[str]:
    if not raw:
        return None
    s = raw.strip().lower().replace("\u200c", "").replace(" ", "")
    # try direct
    for k, v in _ALIASES.items():
        kn = k.lower().replace("\u200c", "").replace(" ", "")
        if s == kn:
            return v
    # startswith soft match
    for k, v in _ALIASES.items():
        kn = k.lower().replace("\u200c", "").replace(" ", "")
        if s.startswith(kn) or kn.startswith(s):
            return v
    return None


# ---- Profanity (Persian common insults — levels mild→severe) ----
# Normalized: remove ZWNJ, arabic/persian variants handled at check time
_PROFANITY_RAW = [
    # mild / common
    "کص", "کس", "کون", "کیر", "کیری", "جنده", "جنده‌", "حرومزاده", "حرامزاده",
    "حرومی", "لاشی", "لاش", "گوه", "گوه بخور", "گوهخور", "عن", "عنتر",
    "آشغال", "گاو", "الاغ", "خر", "خنگ", "احمق", "ابله", "دیوث", "قرمساق",
    "مادرجنده", "ننه جنده", "ننهٔ جنده", "خواهرجنده", "خواهر جنده",
    "کصکش", "کصکش", "کسکش", "کون‌کش", "کونکش", "کیرم", "کیرتو",
    "گاییدم", "گایید", "می‌گامت", "میگامت", "بگا", "بگا رفت",
    "بی‌شرف", "بی شرف", " بیشرف", "بی‌غیرت", "بی غیرت",
    "کونی", "کیری", "کصخل", "کسخل", "کون‌ده", "کونده",
    "سکس", "sexy", "fuck", "fucker", "shit", "bitch", "asshole", "dick",
    "pussy", "cunt", "whore", "slut", "motherfucker", "mf",
    "ناموستو", "ناموست", "به ناموست", "بیناموس", "بی ناموس",
    "فاک", "فاکر", "شاش", "شاشیدم", "ریدم", "ریدی",
    "جق", "جقی", "جق‌زن", "کص‌ننت", "کس ننت", "کصمادرت", "کس مادرت",
    "ننتو گاییدم", "مادرتو", "باباتو", "خواهرتو",
    "تخم", "تخمی", "بکیر", "بکیرم",
    "سیکتیر", "سیک تیر", "گمشو", "برو گمشو",
    "پفیوز", "هیز", "هرزه", "فاسد",
    "کصده", "کسده", "کصکش", "ننه کس", "ننه کص",
    "گایدی", "گاییدن", "می‌کنمت", "میکنمت",
]

def _norm_fa(s: str) -> str:
    s = s.lower()
    s = s.replace("\u200c", "").replace("\u200f", "").replace("\u200e", "")
    s = s.replace("ك", "ک").replace("ي", "ی").replace("ة", "ه")
    s = s.replace("آ", "ا").replace("أ", "ا").replace("إ", "ا").replace("ؤ", "و")
    # collapse spaces
    s = re.sub(r"\s+", "", s)
    return s


_PROFANITY_NORM = sorted({_norm_fa(x) for x in _PROFANITY_RAW if x}, key=len, reverse=True)

_LINK_RE = re.compile(
    r"(https?://|www\.|t\.me/|telegram\.me/|ble\.ir/|instagram\.com/|youtu\.be/|youtube\.com/)",
    re.I,
)
_HASHTAG_RE = re.compile(r"(^|\s)#[\w\u0600-\u06FF]+")
_USERNAME_RE = re.compile(r"(^|[^\w])@[\w\d_]{3,}")
_LATIN_RE = re.compile(r"[A-Za-z]")
_SPAM_WINDOW = 8.0
_SPAM_MAX = 5
_spam_hits: dict[int, list[float]] = {}


def spam_hit(user_id: int) -> bool:
    now = time.time()
    arr = _spam_hits.setdefault(user_id, [])
    arr.append(now)
    _spam_hits[user_id] = [t for t in arr if now - t <= _SPAM_WINDOW]
    return len(_spam_hits[user_id]) > _SPAM_MAX


def has_profanity(text: str) -> bool:
    if not text:
        return False
    n = _norm_fa(text)
    for w in _PROFANITY_NORM:
        if w and w in n:
            return True
    return False


def has_link(text: str) -> bool:
    return bool(text and _LINK_RE.search(text))


def has_hashtag(text: str) -> bool:
    return bool(text and _HASHTAG_RE.search(text))


def has_username(text: str) -> bool:
    return bool(text and _USERNAME_RE.search(text))


def has_english(text: str) -> bool:
    if not text:
        return False
    # if more than 3 latin letters → lock
    return len(_LATIN_RE.findall(text)) >= 3


def is_game_command(text: str) -> bool:
    if not text:
        return False
    t = text.strip().split()[0] if text.strip() else ""
    games = ("دوز", "مافیا", "جرعت", "حقیقت", "بازی")
    return any(t.startswith(g) for g in games)


def detect_violation(message, text: str, locks: dict[str, bool]) -> Optional[str]:
    """
    Return canonical lock key if message violates an enabled lock.
    Admins are exempt (caller must check).
    """
    if not locks:
        return None
    enabled = {k for k, v in locks.items() if v}

    # media attributes on bale Message
    def has(attr: str) -> bool:
        v = getattr(message, attr, None)
        return v is not None

    if "عکس" in enabled and (has("photo") or has("photos")):
        return "عکس"
    if "ویدیو" in enabled and has("video"):
        return "ویدیو"
    if "آهنگ" in enabled and (has("audio") or has("document") and _is_audio_doc(message)):
        return "آهنگ"
    if "ویس" in enabled and has("voice"):
        return "ویس"
    if "استیکر" in enabled and has("sticker"):
        return "استیکر"
    if "گیف" in enabled and (has("animation") or has("gif")):
        return "گیف"
    if "مکان" in enabled and (has("location") or has("venue")):
        return "مکان"
    if "مخاطب" in enabled and has("contact"):
        return "مخاطب"
    if "فوروارد" in enabled and (
        getattr(message, "forward_from", None) is not None
        or getattr(message, "forward_from_chat", None) is not None
        or getattr(message, "forward_date", None) is not None
    ):
        return "فوروارد"
    if "ریپلای" in enabled and getattr(message, "reply_to_message", None) is not None:
        # allow bot command replies? still lock pure reply spam — keep strict
        return "ریپلای"
    if text:
        if "لینک" in enabled and has_link(text):
            return "لینک"
        if "هشتگ" in enabled and has_hashtag(text):
            return "هشتگ"
        if "یوزرنیم" in enabled and has_username(text):
            return "یوزرنیم"
        if "فحش" in enabled and has_profanity(text):
            return "فحش"
        if "انگلیسی" in enabled and has_english(text):
            return "انگلیسی"
        if "بازی" in enabled and is_game_command(text):
            return "بازی"
        if "متن" in enabled:
            # pure text with no media
            if not any(
                has(a)
                for a in ("photo", "photos", "video", "audio", "voice", "sticker", "animation", "document", "location", "contact")
            ):
                return "متن"
    if "اسپم" in enabled:
        uid = None
        au = getattr(message, "author", None) or getattr(message, "from_user", None)
        if au is not None:
            uid = getattr(au, "id", None)
        if uid is not None and spam_hit(int(uid)):
            return "اسپم"
    return None


def _is_audio_doc(message) -> bool:
    doc = getattr(message, "document", None)
    if doc is None:
        return False
    name = (getattr(doc, "file_name", None) or "").lower()
    return any(name.endswith(ext) for ext in (".mp3", ".m4a", ".ogg", ".wav", ".flac"))


def format_locks_status(locks: dict[str, bool]) -> str:
    lines = ["*🔵 قفل‌های عمومی*", ""]
    for key, label in LOCK_LABELS.items():
        on = locks.get(key, False)
        mark = "🔒" if on else "🔓"
        lines.append(f"{mark} {label}")
    lines.append("")
    lines.append("🔹 قفل [مورد]  |  بازکردن [مورد]")
    return "\n".join(lines)
