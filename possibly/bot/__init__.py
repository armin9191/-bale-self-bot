# POSSIBLY
# Central handler registration


from __future__ import annotations

import logging

import bale


logger = logging.getLogger("POSSIBLY.handlers")


def register_handlers(bot: bale.Bot) -> None:
    """
    Register all POSSIBLY handlers.

    Handler modules are imported here instead of keeping all
    registrations inside main.py.
    """

    from bot.handlers.admin import register as register_admin
    from bot.handlers.learning import register as register_learning
    from bot.handlers.stats import register as register_stats
    from bot.handlers.echo import register as register_echo
    from bot.handlers.whisper import register as register_whisper
    from bot.handlers.gif import register as register_gif
    from bot.handlers.games import register as register_games
    from bot.handlers.backup import register as register_backup

    register_admin(bot)
    register_learning(bot)
    register_stats(bot)
    register_echo(bot)
    register_whisper(bot)
    register_gif(bot)
    register_games(bot)
    register_backup(bot)

    logger.info("Handler registry loaded")
