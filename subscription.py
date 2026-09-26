import json
import os
import secrets
from datetime import date, datetime, timedelta

try:
    from zoneinfo import ZoneInfo
    TEHRAN = ZoneInfo("Asia/Tehran")
except Exception:
    TEHRAN = None

from storage import users_path
from users import get_user, update_user


PLANS = {
    "10": {"days": 10, "price": 20000, "title": "۱۰ روز"},
    "20": {"days": 20, "price": 35000, "title": "۲۰ روز"},
    "30": {"days": 30, "price": 50000, "title": "۳۰ روز (۱ ماه)"},
    "60": {"days": 60, "price": 80000, "title": "۶۰ روز (۲ ماه)"},
}

FREE_DAYS = 3
FREE_MAX_CHANNELS = 1
PAID_MAX_CHANNELS = 3
FREE_ALLOWED_CATEGORIES = ["ورزش", "آب‌وهوا"]
FREE_LOCKED_TIMES = {1, 5}
CARD_NUMBER = os.getenv("CARD_NUMBER", "6037-9975-1111-2222")
ADMIN_IDS = [595450272]

LICENSES_FILE = os.path.join(os.path.dirname(users_path()) or "data", "licenses.json")
PAYMENTS_FILE = os.path.join(os.path.dirname(users_path()) or "data", "payments.json")


def today_tehran():
    if TEHRAN:
        return datetime.now(TEHRAN).date()
    return date.today()


def _load_json(path, default):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data if isinstance(data, type(default)) else default
    except Exception:
        return default


def _save_json(path, data):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def load_licenses():
    return _load_json(LICENSES_FILE, {})


def save_licenses(data):
    _save_json(LICENSES_FILE, data)


def load_payments():
    return _load_json(PAYMENTS_FILE, {})


def save_payments(data):
    _save_json(PAYMENTS_FILE, data)


def parse_expire(value):
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except Exception:
        return None


def subscription_info(user_id):
    user = get_user(user_id) or {}
    sub = user.get("subscription") or {}
    kind = sub.get("type") or "none"
    expire = parse_expire(sub.get("expire"))
    total = int(sub.get("total_days") or 0)
    remaining = 0
    active = False
    if expire:
        remaining = max(0, (expire - today_tehran()).days)
        active = remaining > 0 or expire >= today_tehran()
        if expire >= today_tehran() and remaining == 0:
            remaining = 1
        if expire < today_tehran():
            active = False
            remaining = 0
            kind = "expired"
    if kind in (None, "none", "") and not active:
        kind = "none"
    return {
        "type": kind if active else ("none" if kind == "none" else "expired"),
        "active": active,
        "expire": expire.isoformat() if expire else None,
        "remaining": remaining if active else 0,
        "total": total or remaining,
        "label": "رایگان" if kind == "free" and active else ("پولی" if active else "ندارد"),
    }


def has_subscription(user_id):
    return subscription_info(user_id)["active"]


def is_free_user(user_id):
    info = subscription_info(user_id)
    return info["active"] and info["type"] == "free"


def max_channels_for(user_id):
    if not has_subscription(user_id):
        return 0
    return FREE_MAX_CHANNELS if is_free_user(user_id) else PAID_MAX_CHANNELS


def activate_subscription(user_id, kind, days):
    expire = today_tehran() + timedelta(days=int(days))
    update_user(user_id, {
        "subscription": {
            "type": kind,
            "expire": expire.isoformat(),
            "total_days": int(days),
        }
    })
    return True


def create_license(days):
    days = int(days)
    code = f"ANB-{days}-{secrets.token_hex(4).upper()}"
    licenses = load_licenses()
    licenses[code] = {"days": days, "used": False, "used_by": None}
    save_licenses(licenses)
    return code


def redeem_license(user_id, code):
    code = (code or "").strip().upper()
    licenses = load_licenses()
    item = licenses.get(code)
    if not item:
        return False, "کد لایسنس غلط است."
    if item.get("used"):
        return False, "این کد قبلاً استفاده شده است."
    days = int(item.get("days") or 0)
    if days <= 0:
        return False, "کد نامعتبر است."
    activate_subscription(user_id, "paid", days)
    item["used"] = True
    item["used_by"] = str(user_id)
    licenses[code] = item
    save_licenses(licenses)
    return True, days
