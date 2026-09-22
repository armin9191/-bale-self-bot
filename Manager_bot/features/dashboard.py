# ==============================
# Group Manager Bot - Dashboard
# ==============================

send_message = None
edit_message = None
api_request = None


# ==============================
# اتصال به main.py
# ==============================

def setup(
    send_message_function,
    edit_message_function,
    api_function
):

    global send_message
    global edit_message
    global api_request

    send_message = send_message_function
    edit_message = edit_message_function
    api_request = api_function


# ==============================
# داشبورد اصلی
# ==============================

def dashboard_keyboard(group_id):

    return {
        "inline_keyboard": [
            [
                {
                    "text": "🛡️ محافظت",
                    "callback_data": f"group_security_{group_id}"
                }
            ],
            [
                {
                    "text": "⚙️ تنظیمات گروه",
                    "callback_data": f"group_settings_{group_id}"
                }
            ]
        ]
    }


# ==============================
# باز کردن داشبورد
# ==============================

def open_dashboard(message):

    chat = message.get(
        "chat",
        {}
    )

    chat_id = chat.get(
        "id"
    )

    if not chat_id:
        return

    # ==========================
    # نام ربات
    # ==========================

    bot_username = get_bot_username()

    if not bot_username:

        send_message(
            chat_id,
            "❌ نتونستم لینک ورود به داشبورد رو بسازم."
        )

        return

    # ==========================
    # لینک PV
    # ==========================

    private_url = private_dashboard_url(
        bot_username,
        chat_id
    )

    # ==========================
    # انتخاب محل داشبورد
    # ==========================

    send_message(
        chat_id,
        "📊 داشبورد\n\n"
        "داشبورد برای شما کجا باز شود؟",
        {
            "inline_keyboard": [
                [
                    {
                        "text": "👤 در پیوی",
                        "url": private_url
                    },
                    {
                        "text": "👥 داخل گروه",
                        "callback_data": "dashboard_group"
                    }
                ]
            ]
        }
    )


# ==============================
# دریافت نام کاربری ربات
# ==============================

def get_bot_username():

    if not api_request:
        return ""

    result = api_request(
        "getMe"
    )

    if not result:
        return ""

    if not result.get("ok"):
        return ""

    bot = result.get(
        "result",
        {}
    )

    return bot.get(
        "username",
        ""
    )


# ==============================
# ساخت لینک PV
# ==============================

def private_dashboard_url(
    bot_username,
    group_id
):

    return (
        f"https://ble.ir/{bot_username}"
        f"?start=dashboard_{group_id}"
    )


# ==============================
# داشبورد داخل PV
# ==============================

def open_group_dashboard(
    chat_id,
    group_id,
    message_id=None
):

    text = (
        "⚙️ داشبورد گروه\n\n"
        "🛡️ محافظت\n"
        "🟢 ضد اسپم\n"
        "🔴 ضد عکس\n"
        "🔴 ضد ویدیو\n"
        "🔴 ضد فیلم\n"
        "🔴 ضد ویس\n"
        "🔴 ضد فحش"
    )

    keyboard = dashboard_keyboard(
        group_id
    )

    # ==========================
    # اگر پیام داخل گروه است
    # ==========================

    if message_id is not None:

        edit_message(
            chat_id,
            message_id,
            text,
            keyboard
        )

        return

    # ==========================
    # اگر PV است
    # ==========================

    send_message(
        chat_id,
        text,
        keyboard
    )


# ==============================
# متن داشبورد
# ==============================

def dashboard_opened_text():

    return (
        "⚙️ داشبورد گروه\n\n"
        "🛡️ محافظت\n"
        "🟢 ضد اسپم\n"
        "🔴 ضد عکس\n"
        "🔴 ضد ویدیو\n"
        "🔴 ضد فیلم\n"
        "🔴 ضد ویس\n"
        "🔴 ضد فحش"
    )
