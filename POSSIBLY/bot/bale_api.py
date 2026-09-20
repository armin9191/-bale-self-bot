"""Thin helpers for Bale HTTP methods missing from python-bale-bot."""
from __future__ import annotations

import logging
from typing import Optional

import aiohttp

from config import settings

log = logging.getLogger("POSSIBLY.bale_api")

BASE = "https://tapi.bale.ai/bot"


async def answer_callback_query(
    callback_query_id: str,
    text: Optional[str] = None,
    *,
    show_alert: bool = False,
    cache_time: int = 0,
) -> bool:
    """
    Official Bale API: answerCallbackQuery
    Shows a private notification/alert ONLY to the user who pressed the button.
    show_alert=True → modal dialog with OK (client-side).
    text is typically limited (~200 chars on Bale).
    """
    url = f"{BASE}{settings.BOT_TOKEN}/answerCallbackQuery"
    payload: dict = {
        "callback_query_id": str(callback_query_id),
        "show_alert": bool(show_alert),
        "cache_time": int(cache_time),
    }
    if text is not None:
        # hard limit for safety
        payload["text"] = text[:200]

    try:
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload) as resp:
                data = await resp.json(content_type=None)
                if resp.status != 200 or not data.get("ok", False):
                    log.warning("answerCallbackQuery failed: status=%s body=%s", resp.status, data)
                    return False
                return True
    except Exception as e:
        log.warning("answerCallbackQuery error: %s", e)
        return False
