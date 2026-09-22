# ==============================
# Group Manager - Moderation Actions
# ==============================


# ==============================
# اتصال به main.py
# ==============================

api_request = None


def setup(api_function):

    global api_request

    api_request = api_function


# ==============================
# کیک
# ==============================

def kick_user(chat_id, user_id):

    if not api_request:
        return False

    # --------------------------
    # خارج کردن کاربر
    # --------------------------

    ban_result = api_request(
        "banChatMember",
        {
            "chat_id": chat_id,
            "user_id": user_id
        }
    )

    if not ban_result:
        return False

    if not ban_result.get("ok", False):
        return False

    # --------------------------
    # رفع فوری بن
    # --------------------------

    unban_result = api_request(
        "unbanChatMember",
        {
            "chat_id": chat_id,
            "user_id": user_id
        }
    )

    if not unban_result:
        return False

    return unban_result.get(
        "ok",
        False
    )


# ==============================
# بن
# ==============================

def ban_user(chat_id, user_id):

    if not api_request:
        return False

    result = api_request(
        "banChatMember",
        {
            "chat_id": chat_id,
            "user_id": user_id
        }
    )

    if not result:
        return False

    return result.get(
        "ok",
        False
    )


# ==============================
# انبن
# ==============================

def unban_user(chat_id, user_id):

    if not api_request:
        return False

    result = api_request(
        "unbanChatMember",
        {
            "chat_id": chat_id,
            "user_id": user_id
        }
    )

    if not result:
        return False

    return result.get(
        "ok",
        False
    )


# ==============================
# سکوت
# ==============================

def mute_user(chat_id, user_id):

    if not api_request:
        return False

    result = api_request(
        "restrictChatMember",
        {
            "chat_id": chat_id,
            "user_id": user_id,
            "can_send_messages": False,
            "can_send_media_messages": False,
            "can_send_other_messages": False,

        return {
            "success": success,
            "action": "mute"
        }

    # ==========================
    # رفع سکوت
    # ==========================

    if command == "unmute":

        success = unmute_user(
            chat_id,
            target_user_id
        )

        return {
            "success": success,
            "action": "unmute"
        }

    # ==========================
    # حذف پیام
    # ==========================

    if command == "delete":

        message_id = target_message.get(
            "message_id"
        )

        if not message_id:
            return {
                "success": False,
                "reason": "invalid_message"
            }

        success = delete_message(
            chat_id,
            message_id
        )

        return {
            "success": success,
            "action": "delete"
        }

    # ==========================
    # اخطار
    # ==========================

    if command == "warn":

        return {
            "success": False,
            "reason": "warn_not_ready"
        }

    # ==========================
    # حذف اخطار
    # ==========================

    if command == "unwarn":

        return {
            "success": False,
            "reason": "unwarn_not_ready"
        }

    return {
        "success": False,
        "reason": "unknown_command"
    }
