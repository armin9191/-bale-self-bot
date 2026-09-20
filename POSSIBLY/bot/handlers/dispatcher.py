"""
Central message / callback dispatcher for POSSIBLY.
Uses only real python-bale-bot 2.5.0 APIs.
"""
from __future__ import annotations

import logging
import time
from datetime import date
from typing import Optional

from bale import Bot, Message, CallbackQuery

from config import settings
from bot.messages import info, error, success
from bot.permissions import is_special_admin, live_role, Role
from bot.keyboards import private_menu, ttt_keyboard
from database.repositories import (
    upsert_user,
    upsert_member,
    increment_stat,
    get_today_totals,
    get_top_users,
    count_learned,
    set_learned,
    delete_learned,
    list_learned_triggers,
    get_learned_response,
    log_moderation,
    create_whisper,
    get_whisper,
    mark_whisper_viewed,
    list_group_members_seen,
)
from bot.games.tic_tac_toe import TicTacToe
from bot.handlers.backup import create_backup

log = logging.getLogger("POSSIBLY.dispatcher")

# In-memory rate-limit & active TTT games (group_id -> TicTacToe)
_rate: dict[int, float] = {}
TTT: dict[int, TicTacToe] = {}
_backup_last: float = 0.0


def _uid(message: Message) -> Optional[int]:
    author = getattr(message, "author", None) or getattr(message, "from_user", None)
    if author is None:
        return None
    uid = getattr(author, "id", None)
    return int(uid) if uid is not None else None


def _text(message: Message) -> str:
    return (getattr(message, "content", None) or getattr(message, "text", None) or "").strip()


def _gid(message: Message) -> int:
    chat = getattr(message, "chat", None)
    if chat is not None and getattr(chat, "id", None) is not None:
        return int(chat.id)
    return int(getattr(message, "chat_id", 0) or 0)


def _rate_ok(user_id: int) -> bool:
    now = time.monotonic()
    last = _rate.get(user_id, 0.0)
    if now - last < settings.RATE_LIMIT_SECONDS:
        return False
    _rate[user_id] = now
    return True


async def _record_stats(message: Message, gid: int, user: int) -> None:
    author = getattr(message, "author", None) or getattr(message, "from_user", None)
    username = getattr(author, "username", None) if author else None
    display = (
        getattr(author, "first_name", None)
        or getattr(author, "name", None)
        or str(user)
    ) if author else str(user)
    await upsert_user(user, username, display)
    await upsert_member(gid, user, "member")
    kind = "other"
    if getattr(message, "animation", None) is not None:
        kind = "gifs"
    elif getattr(message, "voice", None) is not None:
        kind = "voice"
    elif getattr(message, "photos", None) or getattr(message, "photo", None):
        kind = "photos"
    elif getattr(message, "video", None) is not None:
        kind = "videos"
    today = date.today()
    await increment_stat(gid, user, "messages", today)
    if kind != "other":
        await increment_stat(gid, user, kind, today)
    else:
        await increment_stat(gid, user, "other", today)


async def _handle_learning(message: Message, gid: int, user: int, t: str) -> bool:
    if t.startswith("یاد بگیر"):
        if not is_special_admin(user):
            await message.reply(error("فقط Admin یا Owner مجاز است."))
            return True
        raw = t[len("یاد بگیر"):].strip()
        parts = raw.split(maxsplit=1)
        if len(parts) != 2:
            await message.reply(error("فرمت: یاد بگیر trigger response"))
            return True
        trigger, response = parts[0].strip(), parts[1].strip()
        if not trigger or not response:
            await message.reply(error("trigger و response نباید خالی باشند."))
            return True
        n = await count_learned(gid)
        existing = await get_learned_response(gid, trigger)
        if n >= settings.MAX_LEARNED_WORDS and existing is None:
            await message.reply(error("سقف ۳۰۰ یادگیری پر شده است."))
            return True
        await set_learned(gid, trigger, response, user)
        await message.reply(success(f"«{trigger}» یاد گرفته شد."))
        return True

    if t.startswith("فراموش کن"):
        if not is_special_admin(user):
            await message.reply(error("فقط Admin یا Owner مجاز است."))
            return True
        trigger = t[len("فراموش کن"):].strip()
        ok = await delete_learned(gid, trigger)
        await message.reply(success("حذف شد.") if ok else error("پیدا نشد."))
        return True

    if t in ("لیست یادگیری", "لیست یادگیری‌ها"):
        if not is_special_admin(user):
            await message.reply(error("فقط Admin یا Owner مجاز است."))
            return True
        triggers = await list_learned_triggers(gid)
        body = "\n".join(f"{i}. {tr}" for i, tr in enumerate(triggers, 1)) if triggers else "هنوز موردی ثبت نشده است."
        await message.reply(info(f"🧠 یادگیری‌ها\n\n{body}"))
        return True

    if not t.startswith("/"):
        resp = await get_learned_response(gid, t)
        if resp is not None:
            await message.reply(info(resp))
            return True
    return False


