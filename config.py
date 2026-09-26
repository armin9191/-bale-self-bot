# ==========================
# AutoNewsBot Config v2.5
# ==========================

import os

BOT_TOKEN = os.getenv(
    "BALE_BOT_TOKEN",
    "1159197217:ZwrWy4kXoTdu7hSMHMWjjaQKm-uM1qlUCYs",
)

USERS_FILE = "data/users.json"
SENT_NEWS_FILE = "data/sent_news.json"

MAX_SENT_NEWS = 5000
CHECK_EMPTY_INTERVAL = 60
SEND_INTERVALS = [300, 600]
MAX_CHANNELS = 3
RSS_CACHE_SECONDS = 45
FORBIDDEN_COOLDOWN = 1800
MAX_NEWS_AGE_SECONDS = 45 * 60
FALLBACK_NEWS_AGE_SECONDS = 3 * 60 * 60

CATEGORY_FEEDS = {
    "ورزش": [
        "https://www.mehrnews.com/rss/tp/9",
        "https://www.isna.ir/rss/tp/24",
        "https://www.isna.ir/rss/tp/119",
    ],
    "جنگ": [
        "https://www.mehrnews.com/rss/tp/39",
        "https://www.isna.ir/rss/tp/407",
        "https://www.irna.ir/rss/tp/9",
        "https://www.imna.ir/rss/tp/144",
        "https://defapress.ir/fa/rss/38",
    ],
    "آب‌وهوا": [
        "https://www.isna.ir/rss/tp/62",
        "https://www.imna.ir/rss/tp/153",
    ],
    "اقتصاد": [
        "https://www.mehrnews.com/rss/tp/20",
        "https://www.irna.ir/rss/tp/20",
        "https://www.isna.ir/rss/tp/34",
        "https://www.sena.ir/rss",
    ],
    "فناوری": [
        "https://www.zoomit.ir/feed/",
        "https://www.isna.ir/rss/tp/41",
    ],
    "سیاسی": [
        "https://www.mehrnews.com/rss/tp/7",
        "https://www.isna.ir/rss/tp/14",
        "https://www.irna.ir/rss/tp/5",
    ],
}

RSS_FEEDS = []
for _feeds in CATEGORY_FEEDS.values():
    for _url in _feeds:
        if _url not in RSS_FEEDS:
            RSS_FEEDS.append(_url)

CATEGORY_RULES = {
    "ورزش": {
        "sources": ["rss/tp/9", "rss/tp/24", "rss/tp/119"],
        "keywords": ["فوتبال", "والیبال", "بسکتبال", "لیگ برتر", "لیگ", "جام جهانی", "بازیکن", "مربی", "قهرمانی", "استقلال", "پرسپولیس", "ورزش", "تیم ملی", "داور"],
        "negative": ["موشک", "پهپاد", "هواشناسی", "بارش باران"],
    },
    "اقتصاد": {
        "sources": ["sena.ir", "rss/tp/20", "rss/tp/34"],
        "keywords": ["دلار", "طلا", "سکه", "بورس", "ارز", "اقتصاد", "تورم", "نرخ ارز", "بانک مرکزی", "نفت"],
        "negative": ["فوتبال", "هواشناسی", "جنگنده"],
    },
    "جنگ": {
        "sources": ["defapress", "rss/tp/39", "rss/tp/407", "rss/tp/9", "rss/tp/144"],
        "keywords": ["حمله نظامی", "حمله موشکی", "موشک", "پهپاد", "ارتش", "عملیات نظامی", "درگیری مسلحانه", "جنگنده", "تجاوز نظامی", "شهادت", "بمباران", "پدافند", "غزه", "لبنان", "سپاه"],
        "negative": ["هواشناسی", "بارش باران", "فوتبال", "لیگ برتر", "استقلال"],
    },
    "فناوری": {
        "sources": ["zoomit", "rss/tp/41"],
        "keywords": ["گوشی", "موبایل", "لپ تاپ", "هوش مصنوعی", "تکنولوژی", "اینترنت", "نرم افزار", "اپلیکیشن"],
        "negative": ["موشک", "فوتبال"],
    },
    "سیاسی": {
        "sources": ["rss/tp/7", "rss/tp/14", "rss/tp/5"],
        "keywords": ["مجلس", "دولت", "وزیر", "هیئت دولت", "رئیس جمهور", "انتخابات", "نماینده مجلس", "سیاست خارجی"],
        "negative": ["فوتبال", "هواشناسی", "موشک"],
    },
    "آب‌وهوا": {
        "sources": ["rss/tp/62", "rss/tp/153"],
        "keywords": ["هواشناسی", "پیش بینی هوا", "پیش‌بینی هوا", "وضعیت هوا", "بارش باران", "بارش برف", "سامانه بارشی", "هشدار هواشناسی", "هشدار زرد", "هشدار نارنجی", "هشدار قرمز", "وزش باد شدید", "کاهش دما", "افزایش دما", "گرد و غبار", "آلودگی هوا", "رگبار", "تگرگ", "طوفان", "سیلاب"],
        "negative": ["موشک", "پهپاد", "فوتبال", "دلار", "بورس"],
        "require_iran": True,
    },
}

IRAN_HINTS = [
    "ایران", "کشور", "استان", "تهران", "مشهد", "اصفهان", "شیراز",
    "تبریز", "اهواز", "کرج", "قم", "کرمان", "گیلان", "مازندران",
    "آذربایجان", "خراسان", "خوزستان", "سازمان هواشناسی",
]

FORCE_JOIN_ENABLED = True
FORCE_JOIN_CHANNELS = [{"id": 5156805259, "username": "@adminbots_ir"}]
