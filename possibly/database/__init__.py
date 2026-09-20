```python
# POSSIBLY
# Central handler registry

from __future__ import annotations

import logging

import bale

from bot.handlers.admin import register_admin_handlers
from bot.handlers.backup import register_backup_handlers
from bot.handlers.echo import register_echo_handlers
from bot.handlers.games import register_game_handlers
from bot.handlers.gif import register_gif_handlers
from bot.handlers.learning import register_learning_handlers
from bot.handlers.stats import register_stats_handlers
from bot.handlers.whisper import register_whisper_handlers


logger = logging.getLogger("POSSIBLY.handlers")


def register_handlers(bot: bale.Bot) -> None:
    """
    تمام Handlerهای POSSIBLY را ثبت می‌کند.

    Handlerهای واقعی در فایل‌های جدا نگهداری می‌شوند تا
    business logic با registration قاطی نشود.
    """

    register_admin_handlers(bot)
    register_backup_handlers(bot)
    register_echo_handlers(bot)
    register_game_handlers(bot)
    register_gif_handlers(bot)
    register_learning_handlers(bot)
    register_stats_handlers(bot)
    register_whisper_handlers(bot)

    logger.info("Handler registry loaded")
```
