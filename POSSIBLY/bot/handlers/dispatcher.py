"""Central dispatcher — Persian commands, group + private."""
from __future__ import annotations

import logging
import time
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

from bale import Bot, Message, CallbackQuery, InputFile

from config import settings
from bot.messages import info, error, success, help_text
from bot.permissions import is_special_admin, is_owner, live_role, Role
from bot.keyboards import (
    private_menu, ttt_keyboard, whisper_keyboard, whisper_open_keyboard,
    mafia_lobby_keyboard, tod_lobby_keyboard, tod_choice_keyboard,
)
from database.repositories import (
    upsert_user, upsert_member, increment_stat,
    get_today_totals, get_top_users, get_user_stats,
    count_learned, set_learned, delete_learned, list_learned_triggers, get_learned_response,
    log_moderation, recent_logs, create_whisper, get_whisper, mark_whisper_viewed,
    list_group_members_seen, save_game, load_active_game,
    get_group_settings, set_group_rules, set_group_welcome, set_group_farewell,
)
from bot.games.tic_tac_toe import TicTacToe
from bot.games.mafia import new_state as mafia_new, assign_roles, check_win, Phase as MafiaPhase
from bot.games.truth_dare import new_state as tod_new, pick as tod_pick
from bot.handlers.backup import create_backup
from bot.handlers.gif import process_gif
from bot.bale_api import answer_callback_query

log = logging.getLogger("POSSIBLY.dispatcher")

_rate: dict[int, float] = {}
_backup_last: float = 0.0
TTT: dict[int, TicTacToe] = {}
MAFIA: dict[int, dict] = {}
TOD: dict[int, dict] = {}
_bot: Optional[Bot] = None


def _get_bot(obj=None) -> Optional[Bot]:
    """Resolve Bot instance from message/file or module registry."""
    global _bot
    if obj is not None:
        # BaleObject.bot property / get_bot()
        b = getattr(obj, "bot", None)
        if b is not None:
            return b
        getter = getattr(obj, "get_bot", None)
        if callable(getter):
            try:
                return getter()
            except Exception:
                pass
        chat = getattr(obj, "chat", None)
        if chat is not None:
            b = getattr(chat, "bot", None)
            if b is not None:
                return b
            getter = getattr(chat, "get_bot", None)
            if callable(getter):
                try:
                    return getter()
                except Exception:
                    pass
    return _bot


def _uid(m: Message) -> Optional[int]:
    a = getattr(m, "author", None) or getattr(m, "from_user", None)
    if a is None:
        return None
    i = getattr(a, "id", None)
    return int(i) if i is not None else None


def _text(m: Message) -> str:
    return (getattr(m, "content", None) or getattr(m, "text", None) or "").strip()


def _gid(m: Message) -> int:
    chat = getattr(m, "chat", None)
    if chat is not None and getattr(chat, "id", None) is not None:
        return int(chat.id)
    return int(getattr(m, "chat_id", 0) or 0)


def _is_private(m: Message, gid: int, user: int) -> bool:
    chat = getattr(m, "chat", None)
    t = str(getattr(chat, "type", "") or "").lower()
    return "private" in t or gid == user


def _rate_ok(uid: int) -> bool:
    now = time.monotonic()
    if now - _rate.get(uid, 0) < settings.RATE_LIMIT_SECONDS:
        return False
    _rate[uid] = now
    return True


def _target_from_message(m: Message, t: str) -> Optional[int]:
    reply = getattr(m, "reply_to_message", None)
    if reply is not None:
        ra = getattr(reply, "author", None) or getattr(reply, "from_user", None)
        if ra is not None and getattr(ra, "id", None) is not None:
            return int(ra.id)
    parts = t.split()
    if len(parts) >= 2:
        try:
            return int(parts[1])
        except ValueError:
            pass
    return None


async def _record_stats(m: Message, gid: int, user: int) -> None:
    a = getattr(m, "author", None) or getattr(m, "from_user", None)
    un = getattr(a, "username", None) if a else None
    dn = (getattr(a, "first_name", None) or getattr(a, "name", None) or str(user)) if a else str(user)
    await upsert_user(user, un, dn)
    await upsert_member(gid, user, "member")
    kind = "other"
    if getattr(m, "animation", None) is not None:
        kind = "gifs"
    elif getattr(m, "voice", None) is not None:
        kind = "voice"
    elif getattr(m, "photos", None) or getattr(m, "photo", None):
        kind = "photos"
    elif getattr(m, "video", None) is not None:
        kind = "videos"
    today = date.today()
    await increment_stat(gid, user, "messages", today)
    await increment_stat(gid, user, kind, today)


async def _show_stats(m: Message, gid: int) -> None:
    today = date.today()
    totals = await get_today_totals(gid, today)
    top = await get_top_users(gid, today, 5)
    lines = [
        "📊 آمار امروز",
        f"💬 پیام‌ها: {totals.get('messages', 0)}",
        f"🎞 GIF: {totals.get('gifs', 0)}",
        f"🎤 Voice: {totals.get('voice', 0)}",
        f"🖼 عکس: {totals.get('photos', 0)}",
        f"🎬 ویدیو: {totals.get('videos', 0)}",
        "",
        "🏆 فعال‌ترین‌ها:",
    ]
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    for i, r in enumerate(top):
        name = f"@{r['username']}" if r.get("username") else (r.get("display_name") or str(r.get("user_id")))
        lines.append(f"{medals[i]} {name} — {r['messages']}")
    if not top:
        lines.append("هنوز داده‌ای نیست.")
    await m.reply(info("\n".join(lines)))


