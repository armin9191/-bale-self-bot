# ==============================
# Group Manager Bot - Main
# ==============================

import time
import requests

import config
import keyboards
import database

from features import moderation
from features import moderation_actions
from features import dashboard


# ==============================
# اتصال به API
# ==============================

SESSION = requests.Session()

SESSION.headers.update({
    "Content-Type": "application/json"
})

BASE_URL = config.API_URL


# ==============================
# درخواست به API بله
# ==============================

def api(method, data=None):

    url = f"{BASE_URL}/{method}"

    try:

        response = SESSION.post(
            url,
            json=data or {},
            timeout=30
        )

        return response.json()

    except Exception as error:

        print(f"API Error: {error}")

        return None


# ==============================
# ارسال پیام
# ==============================

def send_message(chat_id, text, reply_markup=None):

    data = {
        "chat_id": chat_id,
        "text": text
    }

    if reply_markup:
        data["reply_markup"] = reply_markup

    return api(
        "sendMessage",
        data
    )


# ==============================
# ویرایش پیام
# ==============================

def edit_message(
    chat_id,
    message_id,
    text,
    reply_markup=None
):

    data = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text
    }

    if reply_markup:
        data["reply_markup"] = reply_markup

    return api(
        "editMessageText",
        data
    )


# ==============================
# اتصال ماژول‌ها
# ==============================

moderation.setup(
    send_message,
    api
)

moderation_actions.setup(
    api
)

dashboard.setup(
    send_message,
    edit_message,
    api
)


# ==============================
# ثبت اطلاعات پیام
# ==============================

def save_message_data(message):

    chat = message.get(
        "chat",
        {}
    )

    user = message.get(
        "from",
        {}
    )

    chat_id = chat.get("id")
    chat_type = chat.get("type")

    user_id = user.get("id")

    if not chat_id:
        return

    # ==========================
    # فقط گروه‌ها
    # ==========================

    if chat_type in (
        "group",
        "supergroup"
    ):

        group_name = (
            chat.get("title")
            or chat.get("first_name")
            or "بدون نام"
        )

        database.save_group(
            chat_id,
            group_name
        )

        # ======================
        # ثبت کاربر
        # ======================

        if user_id:

            database.save_user(
                user_id,
                user.get("username"),
                user.get("first_name")
            )


# ==============================
# پردازش دکمه‌های اینلاین
# ==============================

def handle_callback(callback_query):

    if not callback_query:
        return

    callback_id = callback_query.get(
        "id"
    )

    callback_data = callback_query.get(
        "data"
    )

    message = callback_query.get(
        "message",
        {}
    )

    chat = message.get(
        "chat",
        {}
    )

    chat_id = chat.get(
        "id"
    )

    message_id = message.get(
        "message_id"
    )

    if callback_id:

        api(
            "answerCallbackQuery",
            {
                "callback_query_id": callback_id
            }
        )

    if not chat_id or not message_id:
        return

    # ==========================
    # داشبورد داخل پیوی
    # ==========================

    if callback_data == "dashboard_private":

        edit_message(
            chat_id,
            message_id,
            "📊 داشبورد\n\n"
            "✅ داشبورد برای شما داخل پیوی باز شد."
        )

        return

    # ==========================
    # داشبورد داخل گروه
    # ==========================

    if callback_data == "dashboard_group":

        edit_message(
            chat_id,
            message_id,
            "⚙️ داشبورد گروه\n\n"
            "تنظیمات گروه را از اینجا مدیریت کنید."
        )

        return


# ==============================
# پردازش پیام
# ==============================