async def _handle_moderation(message: Message, gid: int, user: int, t: str) -> bool:
    if not (t.startswith("/ban") or t.startswith("/unban") or t.startswith("/kick")):
        return False
    if not is_special_admin(user):
        await message.reply(error("دسترسی ندارید."))
        return True

    target: Optional[int] = None
    reply = getattr(message, "reply_to_message", None)
    if reply is not None:
        ra = getattr(reply, "author", None) or getattr(reply, "from_user", None)
        if ra is not None and getattr(ra, "id", None) is not None:
            target = int(ra.id)
    if target is None:
        parts = t.split()
        if len(parts) > 1:
            try:
                target = int(parts[1])
            except ValueError:
                pass
    if target is None:
        await message.reply(error("هدف را با User ID یا Reply مشخص کن."))
        return True
    if target in (settings.OWNER_ID, settings.POSSIBLY_ADMIN_ID):
        await message.reply(error("این کاربر محافظت شده است."))
        return True

    chat = getattr(message, "chat", None)
    if chat is None:
        await message.reply(error("چت در دسترس نیست."))
        return True

    try:
        if t.startswith("/ban"):
            await chat.ban_chat_member(target)
            action = "ban"
        elif t.startswith("/unban"):
            await chat.unban_chat_member(target)
            action = "unban"
        else:
            # kick = ban then unban (Bale has no pure kick)
            await chat.ban_chat_member(target)
            try:
                await chat.unban_chat_member(target)
            except Exception:
                pass
            action = "kick"
        await log_moderation(gid, user, target, action)
        await message.reply(success(f"عملیات {action} برای {target} انجام شد."))
    except Exception as e:
        log.warning("moderation failed: %s", e)
        await message.reply(error("عملیات انجام نشد. دسترسی Admin ربات و محدودیت API را بررسی کنید."))
    return True


async def _show_stats(message: Message, gid: int) -> None:
    today = date.today()
    totals = await get_today_totals(gid, today)
    top = await get_top_users(gid, today, 3)
    lines = [
        "📊 آمار امروز",
        f"💬 پیام‌ها: {totals.get('messages', 0)}",
        f"🎞 GIF: {totals.get('gifs', 0)}",
        f"🎤 Voice: {totals.get('voice', 0)}",
        f"🖼 عکس: {totals.get('photos', 0)}",
        f"🎬 ویدیو: {totals.get('videos', 0)}",
        "",
        "🏆 فعال‌ترین اعضا:",
    ]
    medals = ["🥇", "🥈", "🥉"]
    for i, r in enumerate(top):
        name = f"@{r['username']}" if r.get("username") else (r.get("display_name") or str(r.get("user_id")))
        lines.append(f"{medals[i]} {name} — {r['messages']} پیام")
    if not top:
        lines.append("هنوز داده‌ای ثبت نشده.")
    await message.reply(info("\n".join(lines)))


async def _private_menu(message: Message, user: int) -> None:
    role = Role.MEMBER
    if is_special_admin(user):
        role = Role.OWNER if user == settings.OWNER_ID else Role.ADMIN
    else:
        try:
            bot = getattr(getattr(message, "chat", None), "bot", None)
            if bot:
                role = await live_role(bot, user)
        except Exception:
            pass
    await message.reply(
        info(f"منوی خصوصی POSSIBLY\n\nسطح دسترسی: {role.value}"),
        components=private_menu(
            admin=role in (Role.ADMIN, Role.OWNER),
            owner=role == Role.OWNER,
        ),
    )


