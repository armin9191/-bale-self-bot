"""Truth or Dare engine — pure logic."""
from __future__ import annotations

import random
from typing import Any

TRUTHS = [
    "آخرین باری که دروغ گفتی کی بود؟",
    "بزرگ‌ترین ترس تو چیست؟",
    "اگر یک روز می‌توانستی نامرئی باشی چه می‌کردی؟",
    "عجیب‌ترین غذایی که خورده‌ای؟",
    "اگر می‌توانستی شغل فعلی‌ات را عوض کنی چه شغلی انتخاب می‌کردی؟",
]

DARES = [
    "یک ایموجی تصادفی بفرست و توضیح بده چرا.",
    "برای ۳۰ ثانیه فقط با ایموجی حرف بزن.",
    "یک تعریف صادقانه از نفر سمت راستت بگو.",
    "یک جوک کوتاه تعریف کن.",
    "بگو آخرین آهنگی که گوش دادی چه بود.",
]


def new_tod_state(creator_id: int) -> dict[str, Any]:
    return {
        "phase": "lobby",
        "creator_id": creator_id,
        "players": [],
        "current_index": 0,
        "used_truths": [],
        "used_dares": [],
    }


def pick_item(kind: str, used: list[int]) -> tuple[str, int]:
    pool = TRUTHS if kind == "truth" else DARES
    available = [i for i in range(len(pool)) if i not in used]
    if not available:
        available = list(range(len(pool)))
        used.clear()
    idx = random.choice(available)
    used.append(idx)
    return pool[idx], idx
