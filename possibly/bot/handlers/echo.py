# POSSIBLY
# Echo handler


from __future__ import annotations

import logging

from bot.messages import message


logger = logging.getLogger("POSSIBLY.echo")


def register(bot) -> None:
    """
    Echo handler registration.

    The actual Bale event decorator is intentionally kept out of this
    module until the installed python-bale-bot API is verified.
    """

    logger.info("Echo handler registered")


async def handle_echo(
    bot,
    msg,
    text: str,
) -> None:
    """
    Handle:

        اکو سلام

    The caller is responsible for registering this function with the
    verified Bale message-handler API.
    """

    text = text.strip()

    if not text:
        await msg.reply(
            message("اکو")
        )
        return

    await msg.reply(
        message(text)
    )
