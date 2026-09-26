import time

from bale import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton

from client import bot
from ui import edit_message
from states import set_state, get_state, clear_state
from keyboards import plans_menu, pay_method_menu, card_pay_menu, home_inline_menu
from subscription import (
    PLANS,
    CARD_NUMBER,
    ADMIN_IDS,
    load_payments,
    save_payments,
    create_license,
    redeem_license,
)
from sender import send_message, send_photo, copy_message, inline_keyboard
from handlers.home import home_components


def back_only():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔙 بازگشت", callback_data="m_home"), row=1)
    return keyboard


def license_button():
    return inline_keyboard([[("🔑 ورود کد لایسنس", "m_license")], [("🏠 منوی اصلی", "m_home")]])


def admin_markup(req_id):
    return inline_keyboard([
        [("✅ تایید", f"adm_ok_{req_id}"), ("❌ رد", f"adm_no_{req_id}")],
        [("📝 ارسال پیام به کاربر", f"adm_msg_{req_id}")],
    ])


def user_mention(user):
    username = getattr(user, "username", None) if user else None
    if username:
        return "@" + str(username).lstrip("@")
    name = getattr(user, "first_name", None) if user else None
    return name or "کاربر"


def extract_photo(message):
    for attr in ("photos", "photo"):
        value = getattr(message, attr, None)
        if not value:
            continue
        if isinstance(value, str):
            return value
        if isinstance(value, list) and value:
            item = value[-1]
            return getattr(item, "id", None) or getattr(item, "file_id", None) or item
        return getattr(value, "id", None) or getattr(value, "file_id", None) or str(value)
    document = getattr(message, "document", None)
    if document:
        return getattr(document, "id", None) or getattr(document, "file_id", None)
    return None


@bot.event
async def on_callback(callback: CallbackQuery):
    data = callback.data or ""
    user_id = callback.from_user.id

    if data.startswith("plan_"):
        plan_id = data.replace("plan_", "", 1)
        plan = PLANS.get(plan_id)
        if not plan:
            return
        set_state(user_id, "choose_pay", {"plan_id": plan_id})
        price = f"{plan['price']:,}".replace(",", "٬")
        await edit_message(
            callback,
            f"📅 اشتراک {plan['title']}\n💰 مبلغ: {price} تومن\n\nروش پرداخت را انتخاب کن.",
            pay_method_menu(),
        )
        return

    if data == "pay_card":
        state = get_state(user_id)
        plan = PLANS.get((state.get("data") or {}).get("plan_id"), {})
        set_state(user_id, "card_info", state.get("data") or {})
        price = f"{plan.get('price', 0):,}".replace(",", "٬")
        await edit_message(
            callback,
            f"💳 کارت به کارت\n\nمبلغ {price} تومن برای اشتراک {plan.get('title', '')} را به این کارت واریز کن:\n\n`{CARD_NUMBER}`\n\nبعد روی «واریز کردم» بزن و عکس رسید را بفرست.",
            card_pay_menu(),
        )
        return

    if data == "pay_gift":
        state = get_state(user_id)
        set_state(user_id, "gift_code", state.get("data") or {})
        await edit_message(
            callback,
            "🎁 پاکت هدیه\n\nکد یا پیام پاکت هدیه را همین جا بفرست.",
            back_only(),
        )
        return

    if data == "pay_paid":
        state = get_state(user_id)
        set_state(user_id, "wait_receipt", state.get("data") or {})
        await edit_message(
            callback,
            "🖼 عکس واریزی را بفرست.\nاگر توضیحی داری زیر همان عکس بنویس.",
            back_only(),
        )
        return

    if data.startswith("adm_ok_"):
        if callback.from_user.id not in ADMIN_IDS:
            return
        req_id = data.replace("adm_ok_", "", 1)
        payments = load_payments()
        item = payments.get(req_id)
        if not item or item.get("status") != "pending":
            await edit_message(callback, "ℹ️ این درخواست قبلاً بررسی شده.")
            return
        days = int(item.get("days") or 0)
        code = create_license(days)
        item["status"] = "approved"
        item["license"] = code
        payments[req_id] = item
        save_payments(payments)
        send_message(
            item["user_id"],
            "🎉 پرداخت تایید شد\n\n"
            f"🔑 کد لایسنس تو:\n{code}\n\n"
            f"📅 اشتراک: {item.get('title') or str(days) + ' روز'}\n\n"
            "این کد را نزد کسی نده.\nروی دکمه زیر بزن و کد را وارد کن.",
            license_button(),
        )
        await edit_message(callback, f"✅ تایید شد\n🔑 {code}")
        return

    if data.startswith("adm_no_"):
        if callback.from_user.id not in ADMIN_IDS:
            return
        req_id = data.replace("adm_no_", "", 1)
        payments = load_payments()
        item = payments.get(req_id)
        if item:
            item["status"] = "rejected"
            payments[req_id] = item
            save_payments(payments)
            send_message(
                item["user_id"],
                "❌ واریز تایید نشد.\nاگر فکر می‌کنی اشتباهی شده، به پشتیبانی پیام بده.",
                inline_keyboard([[("🏠 منوی اصلی", "m_home")]]),
            )
        await edit_message(callback, "❌ درخواست رد شد.")
        return

    if data.startswith("adm_msg_"):
        if callback.from_user.id not in ADMIN_IDS:
            return
        req_id = data.replace("adm_msg_", "", 1)
        set_state(callback.from_user.id, "admin_msg", {"req_id": req_id})
        await edit_message(callback, "📝 پیامت را بفرست تا برای کاربر ارسال شود.")
        return


