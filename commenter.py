import time

import requests

from config import BOT_TOKEN
from users import _patch_channel

BASE_URL = f"https://tapi.bale.ai/bot{BOT_TOKEN}"
_LINKED = {}


def _call(method, payload):
    try:
        response = requests.post(f"{BASE_URL}/{method}", json=payload, timeout=10)
        try:
            data = response.json()
        except ValueError:
            data = {"description": response.text[:200]}
        result = data.get("result")
        message_id = None
        if isinstance(result, dict):
            message_id = result.get("message_id") or result.get("id")
        elif isinstance(result, int):
            message_id = result
        return {
            "ok": bool(data.get("ok")) and response.status_code == 200,
            "code": response.status_code,
            "description": str(data.get("description") or ""),
            "message_id": int(message_id) if message_id else None,
            "raw": data,
        }
    except Exception as error:
        return {"ok": False, "description": str(error), "message_id": None, "raw": {}}


def extract_message_id(result):
    if not isinstance(result, dict):
        return None
    mid = result.get("message_id")
    if mid:
        try:
            return int(mid)
        except Exception:
            return None
    raw = result.get("raw") or {}
    body = raw.get("result") if isinstance(raw, dict) else None
    if isinstance(body, dict):
        mid = body.get("message_id") or body.get("id")
        try:
            return int(mid) if mid else None
        except Exception:
            return None
    return None


def get_linked_chat(channel_id):
    cached = _LINKED.get(channel_id)
    if cached and time.time() - cached[0] < 180:
        return cached[1]
    data = _call("getChat", {"chat_id": channel_id})
    result = (data.get("raw") or {}).get("result") or {}
    linked = (
        result.get("linked_chat_id")
        or result.get("linked_chat")
        or result.get("discussion_chat_id")
    )
    if isinstance(linked, dict):
        linked = linked.get("id") or linked.get("chat_id")
    _LINKED[channel_id] = (time.time(), linked)
    if linked:
        print(f"🔗 گروه دیدگاه {channel_id} = {linked}")
    else:
        print(f"⚠️ گروه دیدگاه برای {channel_id} پیدا نشد | {data.get('description')}")
    return linked


def _send_to_group(group_id, text, reply_to=None, extra=None):
    payload = {"chat_id": group_id, "text": text}
    if reply_to:
        payload["reply_to_message_id"] = int(reply_to)
    if extra:
        payload.update(extra)
    return _call("sendMessage", payload)


def post_comment(channel_id, text, reply_to=None, group_message_id=None, group_id=None):
    text = (text or "").strip()
    if not text:
        return {"ok": False, "description": "empty"}

    target_group = group_id or get_linked_chat(channel_id)
    if not target_group:
        return {"ok": False, "description": "no-linked-group"}

    if group_message_id:
        result = _send_to_group(target_group, text, group_message_id)
        if result.get("ok"):
            print(f"💬 دیدگاه در گروه {target_group} نوشته شد")
            return result

    if reply_to:
        result = _send_to_group(
            target_group,
            text,
            extra={"reply_parameters": {"message_id": int(reply_to), "chat_id": channel_id}},
        )
        if result.get("ok"):
            print(f"💬 دیدگاه با reply_parameters نوشته شد")
            return result
        result = _send_to_group(target_group, text, reply_to)
        if result.get("ok"):
            print(f"💬 دیدگاه با reply_to روی گروه نوشته شد")
            return result

    print(f"⚠️ دیدگاه {channel_id} نرفت — به کانال چیزی نمی‌فرستم")
    return {"ok": False, "description": "group-send-failed"}


def remember_post(user_id, channel_id, message_id):
    if user_id and channel_id and message_id:
        try:
            _patch_channel(user_id, channel_id, {"last_post_id": int(message_id)})
        except Exception:
            pass
