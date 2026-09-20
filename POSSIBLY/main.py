"""
POSSIBLY — Group Management + Fun + Games Bot for Bale.

Lifecycle note (python-bale-bot 2.5.0):
  bot.run() manages its own event loop.
  Do NOT wrap it in asyncio.run().
"""
from __future__ import annotations

import logging
import sys

from bale import Bot

from config import settings
from database.postgres import init_db, close_db
from bot.handlers.dispatcher import register_handlers

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("POSSIBLY")


def main() -> None:
    if not settings.BOT_TOKEN or settings.BOT_TOKEN.startswith("REPLACE_"):
        log.error("BOT_TOKEN is not set. Set the BOT_TOKEN environment variable.")
        sys.exit(1)

    log.info("POSSIBLY starting")
    bot = Bot(token=settings.BOT_TOKEN)

    @bot.event
    async def on_ready():
        try:
            await init_db()
            log.info("Connected to PostgreSQL")
        except Exception as e:
            log.error("PostgreSQL init failed: %s", e)
            # Bot continues; handlers that need DB will fail gracefully.
        log.info("Handler registry loaded")
        log.info("POSSIBLY initialized")
        log.info("Bot is running")

    register_handlers(bot)
    try:
        bot.run()
    finally:
        # Best-effort cleanup if the process is shutting down.
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            loop.run_until_complete(close_db())
            loop.close()
        except Exception:
            pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.info("POSSIBLY stopped by user")
