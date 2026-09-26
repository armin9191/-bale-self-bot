import json
import os
import time
from datetime import datetime

from storage import users_path

_LOCK_PATH = users_path() + ".lock"


def _acquire_lock():
    os.makedirs(os.path.dirname(users_path()) or ".", exist_ok=True)
    for _ in range(50):
        try:
            fd = os.open(_LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            return True
        except FileExistsError:
            try:
                if time.time() - os.path.getmtime(_LOCK_PATH) > 8:
                    os.remove(_LOCK_PATH)
                    continue
            except OSError:
                pass
            time.sleep(0.05)
    return False


def _release_lock():
    try:
        os.remove(_LOCK_PATH)
    except OSError:
        pass


def load_users():
    path = users_path()
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as file:
            json.dump({}, file, ensure_ascii=False, indent=4)
        return {}
    try:
        with open(path, "r", encoding="utf-8") as file:
            users = json.load(file)
            return users if isinstance(users, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def save_users(users):
    path = users_path()
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as file:
        json.dump(users, file, ensure_ascii=False, indent=4)
    os.replace(tmp, path)


def _patch_channel(user_id, channel_id, updates):
    _acquire_lock()
    try:
        users = load_users()
        user_id = str(user_id)
        if user_id not in users:
            return False
        target = str(channel_id or "").lower()
        for channel in users[user_id].get("channels", []):
            if str(channel.get("id") or "").lower() == target:
                channel.update(updates)
                save_users(users)
                return True
        return False
    finally:
        _release_lock()


def user_exists(user_id):
    return str(user_id) in load_users()


def add_user(user_id, first_name, username=None):
    _acquire_lock()
    try:
        users = load_users()
        user_id = str(user_id)
        if user_id not in users:
            users[user_id] = {
                "first_name": first_name,
                "username": username,
                "join_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                "wallet": 0,
                "channels": [],
                "subscription": {"type": None, "expire": None, "total_days": 0},
                "free_claimed": False,
                "invited_by": None,
                "invite_count": 0,
                "is_admin": False,
            }
            save_users(users)
        else:
            users[user_id]["first_name"] = first_name or users[user_id].get("first_name")
            if username:
                users[user_id]["username"] = username
            save_users(users)
    finally:
        _release_lock()


def get_user(user_id):
    return load_users().get(str(user_id))


def update_user(user_id, data):
    _acquire_lock()
    try:
        users = load_users()
        user_id = str(user_id)
        if user_id in users:
            users[user_id].update(data)
            save_users(users)
    finally:
        _release_lock()


def add_channel(user_id, channel, max_channels=3):
    from channel_utils import normalize_channel_id
    channel = normalize_channel_id(channel) or channel
    _acquire_lock()
    try:
        users = load_users()
        user_id = str(user_id)
        if user_id not in users:
            return False
        channels = users[user_id].setdefault("channels", [])
        if len(channels) >= int(max_channels or 0):
            return False
        for item in channels:
            if str(item.get("id") or "").lower() == str(channel).lower():
                return False
        channels.append({
            "id": channel,
            "status": "active",
            "send_image": True,
            "show_emoji": True,
            "footer_text": "",
            "interval": 10,
            "last_send": 0,
            "categories": ["همه"],
            "comment_on": False,
            "comment_text": "",
        })
        save_users(users)
        return True
    finally:
        _release_lock()


def delete_channel(user_id, channel_id):
    _acquire_lock()
    try:
        users = load_users()
        user_id = str(user_id)
        if user_id not in users:
            return False
        channels = users[user_id].get("channels", [])
        target = str(channel_id or "").lower()
        keep = [item for item in channels if str(item.get("id") or "").lower() != target]
        if len(keep) == len(channels):
            return False
        users[user_id]["channels"] = keep
        save_users(users)
        return True
    finally:
        _release_lock()


def set_channel_status(user_id, channel_id, status):
    return _patch_channel(user_id, channel_id, {"status": status})


def _toggle_flag(user_id, channel_id, key, default=True):
    _acquire_lock()
    try:
        users = load_users()
        user_id = str(user_id)
        target = str(channel_id or "").lower()
        if user_id not in users:
            return None
        for channel in users[user_id].get("channels", []):
            if str(channel.get("id") or "").lower() == target:
                channel[key] = not channel.get(key, default)
                save_users(users)
                return channel[key]
        return None
    finally:
        _release_lock()


def toggle_channel_image(user_id, channel_id):
    return _toggle_flag(user_id, channel_id, "send_image", True)


def toggle_channel_emoji(user_id, channel_id):
    return _toggle_flag(user_id, channel_id, "show_emoji", True)


def update_footer_text(user_id, channel_id, text):
    return _patch_channel(user_id, channel_id, {"footer_text": text})


def update_categories(user_id, channel_id, categories):
    if not categories:
        categories = ["همه"]
    return _patch_channel(user_id, channel_id, {"categories": categories})


def update_send_time(user_id, channel_id, interval):
    try:
        interval = int(interval)
    except Exception:
        return False
    interval = max(1, min(interval, 180))
    return _patch_channel(user_id, channel_id, {"interval": interval})


def update_last_send(user_id, channel_id, last_send):
    return _patch_channel(user_id, channel_id, {"last_send": last_send})
