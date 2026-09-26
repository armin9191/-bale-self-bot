# ==========================
# AutoNewsBot States
# Version 2.0.0
# ==========================

# وضعیت کاربران
user_states = {}


def set_state(user_id, state, data=None):
    """
    تنظیم وضعیت کاربر
    """

    user_states[user_id] = {
        "state": state,
        "data": data or {}
    }


def get_state(user_id):
    """
    دریافت وضعیت کاربر
    """

    return user_states.get(
        user_id,
        {
            "state": None,
            "data": {}
        }
    )


def clear_state(user_id):
    """
    حذف وضعیت کاربر
    """

    user_states.pop(user_id, None)