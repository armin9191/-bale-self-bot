# POSSIBLY
# Python 3.12+

import logging

import bale

from config import settings
from database.postgres import close_db, init_db
from bot.handlers import register_handlers


# ============================================================
# Logging
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)

logger = logging.getLogger("POSSIBLY")


# ============================================================
# Main
# ============================================================

def main() -> None:
    logger.info("POSSIBLY starting")

    try:
        # ----------------------------------------------------
        # PostgreSQL
        # ----------------------------------------------------
        #
        # init_db فعلاً async است، بنابراین برای این مرحله
        # قبل از اجرای Bale آن را با یک event loop موقت
        # اجرا می‌کنیم.
        #
        import asyncio

        asyncio.run(init_db())

        logger.info("Connected to PostgreSQL")

        # ----------------------------------------------------
        # Bale Bot
        # ----------------------------------------------------

        bot = bale.Bot(
            token=settings.BOT_TOKEN,
        )

        # ----------------------------------------------------
        # Register handlers
        # ----------------------------------------------------

        register_handlers(bot)

        logger.info("POSSIBLY initialized")

        # ----------------------------------------------------
        # Start Bale polling
        # ----------------------------------------------------
        #
        # مهم:
        # bot.run() خودش event loop را مدیریت می‌کند.
        # بنابراین نباید بنویسیم:
        #
        # await bot.run()
        #
        # یا:
        #
        # asyncio.run(bot.run())
        #

        bot.run()

    except KeyboardInterrupt:
        logger.info("POSSIBLY stopped")

    except Exception:
        logger.exception("POSSIBLY crashed")

        raise

    finally:
        # ----------------------------------------------------
        # PostgreSQL cleanup
        # ----------------------------------------------------
        #
        # چون bot.run() بعد از توقف خارج می‌شود، اینجا
        # connection pool را می‌بندیم.
        #

        try:
            import asyncio

            asyncio.run(close_db())

        except Exception:
            logger.exception(
                "Failed to close PostgreSQL connection pool"
            )


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    main()
