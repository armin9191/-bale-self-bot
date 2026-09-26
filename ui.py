async def edit_message(target, text, components=None):
    message = getattr(target, "message", target)
    try:
        if components is None:
            await message.edit(text)
        else:
            await message.edit(text, components=components)
        return True
    except Exception:
        try:
            if components is None:
                await message.reply(text)
            else:
                await message.reply(text, components=components)
        except Exception:
            return False
        return False