@bot.event
async def on_message(message: Message):
    if message.from_user is None:
        return
    user_id = message.from_user.id
    state = get_state(user_id)
    name = state.get("state")
    text = (message.content or "").strip()

    if name == "enter_license":
        ok, result = redeem_license(user_id, text)
        clear_state(user_id)
        if ok:
            await message.reply(
                f"✅ لایسنس با موفقیت فعال شد\n\n⭐ اشتراک {result} روزه برایت روشن شد.\nالان می‌تونی تا ۳ کانال ثبت کنی و از همه قابلیت‌ها استفاده کنی.",
                components=home_inline_menu(show_free=False),
            )
        else:
            await message.reply(
                f"❌ {result}\n\nاگر کد را اشتباه زدی دوباره امتحان کن.",
                components=home_components(user_id),
            )
        return

    if name == "admin_msg" and user_id in ADMIN_IDS:
        req_id = (state.get("data") or {}).get("req_id")
        payments = load_payments()
        item = payments.get(req_id) or {}
        if item.get("user_id"):
            send_message(item["user_id"], f"📩 پیام ادمین:\n\n{text}")
        clear_state(user_id)
        await message.reply("✅ پیام برای کاربر ارسال شد.")
        return

    if name in ("wait_receipt", "gift_code"):
        plan_id = (state.get("data") or {}).get("plan_id")
        plan = PLANS.get(plan_id) or {}
        req_id = str(int(time.time())) + str(user_id)
        mention = user_mention(message.from_user)
        note = text or "بدون توضیح"
        payments = load_payments()
        payments[req_id] = {
            "user_id": user_id,
            "username": mention,
            "plan_id": plan_id,
            "days": plan.get("days"),
            "price": plan.get("price"),
            "title": plan.get("title"),
            "note": note,
            "status": "pending",
        }
        save_payments(payments)
        price = f"{plan.get('price', 0):,}".replace(",", "٬")
        admin_text = (
            "📬 درخواست واریز جدید\n"
            "━━━━━━━━━━━━━━\n"
            f"👤 کاربر: {mention}\n"
            f"📅 اشتراک: {plan.get('title')}\n"
            f"💰 مبلغ: {price} تومن\n"
            f"📝 توضیح: {note}"
        )
        photo = extract_photo(message)
        for admin_id in ADMIN_IDS:
            copied = {"ok": False}
            try:
                copied = copy_message(admin_id, user_id, getattr(message, "message_id", None) or getattr(message, "id", None))
            except Exception:
                copied = {"ok": False}
            if photo and not copied.get("ok"):
                send_photo(admin_id, photo, admin_text, admin_markup(req_id))
            else:
                send_message(admin_id, admin_text, admin_markup(req_id))
        clear_state(user_id)
        await message.reply(
            "✅ عکس واریزی برای ادمین ارسال شد.\n\n⏳ حداکثر چند ساعت صبر کن تا بررسی شود.",
            components=home_components(user_id),
        )
        return
