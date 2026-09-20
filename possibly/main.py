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


async def prepare():
    logger.info("POSSIBLY starting")

    await init_db()

    logger.info("PostgreSQL connected")

    return


def main():
    asyncio.run(prepare())

    bot = bale.Bot(
        token=settings.BOT_TOKEN
    )

    register_handlers(bot)

    logger.info("POSSIBLY initialized")
    logger.info("POSSIBLY is starting Bale polling")

    try:
        bot.run()
    except KeyboardInterrupt:
        logger.info("POSSIBLY stopped")
    except Exception:
        logger.exception("POSSIBLY crashed")
        raise
    finally:
        try:
            asyncio.run(close_db())
        except Exception:
            logger.exception(
                "Failed to close PostgreSQL connection pool"
            )


if __name__ == "__main__":
    main()
