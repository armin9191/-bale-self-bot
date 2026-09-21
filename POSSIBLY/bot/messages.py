"""Branded message templates."""
from __future__ import annotations

HEADER = (
    "╭━━━━━━━━━━━━━━━╮\n"
    "│ ⚔️ POSSIBLY\n"
    "╰━━━━━━━━━━━━━━━╯\n\n"
)


def message(text: str) -> str:
    return HEADER + text


def success(text: str) -> str:
    return message(f"✅ {text}")


def error(text: str) -> str:
    return message(f"❌ {text}")


def info(text: str) -> str:
    return message(text)


def warning(text: str) -> str:
    return message(f"⚠️ {text}")


def help_text() -> str:
    return info(
        "📖 راهنمای دستورات POSSIBLY\n\n"
        "—— در گروه (@possibly) ——\n"
        "• بن / کیک / آنبن (ریپلای یا آیدی)\n"
        "• اکو متن\n"
        "• نجوا متن (ریپلای)\n"
        "• یاد بگیر / فراموش کن / لیست یادگیری\n"
        "• آمار / راهنما\n"
        "• دوز / مافیا / جرعت حقیقت\n"
        "• گیف (ریپلای به گیف + گیف متن)\n"
        "• قوانین / تنظیم قوانین\n"
        "• تنظیم خوشامد / تنظیم بدرقه\n"
        "• قفل‌ها / قفل [مورد] / بازکردن [مورد]\n"
        "• ویژه / لغو ویژه / لیست ویژه / پاکسازی ویژه ها\n"
        "• اطلاعات / آیدی / info (ریپلای)\n"
        "• اصل / اصل من / ثبت اصل / ویرایش اصل / لیست اصل‌ها\n"
        "• اصل رندوم / برترین اصل‌ها / آمار اصل / جستجوی اصل\n"
        "• لقب / تنظیم لقب / حذف لقب / لیست لقب‌ها\n"
        "• پنل کاربر (ریپلای یا آیدی)\n"
        "• تنظیم قفل جوین @channel / حذف قفل جوین\n\n"
        "—— در پیوی ربات ——\n"
        "• راهنما / منو / start\n"
        "• آمار من / پروفایل\n"
        "• بکاپ یا /backup (فقط Owner)\n"
        "• بیشتر دستورات ادمین از پیوی هم کار می‌کنند\n\n"
        "ربات فقط در گروه @possibly فعال است."
    )
