from __future__ import annotations
import random
from typing import Any

TRUTHS = [
    "آخرین باری که دروغ گفتی کی بود؟",
    "بزرگ‌ترین ترس تو چیست؟",
    "اگر یک روز نامرئی بودی چه می‌کردی؟",
    "عجیب‌ترین غذایی که خورده‌ای؟",
    "اگر شغلت را عوض کنی چه کاری انتخاب می‌کنی؟",
    "آخرین پیام خوانده‌نشده‌ات از کیست؟",
    "یک راز کوچک از خودت بگو.",
]

DARES = [
    "یک ایموجی تصادفی بفرست و توضیح بده.",
    "۳۰ ثانیه فقط با ایموجی حرف بزن.",
    "یک تعریف صادقانه از یکی از بازیکن‌ها بگو.",
    "یک جوک کوتاه تعریف کن.",
    "آخرین آهنگی که گوش دادی را بگو.",
    "یک جمله با لهجه محلی بگو.",
]


def new_state(creator_id: int) -> dict[str, Any]:
    return {
        "phase": "lobby",
        "creator_id": creator_id,
        "players": [creator_id],
        "current_index": 0,
        "used_truths": [],
        "used_dares": [],
        "last_item": None,
    }


def pick(kind: str, used: list[int]) -> tuple[str, int]:
    pool = TRUTHS if kind == "truth" else DARES
    available = [i for i in range(len(pool)) if i not in used]
    if not available:
        used.clear()
        available = list(range(len(pool)))
    idx = random.choice(available)
    used.append(idx)
    return pool[idx], idx