async def _moderation(m: Message, gid: int, user: int, t: str) -> bool:
    low = t.strip()
    action = None
    if low.startswith("بن") or low.startswith("ban"):
        action = "ban"
    elif low.startswith("کیک") or low.startswith("kick"):
        action = "kick"
    elif low.startswith("آنبن") or low.startswith("انبن") or low.startswith("unban"):
        action = "unban"
    if action is None:
        return False
    if not is_special_admin(user):
        await m.reply(error("فقط Admin/Owner."))
        return True
    target = _target_from_message(m, t)
    if target is None:
        await m.reply(error("هدف را با ریپلای یا آیدی عددی مشخص کن.\nمثال: بن 123456"))
        return True
    if target in (settings.OWNER_ID, settings.POSSIBLY_ADMIN_ID):
        await m.reply(error("این کاربر محافظت شده است."))
        return True
    chat = getattr(m, "chat", None)
    if chat is None:
        await m.reply(error("چت در دسترس نیست."))
        return True
    try:
        if action == "ban":
            await chat.ban_chat_member(target)
        elif action == "unban":
            await chat.unban_chat_member(target)
        else:
            await chat.ban_chat_member(target)
            try:
                await chat.unban_chat_member(target)
            except Exception:
                pass
        await log_moderation(gid, user, target, action)
        await m.reply(success(f"{action} برای {target} انجام شد."))
    except Exception as e:
        log.warning("moderation: %s", e)
        await m.reply(error("عملیات ناموفق. دسترسی Admin ربات را بررسی کن."))
    return True


async def _learning(m: Message, gid: int, user: int, t: str) -> bool:
    if t.startswith("یاد بگیر"):
        if not is_special_admin(user):
            await m.reply(error("فقط Admin/Owner."))
            return True
        raw = t[len("یاد بگیر"):].strip().split(maxsplit=1)
        if len(raw) != 2:
            await m.reply(error("فرمت: یاد بگیر trigger پاسخ"))
            return True
        trigger, response = raw[0].strip(), raw[1].strip()
        n = await count_learned(gid)
        if n >= settings.MAX_LEARNED_WORDS and await get_learned_response(gid, trigger) is None:
            await m.reply(error("سقف ۳۰۰ پر است."))
            return True
        await set_learned(gid, trigger, response, user)
        await m.reply(success(f"«{trigger}» یاد گرفته شد."))
        return True
    if t.startswith("فراموش کن"):
        if not is_special_admin(user):
            await m.reply(error("فقط Admin/Owner."))
            return True
        trigger = t[len("فراموش کن"):].strip()
        ok = await delete_learned(gid, trigger)
        await m.reply(success("حذف شد.") if ok else error("پیدا نشد."))
        return True
    if t in ("لیست یادگیری", "لیست یادگیری‌ها"):
        if not is_special_admin(user):
            await m.reply(error("فقط Admin/Owner."))
            return True
        triggers = await list_learned_triggers(gid)
        body = "\n".join(f"{i}. {x}" for i, x in enumerate(triggers, 1)) or "خالی"
        await m.reply(info(f"🧠 یادگیری ({len(triggers)}/{settings.MAX_LEARNED_WORDS})\n\n{body}"))
        return True
    if not t.startswith("/") and not any(t.startswith(x) for x in ("بن", "کیک", "آنبن", "انبن", "اکو", "نجوا", "گیف", "دوز", "مافیا", "جرعت", "آمار", "امار")):
        resp = await get_learned_response(gid, t)
        if resp is not None:
            await m.reply(info(resp))
            return True
    return False


def _norm_cmd(t: str) -> str:
    """Normalize Persian/Arabic letters and spaces for command matching."""
    if not t:
        return ""
    # Arabic kaf/yeh → Persian
    t = t.replace("\u0643", "\u06a9").replace("\u064a", "\u06cc")
    # zero-width / special spaces
    for ch in ("\u200c", "\u200f", "\u200e", "\xa0", "\u200b"):
        t = t.replace(ch, " ")
    return " ".join(t.split())


async def _echo(m: Message, t: str) -> bool:
    nt = _norm_cmd(t)
    # accept: اکو / اکو: / echo
    if not (nt.startswith("اکو") or nt.lower().startswith("echo")):
        return False
    if nt.lower().startswith("echo"):
        payload = nt[4:].strip().lstrip(":").strip()
    else:
        payload = nt[len("اکو"):].strip().lstrip(":").strip()
    if not payload:
        await m.reply(error("بعد از اکو متن بنویس.\nمثال: اکو سلام"))
        return True
    # Send FIRST (so user always sees the echo even if delete fails)
    sent = False
    try:
        await m.reply(info(payload))
        sent = True
    except Exception as e1:
        log.warning("echo reply failed: %s", e1)
        try:
            chat = getattr(m, "chat", None)
            if chat is not None and hasattr(chat, "send"):
                await chat.send(info(payload))
                sent = True
        except Exception as e2:
            log.warning("echo chat.send failed: %s", e2)
            bot = _get_bot(m)
            if bot is not None:
                try:
                    await bot.send_message(_gid(m), info(payload))
                    sent = True
                except Exception as e3:
                    log.warning("echo bot.send_message failed: %s", e3)
    if not sent:
        await m.reply(error("ارسال اکو ناموفق بود."))
        return True
    # Then try delete original (needs can_delete_messages)
    try:
        await m.delete()
    except Exception as e:
        log.info("echo delete skipped: %s", e)
    return True


