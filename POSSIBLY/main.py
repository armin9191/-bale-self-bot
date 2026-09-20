import logging
import bale

from config import settings
from database.postgres import init_db
from bot.handlers import register_handlers

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("POSSIBLY")


def main() -> None:
    logger.info("POSSIBLY starting")
    bot = bale.Bot(token=settings.BOT_TOKEN)

    @bot.event
    async def on_ready():
        await init_db()
        logger.info("Connected to PostgreSQL")
        logger.info("POSSIBLY initialized")

    register_handlers(bot)
    bot.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("POSSIBLY stopped")
