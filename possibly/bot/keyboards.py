# POSSIBLY
# Keyboard helpers
#
# این فایل فقط از قابلیت‌هایی استفاده می‌کند که در نسخه نصب‌شده
# python-bale-bot واقعاً در دسترس هستند.
#
# Callback/Inline keyboard را بعد از تأیید API نسخه نصب‌شده
# به handlerهای مربوط وصل می‌کنیم.

from __future__ import annotations

from typing import Any


def button(text: str, **kwargs: Any) -> dict[str, Any]:
    """
    سازنده ساده برای نگهداری مشخصات دکمه.
    تبدیل نهایی به keyboard object در لایه Bale انجام می‌شود.
    """
    return {
        "text": text,
        **kwargs,
    }


def member_menu() -> list[list[dict[str, Any]]]:
    return [
        [
            button("👤 پروفایل من"),
            button("📊 آمار من"),
        ],
        [
            button("🎮 بازی‌ها"),
            button("ℹ️ درباره ربات"),
        ],
    ]


def admin_menu() -> list[list[dict[str, Any]]]:
    return [
        [
            button("👥 اعضای گروه"),
            button("🛡 مدیریت"),
        ],
        [
            button("📊 آمار گروه"),
            button("🧠 یادگیری"),
        ],
        [
            button("⚙️ تنظیمات"),
            button("🎮 بازی‌ها"),
        ],
        [
            button("📜 لاگ مدیریت"),
        ],
    ]


def owner_menu() -> list[list[dict[str, Any]]]:
    return [
        [
            button("👥 اعضای گروه"),
            button("🛡 مدیریت"),
        ],
        [
            button("📊 آمار گروه"),
            button("🧠 یادگیری"),
        ],
        [
            button("⚙️ تنظیمات"),
            button("🎮 بازی‌ها"),
        ],
        [
            button("📜 لاگ مدیریت"),
            button("💾 بکاپ"),
        ],
    ]


def tic_tac_toe_board(
    board: list[str | None],
) -> list[list[dict[str, Any]]]:
    """
    صفحه دوز.

    مقدار هر خانه به‌صورت جداگانه نگهداری می‌شود تا handler
    بتواند آن را به keyboard واقعی Bale تبدیل کند.
    """
    rows: list[list[dict[str, Any]]] = []

    for start in (0, 3, 6):
        row: list[dict[str, Any]] = []

        for index in range(start, start + 3):
            value = board[index] or str(index + 1)

            row.append(
                button(
                    value,
                    callback_data=f"ttt:{index}",
                )
            )

        rows.append(row)

    return rows
