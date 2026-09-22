# ==============================
# Group Manager Bot - Main
# ==============================

import time
import requests

import config
import keyboards


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

    return api("sendMessage", data)


# ==============================
# پردازش پیام
# ==============================

def handle_message(message):

    if not message:
        return

    chat = message.get("chat", {})
    chat_id = chat.get("id")

    text = message.get("text", "")

    if not chat_id:
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

    return api("getUpdates", data)


# ==============================
# اجرای اصلی بات
# ==============================

def start():

    print("================================")
    print("🤖 Group Manager Bot")
    print("🚀 Bot is starting...")
    print("================================")

    offset = None

    while True:

        try:

            result = get_updates(offset)

            if not result:
                time.sleep(1)
                continue

            updates = result.get("result", [])

            for update in updates:

                update_id = update.get("update_id")

                if update_id is not None:
                    offset = update_id + 1

                message = update.get("message")

                if message:
                    handle_message(message)

        except KeyboardInterrupt:

            print("\n🛑 Bot stopped.")
            break

        except Exception as error:

            print(f"Main Error: {error}")
            time.sleep(3)