async def _whisper(m: Message, gid: int, user: int, t: str) -> bool:
    if not t.startswith("نجوا"):
        return False
    reply = getattr(m, "reply_to_message", None)
    if reply is None:
        await m.reply(error("روی پیام شخص ریپلای کن و بنویس: نجوا متن"))
        return True
    ra = getattr(reply, "author", None) or getattr(reply, "from_user", None)
    if ra is None or getattr(ra, "id", None) is None:
        await m.reply(error("گیرنده مشخص نیست."))
        return True
    receiver = int(ra.id)
    content = t[len("نجوا"):].strip()
    if not content:
        await m.reply(error("متن نجوا را بنویس."))
        return True
    try:
        wid = await create_whisper(gid, user, receiver, content, settings.WHISPER_TTL_SECONDS)
        try:
            await m.delete()
        except Exception:
            pass
        await m.chat.send(
            info(f"نجوا برای {receiver} ثبت شد.\nفقط گیرنده می‌تواند ببیند."),
            components=whisper_keyboard(wid),
        )
    except Exception as e:
        log.warning("whisper: %s", e)
        await m.reply(error("ثبت نجوا ناموفق."))
    return True


async def _gif(m: Message, t: str) -> bool:
    if not t.startswith("گیف"):
        return False
    caption = t[len("گیف"):].strip()
    if not caption:
        await m.reply(error("فرمت: ریپلای به گیف + گیف متن"))
        return True
    reply = getattr(m, "reply_to_message", None)
    if reply is None:
        await m.reply(error("روی یک گیف/انیمیشن ریپلای کن."))
        return True
    anim = getattr(reply, "animation", None) or getattr(reply, "document", None) or getattr(reply, "video", None)
    if anim is None:
        await m.reply(error("پیام ریپلای‌شده گیف/فایل نیست."))
        return True
    file_id = getattr(anim, "file_id", None) or getattr(anim, "id", None)
    if not file_id:
        await m.reply(error("file_id پیدا نشد."))
        return True
    try:
        raw = None
        # 1) BaseFile.get() if available
        if hasattr(anim, "get") and callable(anim.get):
            try:
                raw = await anim.get()
            except Exception as e:
                log.warning("anim.get failed: %s", e)
        # 2) Message/Chat get_bot + Bot.get_file
        if not raw:
            bot = _get_bot(m) or _get_bot(anim) or _get_bot(reply)
            if bot is None:
                await m.reply(error("بات در دسترس نیست (bot instance)."))
                return True
            raw = await bot.get_file(str(file_id))
        if not raw:
            await m.reply(error("دانلود فایل ناموفق."))
            return True
        if not isinstance(raw, (bytes, bytearray)):
            # some wrappers return file-like
            raw = bytes(raw) if hasattr(raw, "__iter__") else None
            if not raw:
                await m.reply(error("محتوای فایل نامعتبر."))
                return True
        # log magic for debug
        head = bytes(raw[:16]) if raw else b""
        log.info("downloaded head=%r len=%s", head, len(raw) if raw else 0)
        out = process_gif(bytes(raw), caption)
        if not out:
            await m.reply(error("پردازش گیف ناموفق."))
            return True
        # IMPORTANT: InputFile needs file BYTES, not a path string
        media = InputFile(out, file_name="possibly.gif")
        chat_id = getattr(getattr(m, "chat", None), "id", None) or _gid(m)
        bot = _get_bot(m)
        sent = False
        try:
            if hasattr(m, "reply_animation"):
                await m.reply_animation(media)
                sent = True
        except Exception as e0:
            log.warning("reply_animation failed: %s", e0)
        if not sent:
            try:
                chat = getattr(m, "chat", None)
                if chat is not None and hasattr(chat, "send_animation"):
                    await chat.send_animation(InputFile(out, file_name="possibly.gif"))
                    sent = True
            except Exception as e1:
                log.warning("chat.send_animation failed: %s", e1)
        if not sent and bot is not None:
            try:
                await bot.send_animation(chat_id, InputFile(out, file_name="possibly.gif"))
                sent = True
            except Exception as e3:
                log.warning("bot.send_animation failed: %s", e3)
        if not sent:
            try:
                if hasattr(m, "reply_document"):
                    await m.reply_document(InputFile(out, file_name="possibly.gif"))
                    sent = True
                elif bot is not None:
                    await bot.send_document(chat_id, InputFile(out, file_name="possibly.gif"))
                    sent = True
            except Exception as e2:
                log.warning("send_document failed: %s", e2)
        if not sent:
            await m.reply(error("ارسال گیف ناموفق بود."))
    except ValueError as e:
        await m.reply(error(str(e)))
    except Exception as e:
        log.exception("gif")
        await m.reply(error(f"خطا در پردازش گیف: {e}"))
    return True