async def on_message(message: Message) -> None:
    user = _uid(message)
    if user is None:
        return
    t = _text(message)
    gid = _gid(message)

    chat = getattr(message, "chat", None)
    chat_type = str(getattr(chat, "type", "") or "").lower()
    is_private = "private" in chat_type or gid == user

    if is_private:
        if t in ("/start", "start", "menu", "منو", ""):
            return await _private_menu(message, user)
        if t == "بکاپ" and user == settings.POSSIBLY_ADMIN_ID:
            global _backup_last
            now = time.monotonic()
            if now - _backup_last < settings.BACKUP_COOLDOWN_SECONDS:
                return await message.reply(error("لطفاً چند دقیقه صبر کنید."))
            _backup_last = now
            path = await create_backup()
            if path:
                try:
                    # Prefer document send if available
                    if hasattr(message, "reply_document"):
                        await message.reply_document(path, caption="POSSIBLY PostgreSQL backup")
                    else:
                        await message.reply(success(f"بکاپ ساخته شد: {path}"))
                except Exception as e:
                    log.warning("send backup failed: %s", e)
                    await message.reply(error("ارسال فایل بکاپ ناموفق بود."))
            else:
                await message.reply(error("ساخت بکاپ انجام نشد (pg_dump یا دسترسی دیتابیس)."))
            return
        return

    # Group restriction
    if gid != settings.ALLOWED_GROUP_ID:
        return await message.reply(info("این ربات فقط برای گروه مجاز فعال است."))

    if not _rate_ok(user):
        return

    try:
        await _record_stats(message, gid, user)
    except Exception:
        log.exception("stats failed")

    if await _handle_moderation(message, gid, user, t):
        return

    if t in ("امار", "آمار"):
        return await _show_stats(message, gid)

    if t.startswith("اکو"):
        payload = t[len("اکو"):].strip()
        if not payload:
            return await message.reply(error("بعد از اکو متن بنویس."))
        try:
            await message.delete()
        except Exception:
            pass
        return await message.chat.send(info(payload))

    # Whisper: reply + "نجوا متن"
    if t.startswith("نجوا") and getattr(message, "reply_to_message", None):
        reply = message.reply_to_message
        ra = getattr(reply, "author", None) or getattr(reply, "from_user", None)
        if ra is None or getattr(ra, "id", None) is None:
            return await message.reply(error("گیرنده مشخص نیست."))
        receiver = int(ra.id)
        content = t[len("نجوا"):].strip()
        if not content:
            return await message.reply(error("متن نجوا را بنویس."))
        try:
            wid = await create_whisper(gid, user, receiver, content, settings.WHISPER_TTL_SECONDS)
            try:
                await message.delete()
            except Exception:
                pass
            # Safe fallback: do not show content in group
            from bale import InlineKeyboardMarkup, InlineKeyboardButton
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("👁 مشاهده نجوا", callback_data=f"whisper:{wid}"), row=1)
            await message.chat.send(
                info(f"نجوا برای کاربر {receiver} ثبت شد.\nفقط گیرنده می‌تواند آن را ببیند."),
                components=kb,
            )
        except Exception as e:
            log.warning("whisper failed: %s", e)
            await message.reply(error("ثبت نجوا ناموفق بود."))
        return

    # Tic-Tac-Toe start
    if t == "دوز":
        # Simple challenge: first player starts, second joins via callback later
        game = TicTacToe.new(user, 0)  # o = 0 means waiting
        TTT[gid] = game
        await message.reply(
            info("🎮 دوز\n\nنفر اول ثبت شد. نفر دوم روی یک خانه کلیک کند تا بازی شروع شود."),
            components=ttt_keyboard(game.board),
        )
        return

    await _handle_learning(message, gid, user, t)


