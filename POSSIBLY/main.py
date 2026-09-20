"""POSSIBLY entrypoint — python-bale-bot 2.5.0 lifecycle."""
from __future__ import annotations

import logging
import sys

from bale import Bot

from config import settings
from database.postgres import init_db
from bot.handlers.dispatcher import register_handlers

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s", stream=sys.stdout)
log = logging.getLogger("POSSIBLY")


def main() -> None:
    log.info("POSSIBLY starting")
    bot = Bot(token=settings.BOT_TOKEN)

    @bot.event
    async def on_ready():
        try:
            await init_db()
            log.info("Connected to PostgreSQL")
        except Exception as e:
            log.error("PostgreSQL init failed: %s", e)
        log.info("Handler registry loaded")
        log.info("POSSIBLY initialized")
        log.info("Bot is running")

    register_handlers(bot)
    bot.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.info("POSSIBLY stopped")
