# POSSIBLY
# Central handler registration


import logging

from bot.handlers import admin
from bot.handlers import echo
from bot.handlers import games
from bot.handlers import learning
from bot.handlers import stats
from bot.handlers import whisper
from bot.handlers import gif


logger = logging.getLogger("POSSIBLY.handlers")


def register_handlers(bot) -> None:
    """
    Register all POSSIBLY handlers.

    Each handler module owns its own Bale decorators/registration logic.
    """

    admin.register(bot)
    learning.register(bot)
    stats.register(bot)
    echo.register(bot)
    whisper.register(bot)
    gif.register(bot)
    games.register(bot)

    logger.info("All POSSIBLY handlers registered")