def handle_message(message):

    if not message:
        return

    # ==========================
    # ثبت اطلاعات
    # ==========================

    save_message_data(message)

    chat = message.get(
        "chat",
        {}
    )

    chat_id = chat.get(
        "id"
    )

    text = message.get(
        "text",
        ""
    )

    if not chat_id:
        return

    # ==========================
    # داشبورد
    # ==========================

    if text.strip() == "داشبورد":

        dashboard.open_dashboard(
            message
        )

        return

    # ==========================
    # /start
    # ==========================

    if text == "/start":

        send_message(
            chat_id,
            "🤖 به ربات مدیریت گروه خوش اومدی!\n\n"
            "برای مشاهده امکانات، یکی از گزینه‌های زیر رو انتخاب کن:",
            keyboards.main_keyboard()
        )

        return

    # ==========================
    # دستورات مدیریت گروه
    # ==========================

    moderation_result = moderation.handle_message(
        message
    )

    if not moderation_result:
        return

    # ==========================
    # کاربر عادی
    # ==========================

    if moderation_result["type"] == "not_admin":

        send_message(
            chat_id,
            moderation.not_admin_message()
        )

        return

    # ==========================
    # بدون هدف
    # ==========================

    if moderation_result["type"] == "no_target":

        command = moderation_result["command"]

        command_names = {
            "kick": "کیک",
            "ban": "بن",
            "unban": "انبن",
            "mute": "سکوت",
            "unmute": "حذف سکوت",
            "delete": "حذف",
            "warn": "اخطار",
            "unwarn": "حذف اخطار",
        }

        command_name = command_names.get(
            command,
            command
        )

        send_message(
            chat_id,
            f"کیو {command_name} کنم؟؟ 🤔"
        )

        return

    # ==========================
    # هدف پیدا شد
    # ==========================

    if moderation_result["type"] == "target_found":

        command = moderation_result["command"]

        target_message = moderation_result[
            "target_message"
        ]

        # ======================
        # اجرای واقعی عملیات
        # ======================

        result = moderation_actions.execute_command(
            command,
            chat_id,
            target_message
        )

        # ======================
        # عملیات موفق
        # ======================

        if result.get("success"):

            action = result.get(
                "action"
            )

            success_messages = {

                "kick":
                    "👢 کاربر از گروه کیک شد.",

                "ban":
                    "🔨 کاربر بن شد.",

                "unban":
                    "🔓 بن کاربر برداشته شد.",

                "mute":
                    "🔇 کاربر ساکت شد.",

                "unmute":
                    "🔊 سکوت کاربر برداشته شد.",

                "delete":
                    "🗑️ پیام حذف شد.",
            }

            message_text = success_messages.get(
                action,
                "✅ انجام شد."
            )

            send_message(
                chat_id,
                message_text
            )

            return

        # ======================
        # اخطار فعلاً آماده نیست
        # ======================

        reason = result.get(
            "reason"
        )

        if reason == "warn_not_ready":

            send_message(
                chat_id,
                "⚠️ سیستم اخطار هنوز آماده نشده."
            )

            return

        if reason == "unwarn_not_ready":

            send_message(
                chat_id,
                "⚠️ سیستم حذف اخطار هنوز آماده نشده."
            )

            return

        # ======================
        # خطای اجرای عملیات
        # ======================

        send_message(
            chat_id,
            "❌ انجام عملیات موفق نبود."
        )

        return


# ==============================
# دریافت آپدیت‌ها
# ==============================

def get_updates(offset=None):

    data = {
        "limit": 100,
        "timeout": 25
    }

    if offset is not None:
        data["offset"] = offset

    return api(
        "getUpdates",
        data
    )


# ==============================
# اجرای اصلی بات
# ==============================

def start():

    database.init_db()

    print("================================")
    print("🤖 Group Manager Bot")
    print("🚀 Bot is starting...")
    print("🗄️ Database is ready")
    print("================================")

    offset = None

    while True:

        try:

            result = get_updates(
                offset
            )

            if not result:

                time.sleep(1)

                continue

            updates = result.get(
                "result",
                []
            )

            for update in updates:

                update_id = update.get(
                    "update_id"
                )

                if update_id is not None:

                    offset = update_id + 1

                # ======================
                # دکمه‌های اینلاین
                # ======================

                callback_query = update.get(
                    "callback_query"
                )

                if callback_query:

                    handle_callback(
                        callback_query
                    )

                # ======================
                # پیام معمولی
                # ======================

                message = update.get(
                    "message"
                )

                if message:

                    handle_message(
                        message
                    )

        except KeyboardInterrupt:

            print(
                "\n🛑 Bot stopped."
            )

            break

        except Exception as error:

            print(
                f"Main Error: {error}"
            )

            time.sleep(3)
