import requests

from config import BOT_TOKEN


BASE_URL = f"https://tapi.bale.ai/bot{BOT_TOKEN}"


def get_chat_member(chat_id, user_id):
    """
    بررسی عضویت کاربر در کانال
    """

    try:

        response = requests.post(
            f"{BASE_URL}/getChatMember",
            json={
                "chat_id": chat_id,
                "user_id": user_id
            },
            timeout=10
        )

        if response.status_code != 200:
            return None

        data = response.json()

        if not data.get("ok"):
            return None

        return data["result"]["status"]

    except Exception:
        return None