async def _do_backup(m: Message, user: int) -> None:
    global _backup_last
    if not is_owner(user) and user != settings.POSSIBLY_ADMIN_ID:
        await m.reply(error("فقط Owner."))
        return
    now = time.monotonic()
    if now - _backup_last < settings.BACKUP_COOLDOWN_SECONDS:
        await m.reply(error("چند دقیقه صبر کن."))
        return
    _backup_last = now
    await m.reply(info("در حال ساخت بکاپ..."))
    path = await create_backup()
    if not path:
        await m.reply(error("ساخت بکاپ ناموفق بود."))
        return
    try:
        data = Path(path).read_bytes()
        if not data:
            await m.reply(error("فایل بکاپ خالی است."))
            return
        fname = Path(path).name
        media = InputFile(data, file_name=fname)
        chat_id = getattr(getattr(m, "chat", None), "id", None) or user
        bot = _get_bot(m)
        sent = False
        try:
            if hasattr(m, "reply_document"):
                await m.reply_document(media, caption="POSSIBLY DB Backup (SQL)")
                sent = True
        except Exception as e1:
            log.warning("reply_document backup: %s", e1)
        if not sent and bot is not None:
            try:
                await bot.send_document(chat_id, media, caption="POSSIBLY DB Backup (SQL)")
                sent = True
            except Exception as e2:
                log.warning("bot.send_document backup: %s", e2)
        if not sent:
            # last: try without caption
            try:
                if bot is not None:
                    await bot.send_document(chat_id, InputFile(data, file_name=fname))
                    sent = True
            except Exception as e3:
                log.warning("bot.send_document bare: %s", e3)
        if sent:
            await m.reply(success(f"بکاپ ارسال شد ({len(data)} بایت)."))
        else:
            await m.reply(error("ارسال فایل ناموفق. بکاپ ساخته شد ولی API بله فایل را نپذیرفت."))
    except Exception as e:
        log.exception("send backup")
        await m.reply(error(f"خطا در ارسال بکاپ: {e}"))
    try:
        Path(path).unlink(missing_ok=True)
    except Exception:
        pass


async def _private(m: Message, user: int, t: str) -> None:
    low = t.lower().strip()
    if low in ("راهنما", "help", "دستورات"):
        await m.reply(help_text())
        role = Role.OWNER if is_owner(user) else (Role.ADMIN if is_special_admin(user) else Role.MEMBER)
        await m.reply(info(f"منوی خصوصی\nسطح: {role.value}"), components=private_menu(role))
        return
    if low in ("", "/start", "start", "منو", "menu"):
        role = Role.OWNER if is_owner(user) else (Role.ADMIN if is_special_admin(user) else Role.MEMBER)
        await m.reply(info(f"منوی خصوصی\nسطح: {role.value}"), components=private_menu(role))
        return
    if low in ("بکاپ", "/backup", "backup") and (is_owner(user) or user == settings.POSSIBLY_ADMIN_ID):
        await _do_backup(m, user)
        return
    if low in ("آمار من", "امار من", "my stats"):
        st = await get_user_stats(user, settings.ALLOWED_GROUP_ID, date.today())
        await m.reply(info(
            f"📊 آمار امروز شما\n💬 {st.get('messages',0)}\n🎞 {st.get('gifs',0)}\n"
            f"🎤 {st.get('voice',0)}\n🖼 {st.get('photos',0)}\n🎬 {st.get('videos',0)}"
        ))
        return
    if low in ("پروفایل", "profile"):
        await m.reply(info(f"User ID: {user}\nگروه مجاز: {settings.ALLOWED_GROUP_USERNAME}"))
        return
    if low in ("آمار", "امار", "آمار گروه"):
        if is_special_admin(user):
            await _show_stats(m, settings.ALLOWED_GROUP_ID)
        else:
            await m.reply(error("آمار گروه فقط برای Admin."))
        return
    # allow admin moderation commands from private (they still need group context for ban)
    await m.reply(info("از منو استفاده کن یا «راهنما» را بفرست."))



def _format_template(tpl: str, user_name: str, gap_name: str) -> str:
    if not tpl:
        return ""
    out = tpl
    for key, val in (
        ("[User name]", user_name),
        ("[user name]", user_name),
        ("[Username]", user_name),
        ("[username]", user_name),
        ("[Gap name]", gap_name),
        ("[gap name]", gap_name),
        ("[Group name]", gap_name),
        ("[group name]", gap_name),
    ):
        out = out.replace(key, val)
    return out


