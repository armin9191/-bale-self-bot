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


def main():
    logger.info("POSSIBLY starting")

    try:
        init_db_sync()

        bot = bale.Bot(
            token=settings.BOT_TOKEN
        )

        register_handlers(bot)

        logger.info("POSSIBLY initialized")

        bot.run()

    finally:
        close_db_sync()


def init_db_sync():
    import asyncio
    asyncio.run(init_db())


def close_db_sync():
    import asyncio
    asyncio.run(close_db())


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("POSSIBLY stopped")
