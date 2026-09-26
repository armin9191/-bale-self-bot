from bale import CallbackQuery

from client import bot
from ui import edit_message
from keyboards import (
    channel_settings_menu,
    delete_channel_menu,
    category_menu,
    send_time_menu,
)
from users import (
    delete_channel,
    toggle_channel_image,
    toggle_channel_emoji,
    get_user,
    update_categories,
    update_send_time,
)
from handlers.channel import show_channels
from states import set_state, get_state, clear_state
from subscription import is_free_user, FREE_ALLOWED_CATEGORIES, FREE_LOCKED_TIMES


def _locks(user_id):
    if is_free_user(user_id):
        locked_cats = [name for name in ("جنگ", "اقتصاد", "فناوری", "سیاسی", "همه") if name not in FREE_ALLOWED_CATEGORIES]
        return locked_cats, FREE_LOCKED_TIMES
    return [], set()


def _channel_flags(user, channel_id):
    send_image = True
    show_emoji = True
    categories = ["همه"]
    interval = 10
    if not user:
        return send_image, show_emoji, categories, interval
    for channel in user.get("channels", []):
        if channel.get("id") == channel_id:
            send_image = channel.get("send_image", True)
            show_emoji = channel.get("show_emoji", True)
            categories = channel.get("categories") or ["همه"]
            interval = channel.get("interval", 10)
            break
    return send_image, show_emoji, categories, interval


def _settings_text(channel_id, send_image, show_emoji, categories, interval):
    image_state = "روشن" if send_image else "خاموش"
    emoji_state = "روشن" if show_emoji else "خاموش"
    cats = "، ".join(categories) if categories else "همه"
    return (
        f"⚙️ تنظیمات کانال\n\n"
        f"📢 {channel_id}\n"
        f"🖼 عکس: {image_state}\n"
        f"😀 ایموجی: {emoji_state}\n"
        f"⏱ فاصله ارسال: {interval} دقیقه\n"
        f"🏷 دسته‌ها: {cats}\n\n"
        "از دکمه‌های زیر برای تغییر استفاده کنید."
    )


async def _show_settings(callback, channel_id):
    user = get_user(callback.from_user.id)
    send_image, show_emoji, categories, interval = _channel_flags(user, channel_id)
    await edit_message(
        callback,
        _settings_text(channel_id, send_image, show_emoji, categories, interval),
        channel_settings_menu(channel_id, send_image, show_emoji),
    )


@bot.event
async def on_callback(callback: CallbackQuery):
    data = callback.data or ""
    user_id = callback.from_user.id
    locked_cats, locked_times = _locks(user_id)

    if data.startswith("cat_select_"):
        category = data.replace("cat_select_", "", 1)
        if category in locked_cats:
            await edit_message(callback, "این دسته با اشتراک رایگان قفل است.", category_menu(get_state(user_id)["data"].get("categories", []), locked_cats))
            return
        state = get_state(user_id)
        selected = list(state["data"].get("categories", []))
        if category == "همه":
            selected = ["همه"]
        else:
            selected = [item for item in selected if item != "همه"]
            if category in selected:
                selected.remove(category)
            else:
                selected.append(category)
            if not selected:
                selected = ["ورزش"] if locked_cats else ["همه"]
        state["data"]["categories"] = selected
        set_state(user_id, state["state"] or "category_select", state["data"])
        pretty = "، ".join(selected)
        await edit_message(
            callback,
            "🏷 انتخاب دسته‌بندی\n\n"
            f"انتخاب فعلی: {pretty}",
            category_menu(selected, locked_cats),
        )
        return

    if data.startswith("channel_"):
        await _show_settings(callback, data.replace("channel_", "", 1))
        return

    if data.startswith("time_"):
        channel_id = data.replace("time_", "", 1)
        await edit_message(
            callback,
            "⏱ فاصله ارسال خبر\n\nهر چند دقیقه یک خبر جدید فرستاده شود؟",
            send_time_menu(channel_id, locked_times),
        )
        return

    if data.startswith("stime_"):
        try:
            parts = data.split("_", 2)
            interval = int(parts[1])
            channel_id = parts[2].strip()
            if interval in locked_times:
                await edit_message(callback, "این زمان با اشتراک رایگان قفل است.", send_time_menu(channel_id, locked_times))
                return
            if update_send_time(user_id, channel_id, interval):
                await _show_settings(callback, channel_id)
            else:
                await edit_message(callback, "زمان ارسال ذخیره نشد.")
        except Exception as error:
            print("خطا در تغییر زمان ارسال:", error)
            await edit_message(callback, "زمان ارسال ذخیره نشد.")
        return

    if data.startswith("img_"):
        toggle_channel_image(user_id, data.replace("img_", "", 1))
        await _show_settings(callback, data.replace("img_", "", 1))
        return

    if data.startswith("emoji_"):
        toggle_channel_emoji(user_id, data.replace("emoji_", "", 1))
        await _show_settings(callback, data.replace("emoji_", "", 1))
        return

    if data == "cat_save":
        state = get_state(user_id)
        if state["state"] != "category_select":
            return
        channel_id = state["data"]["channel_id"]
        categories = state["data"].get("categories") or ["همه"]
        if update_categories(user_id, channel_id, categories):
            clear_state(user_id)
            await _show_settings(callback, channel_id)
        else:
            await edit_message(callback, "دسته‌بندی ذخیره نشد.")
        return

    if data.startswith("cat_"):
        channel_id = data.replace("cat_", "", 1)
        user = get_user(user_id)
        _, _, categories, _ = _channel_flags(user, channel_id)
        set_state(user_id, "category_select", {"channel_id": channel_id, "categories": list(categories)})
        pretty = "، ".join(categories)
        await edit_message(
            callback,
            "🏷 انتخاب دسته‌بندی\n\n"
            f"انتخاب فعلی: {pretty}",
            category_menu(categories, locked_cats),
        )
        return

    if data.startswith("delete_"):
        channel_id = data.replace("delete_", "", 1)
        await edit_message(callback, f"حذف کانال {channel_id} انجام شود؟", delete_channel_menu(channel_id))
        return

    if data.startswith("yesdel_"):
        channel_id = data.replace("yesdel_", "", 1)
        delete_channel(user_id, channel_id)
        await edit_message(callback, "کانال حذف شد.")
        return

    if data.startswith("nodel_"):
        await _show_settings(callback, data.replace("nodel_", "", 1))
        return