async def _rules_and_greetings(m: Message, gid: int, user: int, t: str) -> bool:
    """قوانین / خوشامد / بدرقه."""
    nt = _norm_cmd(t)

    if nt in ("قوانین", "قانون", "rules"):
        st = await get_group_settings(gid)
        rules = (st.get("rules_text") or "").strip()
        if not rules:
            await m.reply(info("هنوز قوانینی ثبت نشده است.\nادمین با «تنظیم قوانین ...» ثبت می‌کند."))
        else:
            await m.reply(info(f"📜 قوانین گروه\n\n{rules}"))
        return True

    if nt.startswith("تنظیم قوانین") or nt.startswith("ثبت قوانین"):
        if not is_special_admin(user):
            await m.reply(error("فقط Admin/Owner."))
            return True
        body = ""
        for pfx in ("تنظیم قوانین", "ثبت قوانین"):
            if pfx in t:
                body = t.split(pfx, 1)[-1].strip()
                break
        if not body:
            lines = t.strip().splitlines()
            if len(lines) >= 2:
                body = "\n".join(x.strip() for x in lines[1:] if x.strip())
        if not body:
            await m.reply(error("فرمت:\nتنظیم قوانین\nتبلیغ : بن\nفحش : بن"))
            return True
        await set_group_rules(gid, body, user)
        await m.reply(success("قوانین تنظیم شد !"))
        return True

    if nt.startswith("تنظیم خوشامد") or nt.startswith("تنظیم خوش آمد"):
        if not is_special_admin(user):
            await m.reply(error("فقط Admin/Owner."))
            return True
        body = ""
        for pfx in ("تنظیم خوشامد پازیبلی", "تنظیم خوشامد", "تنظیم خوش آمد"):
            if pfx in t:
                body = t.split(pfx, 1)[-1].strip()
                break
        if not body:
            lines = t.strip().splitlines()
            if len(lines) >= 2:
                body = "\n".join(x.strip() for x in lines[1:] if x.strip())
        if not body:
            await m.reply(error(
                "فرمت:\nتنظیم خوشامد سلام [User name] خوش اومدی به [Gap name]"
            ))
            return True
        await set_group_welcome(gid, body, user)
        await m.reply(success("خوشامد تنظیم شد"))
        return True

    if nt.startswith("تنظیم بدرقه"):
        if not is_special_admin(user):
            await m.reply(error("فقط Admin/Owner."))
            return True
        body = ""
        if "تنظیم بدرقه" in t:
            body = t.split("تنظیم بدرقه", 1)[-1].strip()
        if not body:
            lines = t.strip().splitlines()
            if len(lines) >= 2:
                body = "\n".join(x.strip() for x in lines[1:] if x.strip())
        if not body:
            await m.reply(error(
                "فرمت:\nتنظیم بدرقه خداحافظ [User name] امیدوارم برگردی به [Gap name]"
            ))
            return True
        await set_group_farewell(gid, body, user)
        await m.reply(success("بدرقه تنظیم شد"))
        return True

    return False


