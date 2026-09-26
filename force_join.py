from channel_checker import get_chat_member
from admin_store import load_join_channels


def is_force_join_enabled():
    return bool(load_join_channels())


def get_force_join_channels():
    return load_join_channels()


def is_user_joined(user_id):
    channels = load_join_channels()
    if not channels:
        return True
    for channel in channels:
        status = get_chat_member(channel.get("id") or channel.get("username"), user_id)
        if status not in ("creator", "administrator", "member"):
            return False
    return True