async def on_callback(callback: CallbackQuery) -> None:
    data = (callback.data or "").strip()
    user = int(callback.from_user.id) if getattr(callback, "from_user", None) else None
    msg = callback.message
    if user is None or msg is None:
        return

    if data == "about":
        return await msg.reply(info("POSSIBLY\nGroup Management + Fun + Games\nفقط برای @possibly"))

    if data == "games":
        return await msg.reply(info("🎮 بازی‌ها\n\n• دوز — در گروه بنویس «دوز»\n• مافیا و جرأت‌حقیقت در نسخه‌های بعدی کامل‌تر می‌شوند."))

    if data == "group_stats":
        return await _show_stats(msg, settings.ALLOWED_GROUP_ID)

    if data == "members":
        if not is_special_admin(user):
            return await msg.reply(error("دسترسی ندارید."))
        members = await list_group_members_seen(settings.ALLOWED_GROUP_ID, 40)
        if not members:
            return await msg.reply(info("هنوز عضوی از طریق ربات ثبت نشده.\n(Bale API لیست کامل اعضا ندارد؛ فقط کاربران مشاهده‌شده ذخیره می‌شوند.)"))
        lines = [f"• {m.get('display_name') or m['user_id']} (@{m.get('username') or '—'}) — {m.get('role')}" for m in members]
        return await msg.reply(info("👥 اعضای ثبت‌شده\n\n" + "\n".join(lines)))

    if data == "learning":
        if not is_special_admin(user):
            return await msg.reply(error("دسترسی ندارید."))
        triggers = await list_learned_triggers(settings.ALLOWED_GROUP_ID)
        body = "\n".join(f"{i}. {tr}" for i, tr in enumerate(triggers, 1)) if triggers else "خالی"
        return await msg.reply(info(f"🧠 یادگیری‌ها ({len(triggers)}/{settings.MAX_LEARNED_WORDS})\n\n{body}"))

    if data.startswith("whisper:"):
        try:
            wid = int(data.split(":")[1])
        except (IndexError, ValueError):
            return await msg.reply(error("نجوا نامعتبر."))
        w = await get_whisper(wid)
        if not w:
            return await msg.reply(error("نجوا پیدا نشد یا منقضی شده."))
        if int(w["receiver_id"]) != user and int(w["sender_id"]) != user:
            return await msg.reply(error("این نجوا برای شما نیست."))
        from datetime import datetime, timezone
        exp = w.get("expires_at")
        if exp and exp < datetime.now(timezone.utc):
            return await msg.reply(error("نجوا منقضی شده است."))
        await mark_whisper_viewed(wid)
        # Send privately if possible, else reply (content only to allowed user)
        text = w["encrypted_or_private_content"]
        try:
            await callback.from_user.send(info(f"نجوا:\n\n{text}"))
        except Exception:
            await msg.reply(info(f"نجوا:\n\n{text}"))
        return

    if data.startswith("ttt:"):
        try:
            pos = int(data.split(":")[1])
        except (IndexError, ValueError):
            return
        gid = int(getattr(msg, "chat_id", 0) or getattr(getattr(msg, "chat", None), "id", 0) or 0)
        game = TTT.get(gid)
        if not game:
            return await msg.reply(error("بازی منقضی شده است."))
        # Join as second player if needed
        if game.o == 0 and user != game.x:
            game.o = user
        if user not in (game.x, game.o):
            return await msg.reply(error("این بازی برای شما نیست."))
        expected = game.x if game.turn == "X" else game.o
        if user != expected:
            return await msg.reply(error("نوبت شما نیست."))
        if not game.move(pos):
            return await msg.reply(error("حرکت نامعتبر."))
        winner = game.winner()
        board_str = "\n".join(
            " | ".join(game.board[r * 3 + c] or "·" for c in range(3)) for r in range(3)
        )
        if winner:
            result = "مساوی" if winner == "draw" else f"برنده: {winner}"
            TTT.pop(gid, None)
            return await msg.edit(info(f"🎮 دوز\n\n{board_str}\n\nنتیجه: {result}"))
        return await msg.edit(
            info(f"🎮 دوز\n\n{board_str}\n\nنوبت: {game.turn}"),
            components=ttt_keyboard(game.board),
        )


def register_handlers(bot: Bot) -> None:
    @bot.listen("on_message")
    async def _message(message: Message):
        try:
            await on_message(message)
        except Exception:
            log.exception("on_message error")

    @bot.listen("on_callback")
    async def _callback(callback: CallbackQuery):
        try:
            await on_callback(callback)
        except Exception:
            log.exception("on_callback error")