async def on_message(m: Message) -> None:
    user = _uid(m)
    if user is None:
        return
    t = _text(m)
    gid = _gid(m)

    if _is_private(m, gid, user):
        return await _private(m, user, t)

    if gid != settings.ALLOWED_GROUP_ID:
        return await m.reply(info("این ربات فقط برای گروه مجاز فعال است."))

    if not _rate_ok(user):
        return

    try:
        await _record_stats(m, gid, user)
    except Exception:
        log.exception("stats")

    if await _moderation(m, gid, user, t):
        return
    if t in ("آمار", "امار"):
        return await _show_stats(m, gid)
    if t in ("راهنما", "help", "دستورات"):
        return await m.reply(help_text())
    if await _rules_and_greetings(m, gid, user, t):
        return
    if await _echo(m, t):
        return
    if await _whisper(m, gid, user, t):
        return
    if await _gif(m, t):
        return

    # games
    if t == "دوز":
        TTT[gid] = TicTacToe.new(user, 0)
        return await m.reply(
            info("🎮 دوز\nنفر اول ثبت شد. نفر دوم روی خانه کلیک کند."),
            components=ttt_keyboard(TTT[gid].board),
        )
    if t in ("مافیا", "شروع مافیا"):
        MAFIA[gid] = mafia_new(user)
        return await m.reply(
            info("🕵️ مافیا — لابی\nحداقل ۴ نفر. سازنده شروع را بزند."),
            components=mafia_lobby_keyboard(),
        )
    # Mafia phase helpers (creator)
    if t.startswith("پایان شب") or t.startswith("روز مافیا"):
        st = MAFIA.get(gid)
        if not st or user != st.get("creator_id"):
            return await m.reply(error("فقط سازنده بازی می‌تواند فاز را عوض کند."))
        if st.get("phase") != MafiaPhase.NIGHT.value:
            return await m.reply(error("الان شب نیست."))
        st["phase"] = MafiaPhase.DAY.value
        alive_n = len(st.get("alive") or [])
        return await m.reply(info(
            f"☀️ روز {st.get('day', 1)}\nزنده: {alive_n}\n"
            "بحث کنید. سازنده با «رای گیری» رأی را شروع کند.\n"
            "یا «اعدام USER_ID» برای اعدام مستقیم."
        ))
    if t.startswith("رای گیری") or t.startswith("رأی گیری"):
        st = MAFIA.get(gid)
        if not st or user != st.get("creator_id"):
            return await m.reply(error("فقط سازنده."))
        st["phase"] = MafiaPhase.VOTING.value
        st["votes"] = {}
        return await m.reply(info(
            "🗳️ رأی‌گیری شروع شد.\nهر کس بنویسد: رای USER_ID\n"
            "سازنده در پایان «پایان رای» بزند."
        ))
    if t.startswith("رای ") or t.startswith("رأی "):
        st = MAFIA.get(gid)
        if not st or st.get("phase") != MafiaPhase.VOTING.value:
            return False
        if user not in (st.get("alive") or []):
            return await m.reply(error("شما زنده نیستید."))
        parts = t.split()
        try:
            target = int(parts[1])
        except Exception:
            return await m.reply(error("فرمت: رای USER_ID"))
        if target not in (st.get("alive") or []):
            return await m.reply(error("هدف زنده نیست."))
        st.setdefault("votes", {})[str(user)] = target
        return await m.reply(success(f"رأی شما ثبت شد → {target}"))
    if t.startswith("پایان رای") or t.startswith("پایان رأی"):
        st = MAFIA.get(gid)
        if not st or user != st.get("creator_id"):
            return await m.reply(error("فقط سازنده."))
        votes = st.get("votes") or {}
        if not votes:
            return await m.reply(error("رأیی ثبت نشده."))
        from collections import Counter
        cnt = Counter(votes.values())
        target, n = cnt.most_common(1)[0]
        alive = st.get("alive") or []
        if target in alive:
            alive = [p for p in alive if p != target]
            st["alive"] = alive
        st["votes"] = {}
        win = check_win(st)
        if win:
            st["phase"] = MafiaPhase.ENDED.value
            st["winner"] = win
            MAFIA.pop(gid, None)
            return await m.reply(info(f"☠️ اعدام: {target}\n🏆 برنده: {win}"))
        st["phase"] = MafiaPhase.NIGHT.value
        st["day"] = int(st.get("day") or 1) + 1
        return await m.reply(info(
            f"☠️ اعدام شد: {target} ({n} رأی)\nزنده: {len(st['alive'])}\n🌙 شب {st['day']}"
        ))
    if t.startswith("اعدام "):
        st = MAFIA.get(gid)
        if not st or user != st.get("creator_id"):
            return await m.reply(error("فقط سازنده."))
        try:
            target = int(t.split()[1])
        except Exception:
            return await m.reply(error("فرمت: اعدام USER_ID"))
        alive = st.get("alive") or []
        if target not in alive:
            return await m.reply(error("هدف زنده نیست."))
        st["alive"] = [p for p in alive if p != target]
        win = check_win(st)
        if win:
            st["phase"] = MafiaPhase.ENDED.value
            MAFIA.pop(gid, None)
            return await m.reply(info(f"☠️ اعدام: {target}\n🏆 برنده: {win}"))
        st["phase"] = MafiaPhase.NIGHT.value
        st["day"] = int(st.get("day") or 1) + 1
        return await m.reply(info(f"☠️ اعدام: {target}\nزنده: {len(st['alive'])}\n🌙 شب {st['day']}"))
    if t in ("جرعت حقیقت", "جرأت حقیقت", "شروع جرعت و حقیقت", "جرعت و حقیقت"):
        TOD[gid] = tod_new(user)
        return await m.reply(
            info("🎲 جرأت یا حقیقت — لابی"),
            components=tod_lobby_keyboard(),
        )

    await _learning(m, gid, user, t)


