from bale import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from force_join import get_force_join_channels


def force_join_keyboard():

    keyboard = InlineKeyboardMarkup()

    for channel in get_force_join_channels():

        keyboard.add(
            InlineKeyboardButton(
                f"📢 {channel['username']}",
                url=f"https://ble.ir/{channel['username'].replace('@', '')}"
            ),
            row=1
        )

    keyboard.add(
        InlineKeyboardButton(
            "✅ عضو شدم",
            callback_data="check_force_join"
        ),
        row=2
    )

    return keyboard