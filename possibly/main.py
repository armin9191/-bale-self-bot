import asyncio
import logging

import bale

from config import settings
from database.postgres import close_db, init_db
from bot.handlers import register_handlers


logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)

logger = logging.getLogger("POSSIBLY")


async def main():
    logger.info("POSSIBLY starting")

    await init_db()

    bot = bale.Bot(
        token=settings.BOT_TOKEN
    )

    register_handlers(bot)

    logger.info("POSSIBLY initialized")

    try:
        await bot.run()
    finally:
        await close_db()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("POSSIBLY stopped")