async def on_callback(cb: CallbackQuery) -> None:
    data = (cb.data or "").strip()
    user = int(cb.from_user.id) if getattr(cb, "from_user", None) else None
    msg = cb.message
    if user is None or msg is None:
        return
    gid = int(getattr(msg, "chat_id", 0) or getattr(getattr(msg, "chat", None), "id", 0) or 0)

    if data == "help":
        return await msg.reply(help_text())
    if data == "about":
        return await msg.reply(info("POSSIBLY\nGroup Management + Fun + Games\nفقط @possibly"))
    if data == "games":
        return await msg.reply(info("🎮 در گروه بنویس:\n• دوز\n• مافیا\n• جرعت حقیقت"))
    if data == "group_stats":
        return await _show_stats(msg, settings.ALLOWED_GROUP_ID)
    if data == "my_stats":
        st = await get_user_stats(user, settings.ALLOWED_GROUP_ID, date.today())
        return await msg.reply(info(f"📊 آمار شما\n💬 {st.get('messages',0)} پیام"))
    if data == "profile":
        return await msg.reply(info(f"ID: {user}"))
    if data == "members":
        if not is_special_admin(user):
            return await msg.reply(error("دسترسی ندارید."))
        members = await list_group_members_seen(settings.ALLOWED_GROUP_ID, 40)
        if not members:
            return await msg.reply(info("هنوز عضوی ثبت نشده.\n(API بله لیست کامل اعضا ندارد)"))
        lines = [f"• {x.get('display_name') or x['user_id']} (@{x.get('username') or '—'}) [{x.get('role')}]" for x in members]
        return await msg.reply(info("👥 اعضا\n\n" + "\n".join(lines)))
    if data == "learning":
        if not is_special_admin(user):
            return await msg.reply(error("دسترسی ندارید."))
        triggers = await list_learned_triggers(settings.ALLOWED_GROUP_ID)
        body = "\n".join(f"{i}. {x}" for i, x in enumerate(triggers, 1)) or "خالی"
        return await msg.reply(info(f"🧠 {body}"))
    if data == "logs":
        if not is_special_admin(user):
            return await msg.reply(error("دسترسی ندارید."))
        logs = await recent_logs(settings.ALLOWED_GROUP_ID, 12)
        if not logs:
            return await msg.reply(info("لاگی نیست."))
        lines = [f"• {r['action']} — {r.get('target_id')} توسط {r['actor_id']}" for r in logs]
        return await msg.reply(info("📜 لاگ\n\n" + "\n".join(lines)))
    if data == "do_backup":
        return await _do_backup(msg, user)

    # Whisper: private alert popup via answerCallbackQuery (only that user sees it)
    if data.startswith("whisper:") or data.startswith("whisper_ok:"):
        cb_id = getattr(cb, "id", None) or getattr(cb, "callback_id", None)
        try:
            wid = int(data.split(":")[1])
        except Exception:
            if cb_id:
                await answer_callback_query(cb_id, show_alert=False)
            return

        w = await get_whisper(wid)
        if not w:
            if cb_id:
                await answer_callback_query(cb_id, "نجوا دیگر در دسترس نیست.", show_alert=True)
            return

        allowed = {int(w["receiver_id"]), int(w["sender_id"])}
        if user not in allowed:
            # private alert only for the clicker — nothing in the group chat
            if cb_id:
                await answer_callback_query(cb_id, "این نجوا برای شما نیست.", show_alert=True)
            return

        exp = w.get("expires_at")
        if exp is not None:
            try:
                exp_aware = exp if getattr(exp, "tzinfo", None) else exp.replace(tzinfo=timezone.utc)
                if exp_aware < datetime.now(timezone.utc):
                    if cb_id:
                        await answer_callback_query(cb_id, "این نجوا منقضی شده است.", show_alert=True)
                    return
            except Exception:
                pass

        if data.startswith("whisper_ok:"):
            await mark_whisper_viewed(wid)
            if cb_id:
                await answer_callback_query(cb_id, "بسته شد.", show_alert=False)
            return

        body = (w.get("encrypted_or_private_content") or "").strip()
        # Bale alert text limit ~200 chars
        if len(body) > 180:
            shown = body[:177] + "…"
        else:
            shown = body
        alert_text = f"🔒 نجوا\n\n{shown}"
        ok = False
        if cb_id:
            ok = await answer_callback_query(cb_id, alert_text, show_alert=True)
        if ok:
            await mark_whisper_viewed(wid)
        else:
            # API failed — still never post content to group
            if cb_id:
                await answer_callback_query(cb_id, "نمایش نجوا ناموفق بود.", show_alert=True)
        return

    # TTT
    if data.startswith("ttt:"):
        try:
            pos = int(data.split(":")[1])
        except Exception:
            return
        game = TTT.get(gid)
        if not game:
            return await msg.reply(error("بازی منقضی."))
        if game.o == 0 and user != game.x:
            game.o = user
        if user not in (game.x, game.o):
            return await msg.reply(error("بازی شما نیست."))
        expected = game.x if game.turn == "X" else game.o
        if user != expected:
            return await msg.reply(error("نوبت شما نیست."))
        if not game.move(pos):
            return await msg.reply(error("حرکت نامعتبر."))
        w = game.winner()
        board = game.board_text()
        if w:
            TTT.pop(gid, None)
            res = "مساوی" if w == "draw" else f"برنده {w}"
            return await msg.edit(info(f"🎮 دوز\n\n{board}\n\n{res}"))
        return await msg.edit(info(f"🎮 دوز\n\n{board}\n\nنوبت: {game.turn}"), components=ttt_keyboard(game.board))

    # Mafia
    if data.startswith("mafia:"):
        st = MAFIA.get(gid)
        if data == "mafia:join":
            if not st or st["phase"] != MafiaPhase.LOBBY.value:
                return await msg.reply(error("لابی فعالی نیست. بنویس مافیا"))
            if user not in st["players"]:
                st["players"].append(user)
            return await msg.edit(info(f"🕵️ مافیا — لابی\nبازیکن‌ها: {len(st['players'])}"), components=mafia_lobby_keyboard())
        if data == "mafia:leave":
            if st and user in st["players"] and st["phase"] == MafiaPhase.LOBBY.value:
                st["players"] = [p for p in st["players"] if p != user]
                return await msg.edit(info(f"🕵️ لابی\nبازیکن‌ها: {len(st['players'])}"), components=mafia_lobby_keyboard())
            return
        if data == "mafia:cancel":
            if st and user == st["creator_id"]:
                MAFIA.pop(gid, None)
                return await msg.edit(info("مافیا لغو شد."))
            return
        if data == "mafia:start":
            if not st or user != st["creator_id"]:
                return await msg.reply(error("فقط سازنده."))
            if len(st["players"]) < 4:
                return await msg.reply(error("حداقل ۴ نفر."))
            try:
                st["roles"] = assign_roles(st["players"])
            except ValueError as e:
                return await msg.reply(error(str(e)))
            st["alive"] = list(st["players"])
            st["phase"] = MafiaPhase.NIGHT.value
            st["day"] = 1
            # private role messages
            bot = _get_bot(msg)
            for pid, role in st["roles"].items():
                try:
                    if bot:
                        u = await bot.get_user(int(pid))
                        if u:
                            await u.send(info(f"نقش شما در مافیا: {role}"))
                except Exception:
                    pass
            return await msg.edit(info(
                f"🕵️ بازی شروع شد!\nشب ۱\nنقش‌ها خصوصی ارسال شد.\n"
                f"بازیکن زنده: {len(st['alive'])}\n"
                "مافیا در پیوی هدف بگو (فعلاً فاز متنی)."
            ))
        return

    # Truth or Dare
    if data.startswith("tod:"):
        st = TOD.get(gid)
        if data == "tod:join":
            if not st or st["phase"] != "lobby":
                return await msg.reply(error("لابی نیست. بنویس جرعت حقیقت"))
            if user not in st["players"]:
                st["players"].append(user)
            return await msg.edit(info(f"🎲 لابی — {len(st['players'])} نفر"), components=tod_lobby_keyboard())
        if data == "tod:leave":
            if st and user in st["players"] and st["phase"] == "lobby":
                st["players"] = [p for p in st["players"] if p != user]
                return await msg.edit(info(f"🎲 لابی — {len(st['players'])} نفر"), components=tod_lobby_keyboard())
            return
        if data == "tod:start":
            if not st or user != st["creator_id"]:
                return await msg.reply(error("فقط سازنده."))
            if len(st["players"]) < 2:
                return await msg.reply(error("حداقل ۲ نفر."))
            st["phase"] = "playing"
            st["current_index"] = 0
            cur = st["players"][0]
            return await msg.edit(
                info(f"🎲 نوبت بازیکن {cur}\nحقیقت یا جرأت؟"),
                components=tod_choice_keyboard(),
            )
        if data in ("tod:truth", "tod:dare"):
            if not st or st["phase"] != "playing":
                return
            cur = st["players"][st["current_index"] % len(st["players"])]
            if user != cur:
                return await msg.reply(error("نوبت شما نیست."))
            kind = "truth" if data.endswith("truth") else "dare"
            used_key = "used_truths" if kind == "truth" else "used_dares"
            item, _ = tod_pick(kind, st[used_key])
            st["last_item"] = item
            label = "حقیقت" if kind == "truth" else "جرأت"
            return await msg.edit(
                info(f"🎲 {label}\n\n{item}\n\nبعد از انجام، «جواب دادم» را بزن."),
                components=tod_choice_keyboard(),
            )
        if data == "tod:done":
            if not st or st["phase"] != "playing":
                return
            st["current_index"] = (st["current_index"] + 1) % len(st["players"])
            cur = st["players"][st["current_index"]]
            return await msg.edit(
                info(f"🎲 نوبت بازیکن {cur}\nحقیقت یا جرأت؟"),
                components=tod_choice_keyboard(),
            )


