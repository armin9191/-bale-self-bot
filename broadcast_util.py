from concurrent.futures import ThreadPoolExecutor, as_completed

from sender import deliver_broadcast
from users import load_users


def is_forwarded(message):
    names = (
        "forward_from",
        "forward_from_chat",
        "forward_date",
        "forward_sender_name",
        "forward_origin",
        "forward_from_message_id",
    )
    for name in names:
        if getattr(message, name, None):
            return True
    data = getattr(message, "_data", None) or {}
    if isinstance(data, dict):
        for name in names:
            if data.get(name):
                return True
    return False


def has_media(message):
    for name in ("photo", "video", "document", "animation", "audio", "sticker"):
        if getattr(message, name, None):
            return True
    return False


def all_channel_ids():
    ids = []
    for user in load_users().values():
        if not isinstance(user, dict):
            continue
        for channel in user.get("channels") or []:
            if isinstance(channel, dict) and channel.get("id"):
                ids.append(channel["id"])
    return ids


def broadcast_targets(kind):
    if kind == "pv":
        return [int(user_id) for user_id in load_users().keys() if str(user_id).lstrip("-").isdigit()]
    return all_channel_ids()


def run_broadcast(kind, from_chat, message_id, text, forwarded=False, media=False):
    targets = broadcast_targets(kind)
    if not targets:
        return 0, 0
    workers = min(40, max(8, len(targets)))
    ok = 0
    fail = 0

    def send_one(target):
        if forwarded:
            return deliver_broadcast(target, from_chat, message_id, text, True)
        if media:
            return deliver_broadcast(target, from_chat, message_id, text, False)
        if text:
            return deliver_broadcast(target, from_chat, None, text, False)
        return deliver_broadcast(target, from_chat, message_id, text, False)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(send_one, target) for target in targets]
        for future in as_completed(futures):
            result = future.result() or {}
            if result.get("ok"):
                ok += 1
            else:
                fail += 1
    return ok, fail
