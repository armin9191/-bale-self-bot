"""Default auto-reply engine with fuzzy Persian matching."""
from __future__ import annotations

import random
import re
from typing import Optional

# --- normalize ---
def _norm(s: str) -> str:
    s = (s or "").strip().lower()
    s = s.replace("\u200c", "").replace("\u200f", "").replace("\u200e", "")
    s = s.replace("ك", "ک").replace("ي", "ی").replace("ة", "ه")
    s = s.replace("آ", "ا").replace("أ", "ا").replace("إ", "ا").replace("ؤ", "و").replace("ئ", "ی")
    # common typos
    s = s.replace("ث", "س")  # ثلام → سلام-ish
    s = s.replace("ً", "").replace("ٌ", "").replace("ٍ", "").replace("َ", "").replace("ُ", "").replace("ِ", "")
    s = re.sub(r"[!?.،,؛:…]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _compact(s: str) -> str:
    return re.sub(r"\s+", "", _norm(s))


# --- response pools ---
GREETINGS = [
    "سلاممم 🌸 امروز چطوری؟",
    "سلامم! خوش اومدی ✨ روزت چطور بود؟",
    "سلام علیکم 😊 چه خبر؟",
    "هاییی 👋 حال دلت خوبه؟",
    "سلاممممم امروز چطور بود؟ تعریف کن ببینم!",
    "سلام دوست من 💫 امیدوارم روزت عالی باشه",
    "سلام! من اینجام اگه کاری داشتی بگو 🤖",
]

BOREDOM = [
    "هی !! حوصله‌ت سر رفته؟ بیا بازی کنیم 🎮\nدوز · مافیا · جرعت حقیقت — تو راهنما هم هست!",
    "حوصله نداری؟ بیا دوز بازی کنیم یا مافیا راه بندازیم 🔥",
    "سر رفتن حوصله ممنوعه اینجا 😎 بنویس: دوز یا مافیا یا جرعت حقیقت",
    "هی بیا حواستو پرت کنیم! مافیا؟ دوز؟ یا جرعت حقیقت؟ خودت بگو!",
    "حوصله‌ت سر رفته؟ من آماده‌ام 💪 یکی از بازی‌ها رو استارت بزن.",
]

CREATOR = [
    "سازنده منو میگی؟ 🥹\nاون منو ساخته.",
    "درود بر سازنده من 🥹✨",
    "آره در مورد سازنده‌م حرف می‌زنی… درود بر اون 🙏",
    "سازنده منو یاد کردی؟ دمت گرم 🥹 اون منو ساخته.",
]

BOT_MENTION = [
    "جانم در خدمتم 🫡",
    "بفرما ارباب، در خدمتم 👑",
    "دستور چیه؟",
    "بفرمایید ✨",
    "بگو 🥹",
    "بله... 💆",
    "امروز یکم حال ندارم؛ جدی میشه خودت انجام بده کاراتو، فکنم باید ریکاوری کنم خودمو 😓😷",
    "بله قربان، گوش به فرمانم 🤖",
]

# pattern groups: (name, matcher_fn or keywords, responses)
def _match_greeting(n: str, c: str) -> bool:
    keys = ("سلام", "سالام", "سلامم", "سلوم", "درود", "hi", "hello", "hey", "سلاممم")
    if c in ("سلام", "سالام", "سلوم", "درود", "hi", "hello", "hey"):
        return True
    for k in keys:
        if k in n or _compact(k) in c:
            # avoid matching inside long unrelated text if too long
            if len(n) <= 40:
                return True
    return False


def _match_boredom(n: str, c: str) -> bool:
    keys = (
        "حوصلم سر رفت", "حوصله م سر رفت", "حوصلم سررفته", "حوصله ندارم",
        "حوصلم", "حوصله", "حوص", "کسل", "کسلم", "حوصله‌م", "boredom", "bored",
        "سر رفته", "سررفتم",
    )
    for k in keys:
        kn = _norm(k)
        kc = _compact(k)
        if kn in n or kc in c:
            return True
    # partial حوصل / حوصله
    if "حوص" in c or "کسل" in c:
        return True
    return False


def _match_creator(n: str, c: str) -> bool:
    keys = (
        "دارکنایت", "دارک نایت", "darknight", "dark night", "dark_night",
        "استدیو", "استودیو", "studio",
        "کامندر", "کوماندر", "commander", "کومندر",
        "آرتین", "ارتین", "artin", "aartin",
        "سازنده ربات", "سازنده بات",
    )
    for k in keys:
        if _norm(k) in n or _compact(k) in c:
            return True
    return False


def _match_bot(n: str, c: str) -> bool:
    # whole-ish mentions of bot
    if c in ("بات", "ربات", "bot", "robot", "بات؟", "ربات؟"):
        return True
    # short messages containing بات/ربات as main word
    if len(n) <= 25:
        for k in ("بات", "ربات", "bot", "possibly", "پازیبلی", "پوسیبیلی"):
            if _norm(k) in n or _compact(k) in c:
                # avoid matching inside learning commands etc - caller filters
                return True
    return False


def pick_auto_reply(text: str) -> Optional[str]:
    """Return a random reply string or None."""
    if not text or len(text) > 120:
        return None
    n = _norm(text)
    c = _compact(text)
    if not n:
        return None

    # priority: creator > boredom > greeting > bot
    if _match_creator(n, c):
        return random.choice(CREATOR)
    if _match_boredom(n, c):
        return random.choice(BOREDOM)
    if _match_greeting(n, c):
        return random.choice(GREETINGS)
    if _match_bot(n, c):
        return random.choice(BOT_MENTION)
    return None
