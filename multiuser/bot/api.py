# bot/api.py
"""کلاینت ساده Bot API بله با requests (بدون وابستگی سنگین)."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import requests

from core.config import BOT_TOKEN, BALE_BOT_API

logger = logging.getLogger(__name__)


class BaleBotAPI:
    def __init__(self, token: str = BOT_TOKEN, base: str = BALE_BOT_API, timeout: int = 35):
        self.base = f"{base}{token}"
        self.timeout = timeout
        self.session = requests.Session()

    def _call(self, method: str, **payload) -> Dict[str, Any]:
        url = f"{self.base}/{method}"
        try:
            r = self.session.post(url, json=payload, timeout=self.timeout)
            data = r.json()
            return data
        except Exception as e:
            logger.error("API %s failed: %s", method, e)
            return {"ok": False, "description": str(e)}

    def get_me(self) -> Dict[str, Any]:
        return self._call("getMe")

    def delete_webhook(self) -> Dict[str, Any]:
        return self._call("deleteWebhook")

    def get_updates(
        self,
        offset: Optional[int] = None,
        timeout: int = 25,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        payload: Dict[str, Any] = {"timeout": timeout, "limit": limit}
        if offset is not None:
            payload["offset"] = offset
        data = self._call("getUpdates", **payload)
        if not data.get("ok"):
            return []
        return data.get("result") or []

    def send_message(
        self,
        chat_id: int,
        text: str,
        reply_to_message_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"chat_id": chat_id, "text": text}
        if reply_to_message_id is not None:
            payload["reply_to_message_id"] = reply_to_message_id
        return self._call("sendMessage", **payload)
