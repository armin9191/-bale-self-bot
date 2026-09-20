# POSSIBLY
# Keyboard builders

from __future__ import annotations

import bale


def private_member_keyboard() -> bale.InlineKeyboardMarkup:
    return bale.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                bale.InlineKeyboardButton(
                    text="👤 پروفایل من",
                    callback_data="profile",
                ),
                bale.InlineKeyboardButton(
                    text="📊 آمار من",
                    callback_data="my_stats",
                ),
            ],
            [
                bale.InlineKeyboardButton(
                    text="🎮 بازی‌ها",
                    callback_data="games",
                ),
                bale.InlineKeyboardButton(
                    text="ℹ️ درباره ربات",
                    callback_data="about",
                ),
            ],
        ]
    )


def private_admin_keyboard() -> bale.InlineKeyboardMarkup:
    return bale.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                bale.InlineKeyboardButton(
                    text="👥 اعضای گروه",
                    callback_data="members",
                ),
                bale.InlineKeyboardButton(
                    text="🛡 مدیریت",
                    callback_data="admin",
                ),
            ],
            [
                bale.InlineKeyboardButton(
                    text="📊 آمار گروه",
                    callback_data="group_stats",
                ),
                bale.InlineKeyboardButton(
                    text="🧠 یادگیری",
                    callback_data="learning",
                ),
            ],
            [
                bale.InlineKeyboardButton(
                    text="⚙️ تنظیمات",
                    callback_data="settings",
                ),
                bale.InlineKeyboardButton(
                    text="🎮 بازی‌ها",
                    callback_data="games",
                ),
            ],
            [
                bale.InlineKeyboardButton(
                    text="📜 لاگ مدیریت",
                    callback_data="moderation_logs",
                ),
            ],
        ]
    )


def private_owner_keyboard() -> bale.InlineKeyboardMarkup:
    return bale.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                bale.InlineKeyboardButton(
                    text="👥 اعضای گروه",
                    callback_data="members",
                ),
                bale.InlineKeyboardButton(
                    text="🛡 مدیریت",
                    callback_data="admin",
                ),
            ],
            [
                bale.InlineKeyboardButton(
                    text="📊 آمار گروه",
                    callback_data="group_stats",
                ),
                bale.InlineKeyboardButton(
                    text="🧠 یادگیری",
                    callback_data="learning",
                ),
            ],
            [
                bale.InlineKeyboardButton(
                    text="⚙️ تنظیمات",
                    callback_data="settings",
                ),
                bale.InlineKeyboardButton(
                    text="🎮 بازی‌ها",
                    callback_data="games",
                ),
            ],
            [
                bale.InlineKeyboardButton(
                    text="📜 لاگ مدیریت",
                    callback_data="moderation_logs",
                ),
            ],
            [
                bale.InlineKeyboardButton(
                    text="💾 بکاپ دیتابیس",
                    callback_data="database_backup",
                ),
            ],
        ]
    )


def whisper_keyboard(
    whisper_id: int,
) -> bale.InlineKeyboardMarkup:
    return bale.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                bale.InlineKeyboardButton(
                    text="👁 مشاهده نجوا",
                    callback_data=f"whisper:{whisper_id}",
                )
            ]
        ]
    )


def tic_tac_toe_keyboard(
    board: list[str | None],
) -> bale.InlineKeyboardMarkup:
    buttons = []

    for row in range(3):
        current_row = []

        for column in range(3):
            position = row * 3 + column
            value = board[position]

            text = value if value else str(position + 1)

            current_row.append(
                bale.InlineKeyboardButton(
                    text=text,
                    callback_data=f"ttt:{position}",
                )
            )

        buttons.append(current_row)

    return bale.InlineKeyboardMarkup(
        inline_keyboard=buttons
    )
