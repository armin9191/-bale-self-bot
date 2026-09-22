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

    send_message(
        chat_id,
        "📊 داشبورد\n\n"
        "داشبورد برای شما کجا باز شود؟",
        {
            "inline_keyboard": [
                [
                    {
                        "text": "👤 در پیوی",
                        "callback_data": "dashboard_private"
                    },
                    {
                        "text": "👥 داخل گروه",
                        "callback_data": "dashboard_group"
                    }
                ]
            ]
        }
    )
