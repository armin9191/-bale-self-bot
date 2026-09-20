# POSSIBLY
# Keyboard helpers

from __future__ import annotations

import bale


def private_member_keyboard() -> bale.InlineKeyboardMarkup:
    return bale.InlineKeyboardMarkup(
        [
            [
                bale.InlineKeyboardButton(
                    "👤 پروفایل من",
                    callback_data="profile",
                ),
                bale.InlineKeyboardButton(
                    "📊 آمار من",
                    callback_data="my_stats",
                ),
            ],
            [
                bale.InlineKeyboardButton(
                    "🎮 بازی‌ها",
                    callback_data="games",
                ),
            ],
            [
                bale.InlineKeyboardButton(
                    "ℹ️ درباره ربات",
                    callback_data="about",
                ),
            ],
        ]
    )


def private_admin_keyboard() -> bale.InlineKeyboardMarkup:
    return bale.InlineKeyboardMarkup(
        [
            [
                bale.InlineKeyboardButton(
                    "👥 اعضای گروه",
                    callback_data="members",
                ),
                bale.InlineKeyboardButton(
                    "🛡 مدیریت",
                    callback_data="management",
                ),
            ],
            [
                bale.InlineKeyboardButton(
                    "📊 آمار گروه",
                    callback_data="group_stats",
                ),
                bale.InlineKeyboardButton(
                    "🧠 یادگیری",
                    callback_data="learning",
                ),
            ],
            [
                bale.InlineKeyboardButton(
                    "⚙️ تنظیمات",
                    callback_data="settings",
                ),
                bale.InlineKeyboardButton(
                    "🎮 بازی‌ها",
                    callback_data="games",
                ),
            ],
            [
                bale.InlineKeyboardButton(
                    "📜 لاگ مدیریت",
                    callback_data="moderation_logs",
                ),
            ],
        ]
    )


def private_owner_keyboard() -> bale.InlineKeyboardMarkup:
    return bale.InlineKeyboardMarkup(
        [
            [
                bale.InlineKeyboardButton(
                    "👥 اعضای گروه",
                    callback_data="members",
                ),
                bale.InlineKeyboardButton(
                    "🛡 مدیریت",
                    callback_data="management",
                ),
            ],
            [
                bale.InlineKeyboardButton(
                    "📊 آمار گروه",
                    callback_data="group_stats",
                ),
                bale.InlineKeyboardButton(
                    "🧠 یادگیری",
                    callback_data="learning",
                ),
            ],
            [
                bale.InlineKeyboardButton(
                    "⚙️ تنظیمات",
                    callback_data="settings",
                ),
                bale.InlineKeyboardButton(
                    "🎮 بازی‌ها",
                    callback_data="games",
                ),
            ],
            [
                bale.InlineKeyboardButton(
                    "📜 لاگ مدیریت",
                    callback_data="moderation_logs",
                ),
            ],
            [
                bale.InlineKeyboardButton(
                    "💾 بکاپ",
                    callback_data="backup",
                ),
            ],
        ]
    )


def games_keyboard() -> bale.InlineKeyboardMarkup:
    return bale.InlineKeyboardMarkup(
        [
            [
                bale.InlineKeyboardButton(
                    "🎭 مافیا",
                    callback_data="game_mafia",
                ),
                bale.InlineKeyboardButton(
                    "❌⭕ دوز",
                    callback_data="game_tictactoe",
                ),
            ],
            [
                bale.InlineKeyboardButton(
                    "🎲 جرأت و حقیقت",
                    callback_data="game_truth_dare",
                ),
            ],
            [
                bale.InlineKeyboardButton(
                    "🔙 بازگشت",
                    callback_data="back_private_menu",
                ),
            ],
        ]
    )


def tictactoe_keyboard(
    board: list[str | None],
) -> bale.InlineKeyboardMarkup:
    buttons = []

    for row in range(3):
        current_row = []

        for column in range(3):
            index = row * 3 + column

            value = board[index]

            if value is None:
                label = str(index + 1)
            else:
                label = value

            current_row.append(
                bale.InlineKeyboardButton(
                    label,
                    callback_data=f"ttt:{index}",
                )
            )

        buttons.append(current_row)

    return bale.InlineKeyboardMarkup(buttons)


def truth_dare_lobby_keyboard() -> bale.InlineKeyboardMarkup:
    return bale.InlineKeyboardMarkup(
        [
            [
                bale.InlineKeyboardButton(
                    "➕ پیوستن به بازی",
                    callback_data="td_join",
                ),
                bale.InlineKeyboardButton(
                    "➖ خروج از بازی",
                    callback_data="td_leave",
                ),
            ],
            [
                bale.InlineKeyboardButton(
                    "▶️ شروع بازی",
                    callback_data="td_start",
                ),
            ],
            [
                bale.InlineKeyboardButton(
                    "🛑 پایان بازی",
                    callback_data="td_end",
                ),
            ],
        ]
    )


def truth_dare_turn_keyboard() -> bale.InlineKeyboardMarkup:
    return bale.InlineKeyboardMarkup(
        [
            [
                bale.InlineKeyboardButton(
                    "🎯 جرأت",
                    callback_data="td_dare",
                ),
                bale.InlineKeyboardButton(
                    "❓ حقیقت",
                    callback_data="td_truth",
                ),
            ],
        ]
    )


def truth_dare_done_keyboard() -> bale.InlineKeyboardMarkup:
    return bale.InlineKeyboardMarkup(
        [
            [
                bale.InlineKeyboardButton(
                    "✅ جواب دادم",
                    callback_data="td_done",
                ),
            ],
        ]
    )


def whisper_keyboard(
    whisper_id: int,
) -> bale.InlineKeyboardMarkup:
    return bale.InlineKeyboardMarkup(
        [
            [
                bale.InlineKeyboardButton(
                    "👁 مشاهده نجوا",
                    callback_data=f"whisper:{whisper_id}",
                ),
            ],
        ]
    )


def back_keyboard() -> bale.InlineKeyboardMarkup:
    return bale.InlineKeyboardMarkup(
        [
            [
                bale.InlineKeyboardButton(
                    "🔙 بازگشت",
                    callback_data="back_private_menu",
                ),
            ],
        ]
    )

