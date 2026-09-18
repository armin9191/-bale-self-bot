# bot/handlers.py
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict

from bot.api import BaleBotAPI
from core import database as db
from core.auth_service import (
    send_login_code,
    session_exists,
    verify_code,
    verify_password,
)
from core.config import MAX_USERS

logger = logging.getLogger(__name__)


def _uid(message: Dict[str, Any]) -> int:
    return int(message["from"]["id"])


def _chat_id(message: Dict[str, Any]) -> int:
    return int(message["chat"]["id"])


def _text(message: Dict[str, Any]) -> str:
    return (message.get("text") or "").strip()


async def handle_message(bot: BaleBotAPI, message: Dict[str, Any]) -> None:
    if "from" not in message:
        return

    user_id = _uid(message)
    chat_id = _chat_id(message)
    text = _text(message)
    if not text:
        return

    if text in ("/start", "/help"):
        await cmd_start(bot, chat_id, user_id)
        return
    if text == "/status":
        await cmd_status(bot, chat_id, user_id)
        return
    if text == "/logout":
        await cmd_logout(bot, chat_id, user_id)
        return
    if text == "/cancel":
        db.clear_login_state(user_id)
        bot.send_message(chat_id, "لغو شد. /start")
        return

    state = db.get_login_state(user_id)
    if state:
        step = state.get("step")
        if step == "wait_phone":
            await on_phone(bot, chat_id, user_id, text)
            return
        if step == "wait_code":
            await on_code(bot, chat_id, user_id, text, state)
            return
        if step == "wait_password":
            await on_password(bot, chat_id, user_id, text, state)
            return

    bot.send_message(chat_id, "/start /status /logout /cancel")


async def cmd_start(bot: BaleBotAPI, chat_id: int, user_id: int) -> None:
    user = db.get_user(user_id)
    if user and user.get("status") == "active" and session_exists(user_id):
        bot.send_message(
            chat_id,
            "قبلاً وارد شده‌اید.\n"
            f"شماره: {user.get('phone')}\n"
            f"سشن: {user.get('session_file')}\n"
            "دستورات را در Saved Messages بزنید.",
        )
        return

    if db.count_users() >= MAX_USERS and not (user and user.get("status") == "active"):
        bot.send_message(chat_id, "ظرفیت پر است.")
        return

    db.set_login_state(user_id, step="wait_phone")
    bot.send_message(chat_id, "شماره موبایل بله را بفرستید.\nمثال: 09123456789")


async def cmd_status(bot: BaleBotAPI, chat_id: int, user_id: int) -> None:
    user = db.get_user(user_id)
    if not user or user.get("status") != "active":
        bot.send_message(chat_id, "وارد نشده‌اید. /start")
        return
    bot.send_message(
        chat_id,
        f"وضعیت: {'فعال' if session_exists(user_id) else 'سشن ناقص'}\n"
        f"شماره: {user.get('phone')}\n"
        f"سشن: {user.get('session_file')}",
    )


async def cmd_logout(bot: BaleBotAPI, chat_id: int, user_id: int) -> None:
    user = db.get_user(user_id)
    if user and user.get("session_file"):
        p = Path(user["session_file"])
        if p.exists():
            p.unlink()
    db.upsert_user(user_id, status="logged_out")
    db.clear_login_state(user_id)
    bot.send_message(chat_id, "خارج شدید. /start")


async def on_phone(bot: BaleBotAPI, chat_id: int, user_id: int, text: str) -> None:
    bot.send_message(chat_id, "در حال ارسال کد...")
    result = await send_login_code(user_id, text)
    if not result.get("ok"):
        bot.send_message(chat_id, str(result.get("error")))
        return
    db.set_login_state(
        user_id,
        step="wait_code",
        phone=result["phone"],
        transaction_hash=result["transaction_hash"],
    )
    bot.send_message(chat_id, "کد را وارد کنید.")


async def on_code(bot: BaleBotAPI, chat_id: int, user_id: int, text: str, state: Dict[str, Any]) -> None:
    tx = state.get("transaction_hash")
    if not tx:
        db.set_login_state(user_id, step="wait_phone")
        bot.send_message(chat_id, "منقضی شد. دوباره شماره بفرستید.")
        return
    result = await verify_code(user_id, text, tx)
    if result.get("need_password"):
        db.set_login_state(user_id, step="wait_password", transaction_hash=tx)
        bot.send_message(chat_id, "رمز دو مرحله‌ای را وارد کنید.")
        return
    if not result.get("ok"):
        bot.send_message(chat_id, str(result.get("error")))
        return
    await _finish_login(bot, chat_id, user_id, state.get("phone"), result)


async def on_password(bot: BaleBotAPI, chat_id: int, user_id: int, text: str, state: Dict[str, Any]) -> None:
    tx = state.get("transaction_hash")
    if not tx:
        db.clear_login_state(user_id)
        bot.send_message(chat_id, "منقضی شد. /start")
        return
    result = await verify_password(user_id, text, tx)
    if not result.get("ok"):
        bot.send_message(chat_id, str(result.get("error")))
        return
    await _finish_login(bot, chat_id, user_id, state.get("phone"), result)


async def _finish_login(bot: BaleBotAPI, chat_id: int, user_id: int, phone: str, result: Dict[str, Any]) -> None:
    db.upsert_user(
        user_id,
        phone=phone,
        session_file=result.get("session_file"),
        account_id=result.get("account_id"),
        account_name=result.get("account_name"),
        status="active",
    )
    db.clear_login_state(user_id)

    session_file = result.get("session_file")
    if session_file:
        try:
            from worker.session_worker import spawn_session
            spawn_session(user_id, session_file, result.get("account_id"))
        except Exception:
            logger.exception("could not start session after login")

    bot.send_message(
        chat_id,
        "ورود موفق. سشن باید آنلاین شود.\n"
        "در Saved Messages بزنید: /help",
    )