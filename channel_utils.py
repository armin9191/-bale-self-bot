import re
import requests

from config import BOT_TOKEN

BASE_URL = f"https://tapi.bale.ai/bot{BOT_TOKEN}"


def bot_user_id():
    try:
        return int(str(BOT_TOKEN).split(":", 1)[0])
    except Exception:
        return None


def normalize_channel_id(raw):
    text = (raw or "").strip()
    if not text:
        return None
    text = text.replace("https://ble.ir/", "").replace("http://ble.ir/", "")
    text = text.replace("ble.ir/", "").replace("https://bale.ai/", "")
    text = text.split("?")[0].strip().strip("/")
    text = text.split("/")[0].strip()
    text = text.lstrip("@").strip()
    if not text:
        return None
    if text.lstrip("-").isdigit():
        return text
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{3,31}", text):
        return None
    return "@" + text


def _api(method, payload):
    try:
        response = requests.post(f"{BASE_URL}/{method}", json=payload, timeout=10)
        data = response.json()
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def channel_exists(channel_id):
    data = _api("getChat", {"chat_id": channel_id})
    if not data.get("ok"):
        return False, data.get("description") or "کانال پیدا نشد"
    result = data.get("result") or {}
    if str(result.get("type") or "") != "channel":
        return False, "این آیدی کانال نیست"
    return True, result


def bot_is_admin(channel_id):
    user_id = bot_user_id()
    if not user_id:
        return False, "توکن ربات نامعتبر است"
    data = _api("getChatMember", {"chat_id": channel_id, "user_id": user_id})
    if not data.get("ok"):
        return False, "ربات عضو یا ادمین کانال نیست"
    status = str((data.get("result") or {}).get("status") or "")
    if status not in ("creator", "administrator"):
        return False, "ربات باید ادمین کانال باشد"
    return True, status
