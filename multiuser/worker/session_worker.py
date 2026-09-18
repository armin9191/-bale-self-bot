# worker/session_worker.py
from __future__ import annotations

import asyncio
import logging
import random
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Optional

from aiobale import Client, Dispatcher, F
from aiobale.enums import ChatType
from aiobale.exceptions import BaleError
from aiobale.types import Message

from core.database import list_active_sessions

logger = logging.getLogger(__name__)

TEHRAN = timezone(timedelta(hours=3, minutes=30))
NAME_INTERVAL = 60

SWEARS = [
    "کصخل", "کیری", "حرومزاده", "لاشی", "جنده",
    "کصکش", "مادرجنده", "گوه", "احمق", "بی‌شعور",
    "کثافت", "ننه جنده", "پدر سگ", "حرومی", "گوساله",
]

_clients: Dict[int, Client] = {}
_tasks: Dict[int, asyncio.Task] = {}
_clock_tasks: Dict[int, asyncio.Task] = {}
_states: Dict[int, "UserState"] = {}


@dataclass
class UserState:
    afk_on: bool = False
    afk_text: str = "سلام نیستم، بعداً پیام بده."
    bold_on: bool = False
    italic_on: bool = False
    clock_on: bool = False
    name_format: str = "commander04 time"
    waiting_format: bool = False
    account_id: Optional[int] = None


def _state(bot_user_id: int) -> UserState:
    if bot_user_id not in _states:
        _states[bot_user_id] = UserState()
    return _states[bot_user_id]


def _chat_type(msg: Message) -> ChatType:
    t = msg.chat.type
    if isinstance(t, ChatType):
        return t
    try:
        return ChatType(int(getattr(t, "value", t)))
    except Exception:
        return ChatType.PRIVATE


def _is_private(msg: Message) -> bool:
    try:
        return int(getattr(msg.chat.type, "value", msg.chat.type)) == 1
    except Exception:
        return False


async def _send(msg: Message, text: str) -> None:
    tries = [
        {"chat_id": msg.chat.id, "chat_type": _chat_type(msg)},
        {"chat_id": msg.sender_id, "chat_type": ChatType.PRIVATE},
    ]
    for kwargs in tries:
        try:
            await msg.client.send_message(text=text, **kwargs)
            return
        except BaleError as e:
            logger.error("send fail %s: %s", kwargs, e)
        except Exception as e:
            logger.error("send fail %s: %s", kwargs, e)


def _is_owner(msg: Message, st: UserState) -> bool:
    me_id = st.account_id
    try:
        me = getattr(msg.client, "me", None)
        if me is not None and getattr(me, "id", None):
            me_id = me.id
        elif getattr(msg.client, "id", None):
            me_id = msg.client.id
    except Exception:
        pass
    if not me_id:
        return True
    return msg.sender_id == me_id


def _apply_style(st: UserState, text: str) -> str:
    if not text:
        return text
    if text.startswith("**") or text.startswith("__"):
        return text
    if st.bold_on and st.italic_on:
        return f"**__{text}__**"
    if st.bold_on:
        return f"**{text}**"
    if st.italic_on:
        return f"__{text}__"
    return text


