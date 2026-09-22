# ==============================
# Group Manager - Moderation
# ==============================

import random


# ==============================
# اتصال به main.py
# ==============================

send_message = None
api_request = None


def setup(send_message_function, api_function):

    global send_message
    global api_request

    send_message = send_message_function
    api_request = api_function


# ==============================
# جواب به کاربر عادی
# ==============================

NOT_ADMIN_MESSAGES = [
    "😂 تو که ادمین نیستی داداش!",
    "😐 مجوز مدیریت کجاست فرمانده؟",
    "😭 اول ادمین شو، بعد دستور بده!",
    "😂 اینجا دستورات مدیریتی فقط برای ادمیناست!",
    "😎 قدرت دست تو نیست هنوز!",
    "🤨 با چه سمتی دقیقاً؟!",
    "😂 دستور قشنگی بود، ولی دسترسی نداری!",
]


def not_admin_message():

    return random.choice(
        NOT_ADMIN_MESSAGES
    )


# ==============================
# دستورهای مدیریتی
# ==============================

COMMANDS = {

    # --------------------------
    # کیک
    # --------------------------

    "kick": [
        "کیک",
        "کیک کن",
        "کیکش کن",
        "کیکش",
    ],

    # --------------------------
    # بن
    # --------------------------

    "ban": [
        "بن",
        "بن کن",
        "بنش کن",
        "بن کنش",
        "بنش",
    ],

    # --------------------------
    # انبن
    # --------------------------

    "unban": [
        "انبن",
        "انبن کن",
        "آن‌بن",
        "آن‌بن کن",
        "رفع بن",
        "رفع بن کن",
    ],

    # --------------------------
    # سکوت
    # --------------------------

    "mute": [
        "سکوت",
        "سکوت کن",
        "ساکتش کن",
        "ساکت کن",
        "ساکتش",
    ],

    # --------------------------
    # حذف سکوت
    # --------------------------

    "unmute": [
        "حذف سکوت",
        "حذف سکوت کن",
        "رفع سکوت",
        "رفع سکوت کن",
        "آنسکوت",
        "آنسکوت کن",
    ],

    # --------------------------
    # حذف پیام
    # --------------------------

    "delete": [
        "حذف",
        "حذفش کن",
        "پاک کن",
        "پاکش کن",
        "حذف پیام",
    ],

    # --------------------------
    # اخطار
    # --------------------------

    "warn": [
        "اخطار",
        "اخطار بده",
        "اخطارش بده",
    ],

    # --------------------------
    # حذف اخطار
    # --------------------------

    "unwarn": [
        "حذف اخطار",
        "حذف اخطار کن",
        "رفع اخطار",
        "رفع اخطار کن",
    ],
}


# ==============================
# تشخیص دستور
# ==============================

def detect_command(text):

    if not text:
        return None

    text = text.strip().lower()

    for command, aliases in COMMANDS.items():

        if text in aliases:
            return command

    return None


# ==============================
# دریافت وضعیت عضو گروه
# ==============================

def get_member_status(chat_id, user_id):

    if not api_request:
        return None

    result = api_request(
        "getChatMember",
        {
            "chat_id": chat_id,
            "user_id": user_id
        }
    )

    if not result:
        return None

    if not result.get("ok", False):
        return None

    member = result.get("result")

    if not member:
        return None

    return member.get("status")


# ==============================
# بررسی ادمین یا مالک
# ==============================

def is_admin(chat_id, user_id):

    status = get_member_status(
        chat_id,
        user_id
    )

    return status in (
        "administrator",
        "creator"
    )


# ==============================
# بررسی گروه
# ==============================

def is_group_message(message):

    if not message:
        return False

    chat = message.get("chat", {})

    return chat.get("type") in (
        "group",
        "supergroup"
    )


# ==============================
# دریافت پیام هدف
# ==============================

def get_target_message(message):

    reply_message = message.get(
        "reply_to_message"
    )

    if not reply_message:
        return None

    target_user = reply_message.get(
        "from"
    )

    if not target_user:
        return None

    return reply_message


# ==============================
# پردازش دستور
# ==============================

def handle_message(message):

    if not message:
        return False

    # ==========================
    # فقط گروه
    # ==========================

    if not is_group_message(message):
        return False

    text = message.get("text", "")

    command = detect_command(text)

    if not command:
        return False

    chat = message.get("chat", {})
    user = message.get("from", {})

    chat_id = chat.get("id")
    user_id = user.get("id")

    if not chat_id or not user_id:
        return False

    # ==========================
    # بررسی ادمین
    # ==========================

    if not is_admin(
        chat_id,
        user_id
    ):

        return {
            "type": "not_admin",
            "command": command,
            "message": message
        }

    # ==========================
    # پیدا کردن پیام هدف
    # ==========================

    target_message = get_target_message(
        message
    )

    # ==========================
    # بدون ریپلای
    # ==========================

    if not target_message:

        return {
            "type": "no_target",
            "command": command,
            "message": message
        }

    # ==========================
    # با ریپلای
    # ==========================

    target_user = target_message.get(
        "from",
        {}
    )

    return {
        "type": "target_found",
        "command": command,
        "message": message,
        "target_message": target_message,
        "target_user": target_user
    }
