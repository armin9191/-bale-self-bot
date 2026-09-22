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

            # جلوگیری از ارسال پیام
            "can_send_messages": False,

            # جلوگیری از ارسال فایل و رسانه
            "can_send_media_messages": False,

            # جلوگیری از استیکر و موارد مشابه
            "can_send_other_messages": False,

            # جلوگیری از لینک
            "can_add_web_page_previews": False
        }
    )

    print(
        "MUTE API RESULT:",
        result
    )

    if not result:
        return False

    return result.get(
        "ok",
        False
    )


# ==============================
# رفع سکوت
# ==============================

def unmute_user(chat_id, user_id):

    if not api_request:
        return False

    result = api_request(
        "restrictChatMember",
        {
            "chat_id": chat_id,
            "user_id": user_id,
            "can_send_messages": True,
            "can_send_media_messages": True,
            "can_send_other_messages": True,
            "can_add_web_page_previews": True
        }
    )

    if not result:
        return False

    return result.get(
        "ok",
        False
    )


# ==============================
# حذف پیام
# ==============================

def delete_message(chat_id, message_id):

    if not api_request:
        return False

    result = api_request(
        "deleteMessage",
        {
            "chat_id": chat_id,
            "message_id": message_id
        }
    )

    if not result:
        return False

    return result.get(
        "ok",
        False
    )


# ==============================
# اجرای دستور
# ==============================

def execute_command(
    command,
    chat_id,
    target_message
):

    if not target_message:

        return {
            "success": False,
            "reason": "no_target"
        }

    target_user = target_message.get(
        "from",
        {}
    )

    target_user_id = target_user.get(
        "id"
    )

    if not target_user_id:

        return {
            "success": False,
            "reason": "invalid_target"
        }

    # ==========================
    # کیک
    # ==========================

    if command == "kick":

        success = kick_user(
            chat_id,
            target_user_id
        )

        return {
            "success": success,
            "action": "kick"
        }

    # ==========================
    # بن
    # ==========================

    if command == "ban":

        success = ban_user(
            chat_id,
            target_user_id
        )

        return {
            "success": success,
            "action": "ban"
        }

    # ==========================
    # انبن
    # ==========================

    if command == "unban":

        success = unban_user(
            chat_id,
            target_user_id
        )

        return {
            "success": success,
            "action": "unban"
        }

    # ==========================
    # سکوت
    # ==========================

    if command == "mute":

        success = mute_user(
            chat_id,
            target_user_id
        )

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

    # ==========================
    # دستور ناشناخته
    # ==========================

    return {
        "success": False,
        "reason": "unknown_command"
    }