def _build_dispatcher(bot_user_id: int) -> Dispatcher:
    dp = Dispatcher()
    st = _state(bot_user_id)

    @dp.message(F.text == "/help")
    async def cmd_help(msg: Message):
        if not _is_owner(msg, st):
            return
        await _send(
            msg,
            "راهنما\n\n"
            "/help — راهنما\n"
            "/status — وضعیت\n"
            "/profile — پینگ + قابلیت‌ها\n"
            "/test — تست ارسال\n"
            "/afk متن — روشن AFK\n"
            "/unafk — خاموش AFK\n"
            "/bold on|off\n"
            "/italic on|off\n"
            "/time on|off — ساعت روی اسم\n"
            "اسپم 3 متن\n"
            "رگباری 10\n"
            "ping | سلام",
        )

    @dp.message(F.text == "/status")
    async def cmd_status(msg: Message):
        if not _is_owner(msg, st):
            return
        await _send(
            msg,
            "وضعیت سیستم\n\n"
            f"AFK: {'روشن' if st.afk_on else 'خاموش'}\n"
            f"Bold: {'روشن' if st.bold_on else 'خاموش'}\n"
            f"Italic: {'روشن' if st.italic_on else 'خاموش'}\n"
            f"ساعت اسم: {'روشن' if st.clock_on else 'خاموش'}",
        )

    @dp.message(F.text == "/profile")
    async def cmd_profile(msg: Message):
        if not _is_owner(msg, st):
            return
        t0 = time.perf_counter()
        try:
            await msg.client.get_me()
            ping_ms = int((time.perf_counter() - t0) * 1000)
        except Exception:
            ping_ms = -1

        active = []
        if st.afk_on:
            active.append("AFK")
        if st.clock_on:
            active.append("ساعت اسم")
        if st.bold_on:
            active.append("Bold")
        if st.italic_on:
            active.append("Italic")
        features = " and ".join(active) if active else "هیچکدام"

        await _send(
            msg,
            "پروفایل\n\n"
            f"شناسه: {msg.sender_id}\n"
            f"چت: {msg.chat.id}\n"
            f"پینگ: {ping_ms} ms\n\n"
            f"قابلیت‌های فعال:\n{features}",
        )

    @dp.message(F.text == "/test")
    async def cmd_test(msg: Message):
        if not _is_owner(msg, st):
            return
        await _send(msg, "سیستم ارسال پیام سالم است.")

    # ----- AFK -----
    @dp.message(F.text.startswith("/afk"))
    async def cmd_afk(msg: Message):
        if not _is_owner(msg, st):
            return
        t = (msg.text or "")[4:].strip() or "سلام نیستم، بعداً پیام بده."
        st.afk_on = True
        st.afk_text = t
        await _send(msg, f"AFK روشن شد:\n{t}")

    @dp.message(F.text == "/unafk")
    async def cmd_unafk(msg: Message):
        if not _is_owner(msg, st):
            return
        st.afk_on = False
        await _send(msg, "AFK خاموش شد.")

    # ----- Bold / Italic -----
    @dp.message(F.text == "/bold on")
    async def cmd_bold_on(msg: Message):
        if not _is_owner(msg, st):
            return
        st.bold_on = True
        await _send(msg, "Bold روشن شد.")

    @dp.message(F.text == "/bold off")
    async def cmd_bold_off(msg: Message):
        if not _is_owner(msg, st):
            return
        st.bold_on = False
        await _send(msg, "Bold خاموش شد.")

    @dp.message(F.text == "/italic on")
    async def cmd_italic_on(msg: Message):
        if not _is_owner(msg, st):
            return
        st.italic_on = True
        await _send(msg, "Italic روشن شد.")

    @dp.message(F.text == "/italic off")
    async def cmd_italic_off(msg: Message):
        if not _is_owner(msg, st):
            return
        st.italic_on = False
        await _send(msg, "Italic خاموش شد.")

    # ----- Time on name -----
    @dp.message(F.text == "/time")
    async def cmd_time_help(msg: Message):
        if not _is_owner(msg, st):
            return
        await _send(
            msg,
            "ساعت روی اسم\n\n"
            "/time on — روشن + وارد کردن فرمت\n"
            "/time off — خاموش\n\n"
            "مثال فرمت: commander04 time",
        )

    @dp.message(F.text == "/time on")
    async def cmd_time_on(msg: Message):
        if not _is_owner(msg, st):
            return
        st.waiting_format = True
        await _send(
            msg,
            "فرمت اسم را بفرستید.\n"
            "مثال: commander04 time\n"
            "کلمه time با ساعت تهران جایگزین می‌شود.",
        )

    @dp.message(F.text == "/time off")
    async def cmd_time_off(msg: Message):
        if not _is_owner(msg, st):
            return
        st.clock_on = False
        st.waiting_format = False
        t = _clock_tasks.pop(bot_user_id, None)
        if t:
            t.cancel()
        await _send(msg, "ساعت روی اسم خاموش شد.")

    # ----- Spam / Ragbari -----
    @dp.message(F.text.startswith("اسپم "))
    async def cmd_spam(msg: Message):
        if not _is_owner(msg, st):
            return
        parts = msg.text.split(maxsplit=2)
        if len(parts) < 3:
            await _send(msg, "فرمت: اسپم 3 متن")
            return
        try:
            count = int(parts[1])
        except ValueError:
            await _send(msg, "عدد نامعتبر")
            return
        if count < 1 or count > 30:
            await _send(msg, "تعداد ۱ تا ۳۰")
            return
        text = parts[2]
        for _ in range(count):
            await _send(msg, text)
            await asyncio.sleep(0.4)

    @dp.message(F.text.startswith("رگباری "))
    async def cmd_ragbari(msg: Message):
        if not _is_owner(msg, st):
            return
        parts = msg.text.split()
        if len(parts) < 2:
            await _send(msg, "فرمت: رگباری 10")
            return
        try:
            count = int(parts[1])
        except ValueError:
            await _send(msg, "عدد نامعتبر")
            return
        if count < 1 or count > 50:
            await _send(msg, "تعداد ۱ تا ۵۰")
            return
        for _ in range(count):
            await _send(msg, random.choice(SWEARS))
            await asyncio.sleep(0.35)

    @dp.message(F.text.lower() == "ping")
    async def cmd_ping(msg: Message):
        if not _is_owner(msg, st):
            return
        await _send(msg, "pong")

    @dp.message(F.text == "سلام")
    async def cmd_salam(msg: Message):
        if not _is_owner(msg, st):
            return
        await _send(msg, "سلام")

    # ----- catch-all: format wait / AFK / style -----
    @dp.message(F.text)
    async def on_text(msg: Message):
        text = (msg.text or "").strip()
        if not text:
            return

        # فرمت ساعت اسم
        if st.waiting_format and _is_owner(msg, st) and not text.startswith("/"):
            if "time" not in text.lower():
                await _send(msg, "فرمت باید شامل کلمه time باشد.\nمثال: commander04 time")
                return
            st.name_format = text
            st.clock_on = True
            st.waiting_format = False
            now = datetime.now(TEHRAN).strftime("%H:%M")
            new_name = re.sub(r"time", now, text, flags=re.IGNORECASE)
            try:
                await msg.client.edit_name(new_name)
                await _send(msg, f"ساعت اسم فعال شد.\nالان: {new_name}")
            except Exception as e:
                logger.error("edit_name: %s", e)
                await _send(msg, f"فرمت ذخیره شد ولی ویرایش اسم خطا داد:\n{e}")
            _start_clock(bot_user_id, msg.client)
            return

        # AFK برای دیگران در پیوی
        if st.afk_on and not _is_owner(msg, st) and _is_private(msg) and not text.startswith("/"):
            await _send(msg, st.afk_text)
            return

        # Bold/Italic روی پیام‌های خودتان
        if _is_owner(msg, st) and (st.bold_on or st.italic_on):
            if text.startswith("/") or text.startswith("اسپم ") or text.startswith("رگباری "):
                return
            styled = _apply_style(st, text)
            if styled != text:
                try:
                    await msg.edit_text(styled)
                except Exception as e:
                    logger.warning("edit_text style: %s", e)

    return dp


