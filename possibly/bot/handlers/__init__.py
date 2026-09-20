import logging

logger = logging.getLogger("POSSIBLY.handlers")


def register_handlers(bot):
    """
    Central handler registration point.

    The exact handler decorators/classes are kept version-pinned to
    python-bale-bot 2.5.0 and will be added in the implementation phase.
    """
    logger.info("Handler registry loaded")
