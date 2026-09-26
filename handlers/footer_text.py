from bale import CallbackQuery, Message

from client import bot

from keyboards import (
    footer_preview_menu, 
    footer_manage_menu, 
    footer_delete_menu
)

from states import (
    set_state,
    get_state,
    clear_state
)

from users import (
    update_footer_text,
    get_user
)

from keyboards import (
    channel_settings_menu,
    channel_settings_bottom_menu
)



@bot.event
async def on_callback(callback: CallbackQuery):

    data = callback.data

    user_id = callback.from_user.id


    # ==========================
    # باز کردن متن پایین خبر
    # ==========================

    if data.startswith("link_"):

        channel_id = data.replace(
            "link_",
            "",
            1
        )


        user = get_user(user_id)

        footer = ""


        if user:

            for channel in user.get(
                "channels",
                []
            ):

                if channel["id"] == channel_id:

                    footer = channel.get(
                        "footer_text",
                        ""
                    )

                    break



        if footer:

            set_state(
                user_id,
                "footer_manage",
                {
                    "channel_id": channel_id
                }
            )


            await callback.message.reply(
                "✏️ متن فعلی پایین خبر\n\n"
                "━━━━━━━━━━━━━━\n\n"
                f"{footer}\n\n"
                "━━━━━━━━━━━━━━\n\n"
                "لطفاً یکی از گزینه‌ها را انتخاب کنید.", 
                components=footer_manage_menu()
            )

            return



        set_state(
            user_id,
            "footer_text",
            {
                "channel_id": channel_id
            }
        )


        await callback.message.reply(
            "✏️ تنظیم متن پایین خبر\n\n"
            f"📢 کانال:\n{channel_id}\n\n"
            "لطفاً متن دلخواه خود را ارسال کنید.\n\n"
            "این متن زیر تمام خبرهای این کانال نمایش داده می‌شود."
        )

        return



    # ==========================
    # تایید ذخیره
    # ==========================

    if data == "footer_save":

        state = get_state(user_id)


        if state["state"] != "footer_confirm":

            return


        channel_id = state["data"].get(
            "channel_id"
        )

        text = state["data"].get(
            "text"
        )


        result = update_footer_text(
            user_id,
            channel_id,
            text
        )


        if result:

            await callback.message.reply(
                "✅ متن پایین خبر با موفقیت ذخیره شد."
            )


            user = get_user(user_id)

            send_image = True
            show_emoji = True


            for channel in user["channels"]:

                if channel["id"] == channel_id:

                    send_image = channel.get(
                        "send_image",
                        True
                    )

                    show_emoji = channel.get(
                        "show_emoji",
                        True
                    )

                    break


            await callback.message.reply(
                f"⚙️ تنظیمات کانال\n\n{channel_id}",
                components=channel_settings_menu(
                    channel_id,
                    send_image,
                    show_emoji
                )
            )


            await callback.message.reply(
                "لیست کانال‌های شما",
                components=channel_settings_bottom_menu()
            )

        else:

            await callback.message.reply(
                "❌ خطا در ذخیره متن."
            )


        clear_state(user_id)

        return



    # ==========================
    # ویرایش
    # ==========================

    if data == "footer_edit":

        state = get_state(user_id)


        set_state(
            user_id,
            "footer_text",
            {
                "channel_id":
                state["data"].get(
                    "channel_id"
                )
            }
        )


        await callback.message.reply(
            "✏️ ویرایش متن پایین خبر\n\n"
            "لطفاً متن جدید را ارسال کنید.\n\n"
            "این متن جایگزین متن قبلی خواهد شد."
        )

        return

# ==========================
    # درخواست حذف متن پایین خبر
# ==========================

    if data == "footer_delete":

        state = get_state(user_id)


        if state["state"] != "footer_manage":

            return


        await callback.message.reply(
            "⚠️ آیا از حذف متن پایین خبر مطمئن هستید؟",
            components=footer_delete_menu()
        )

        return
        
        
        # ==========================
    # تایید حذف متن پایین خبر
    # ==========================

    if data == "footer_delete_yes":

        state = get_state(user_id)


        if state["state"] != "footer_manage":

            return


        channel_id = state["data"].get(
            "channel_id"
        )


        result = update_footer_text(
            user_id,
            channel_id,
            ""
        )


        if result:

            await callback.message.reply(
                "✅ متن پایین خبر حذف شد."
            )


            user = get_user(user_id)

            send_image = True
            show_emoji = True


            for channel in user["channels"]:

                if channel["id"] == channel_id:

                    send_image = channel.get(
                        "send_image",
                        True
                    )

                    show_emoji = channel.get(
                        "show_emoji",
                        True
                    )

                    break


            await callback.message.reply(
                f"⚙️ تنظیمات کانال\n\n{channel_id}",
                components=channel_settings_menu(
                    channel_id,
                    send_image,
                    show_emoji
                )
            )


            await callback.message.reply(
                "لیست کانال‌های شما",
                components=channel_settings_bottom_menu()
            )


        else:

            await callback.message.reply(
                "❌ خطا در حذف متن."
            )


        clear_state(user_id)

        return
        
        
        # ==========================
    # لغو حذف متن پایین خبر
    # ==========================

    if data == "footer_delete_no":

        state = get_state(user_id)


        if state["state"] != "footer_manage":

            return


        await callback.message.reply(
            "❌ حذف متن لغو شد."
        )

        return


    # ==========================
    # انصراف
    # ==========================

    if data == "footer_cancel":

        clear_state(user_id)


        await callback.message.reply(
            "❌ عملیات لغو شد."
        )

        return



@bot.event
async def on_message(message: Message):

    if message.from_user is None:

        return


    user_id = message.from_user.id


    state = get_state(user_id)


    if state["state"] != "footer_text":

        return



    text = message.content.strip()



    if text in [
        "🔙 بازگشت",
        "🏠 منوی اصلی",
        "❌ انصراف"
    ]:

        clear_state(user_id)

        return



    state["data"]["text"] = text


    set_state(
        user_id,
        "footer_confirm",
        state["data"]
    )


    await message.reply(
    "👀 پیش‌نمایش متن پایین خبر\n\n"
    "━━━━━━━━━━━━━━\n\n"
    f"{text}\n\n"
    "━━━━━━━━━━━━━━\n\n"
    "آیا از ذخیره این متن مطمئن هستید؟",
    components=footer_preview_menu()
)