async def _clock_loop(bot_user_id: int, client: Client) -> None:
    while True:
        try:
            st = _state(bot_user_id)
            if st.clock_on and st.name_format:
                now = datetime.now(TEHRAN).strftime("%H:%M")
                new_name = re.sub(r"time", now, st.name_format, flags=re.IGNORECASE)
                try:
                    await client.edit_name(new_name)
                except Exception as e:
                    logger.warning("clock edit_name: %s", e)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.exception("clock loop: %s", e)
        await asyncio.sleep(NAME_INTERVAL)


def _start_clock(bot_user_id: int, client: Client) -> None:
    old = _clock_tasks.pop(bot_user_id, None)
    if old:
        old.cancel()
    _clock_tasks[bot_user_id] = asyncio.create_task(_clock_loop(bot_user_id, client))


async def start_session_client(
    bot_user_id: int,
    session_file: str,
    account_id: Optional[int] = None,
) -> None:
    path = Path(session_file)
    if not path.exists() or path.stat().st_size == 0:
        print(f"SESSION FILE MISSING: {path}")
        return

    st = _state(bot_user_id)
    if account_id:
        st.account_id = int(account_id)

    dp = _build_dispatcher(bot_user_id)
    client = Client(dp, session_file=path)
    _clients[bot_user_id] = client
    print(f"SESSION START {path}")
    logger.info("SESSION START file=%s account_id=%s", path, account_id)
    await client.start()


def spawn_session(
    bot_user_id: int,
    session_file: str,
    account_id: Optional[int] = None,
) -> None:
    old = _tasks.get(bot_user_id)
    if old and not old.done():
        old.cancel()
        print(f"cancelled old session task {bot_user_id}")
    _tasks[bot_user_id] = asyncio.create_task(
        start_session_client(bot_user_id, session_file, account_id)
    )


async def start_all_sessions() -> None:
    rows = list_active_sessions()
    print(f"DB active sessions={len(rows)}")
    for row in rows:
        print("DB row:", row.get("session_file"), "account_id=", row.get("account_id"))
        spawn_session(
            int(row["bot_user_id"]),
            row["session_file"],
            row.get("account_id"),
        )