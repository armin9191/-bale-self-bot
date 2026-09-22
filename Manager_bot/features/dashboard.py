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
# باز کردن داشبورد
# ==============================

def open_dashboard(message):

    chat = message.get(
        "chat",
        {}
    )

    chat_id = chat.get("id")

    if not chat_id:
        return

    # ==========================
    # فعلاً لینک مستقیم
    # ==========================

    bot_username = get_bot_username()

    private_url = private_dashboard_url(
        bot_username,
        chat_id
    )

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
# دریافت اطلاعات ربات
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
# ساخت لینک ورود به PV
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
# متن داشبورد باز شده
# ==============================

def dashboard_opened_text():

    return (
        "📊 داشبورد\n\n"
        "✅ داشبورد برای شما داخل پیوی باز شد."
    )