def register_handlers(bot: Bot) -> None:
    global _bot
    _bot = bot

    @bot.listen("on_message")
    async def _m(message: Message):
        try:
            await on_message(message)
        except Exception:
            log.exception("on_message")

    @bot.listen("on_callback")
    async def _c(callback: CallbackQuery):
        try:
            await on_callback(callback)
        except Exception:
            log.exception("on_callback")

    @bot.listen("on_member_chat_join")
    async def _join(message: Message, chat, user):
        try:
            gid = int(getattr(chat, "id", 0) or 0)
            if gid != settings.ALLOWED_GROUP_ID:
                return
            st = await get_group_settings(gid)
            tpl = (st.get("welcome_text") or "").strip()
            if not tpl:
                return
            uname = (
                getattr(user, "first_name", None)
                or getattr(user, "username", None)
                or str(getattr(user, "id", ""))
            )
            gap = (
                getattr(chat, "title", None)
                or settings.ALLOWED_GROUP_USERNAME
                or "گروه"
            )
            text_out = _format_template(tpl, str(uname), str(gap))
            try:
                await chat.send(info(text_out))
            except Exception:
                if message is not None:
                    await message.reply(info(text_out))
            # track member
            try:
                uid = int(user.id)
                await upsert_user(uid, getattr(user, "username", None), str(uname))
                await upsert_member(gid, uid, "member")
            except Exception:
                pass
        except Exception:
            log.exception("on_member_chat_join")

    @bot.listen("on_member_chat_leave")
    async def _leave(message: Message, chat, user):
        try:
            gid = int(getattr(chat, "id", 0) or 0)
            if gid != settings.ALLOWED_GROUP_ID:
                return
            st = await get_group_settings(gid)
            tpl = (st.get("farewell_text") or "").strip()
            if not tpl:
                return
            uname = (
                getattr(user, "first_name", None)
                or getattr(user, "username", None)
                or str(getattr(user, "id", ""))
            )
            gap = (
                getattr(chat, "title", None)
                or settings.ALLOWED_GROUP_USERNAME
                or "گروه"
            )
            text_out = _format_template(tpl, str(uname), str(gap))
            # group message
            try:
                await chat.send(info(text_out))
            except Exception:
                if message is not None:
                    try:
                        await message.reply(info(text_out))
                    except Exception:
                        pass
            # try PM if user started the bot
            try:
                bot = _bot
                if bot is not None:
                    u = await bot.get_user(int(user.id))
                    if u is not None:
                        await u.send(info(text_out))
            except Exception as e:
                log.info("farewell PM skipped: %s", e)
        except Exception:
            log.exception("on_member_chat_leave")
