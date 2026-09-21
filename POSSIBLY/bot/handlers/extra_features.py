"""Special users, info, ASL, titles, user panel, force-join."""
from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Optional

from bale import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from config import settings
from bot.messages import info, error, success
from bot.permissions import is_special_admin, is_owner
from bot.locks import LOCK_LABELS
from database.repositories import (
    add_special, remove_special, clear_special, list_special, is_special_user,
    set_title, get_title, delete_title, list_titles, set_title_ttl, get_title_ttl,
    set_asl, get_asl, delete_asl, set_asl_verified, set_asl_self_register,
    get_asl_self_register, list_asl, random_asl, top_asl, search_asl, asl_stats,
    asl_history, inc_asl_view, toggle_asl_like,
    get_warnings, clear_warnings, get_mute, clear_mute, set_mute,
    set_protection, is_protected, get_personal_locks, set_personal_lock,
    clear_personal_locks, add_bot_manager, remove_bot_manager, is_bot_manager,
    set_force_join, clear_force_join, get_force_join, get_user_stats,
)

log = logging.getLogger("POSSIBLY.extra")


def _reply_user_id(m: Message) -> Optional[int]:
    reply = getattr(m, "reply_to_message", None)
    if reply is None:
        return None
    au = getattr(reply, "author", None) or getattr(reply, "from_user", None)
    if au is None:
        return None
    uid = getattr(au, "id", None)
    return int(uid) if uid is not None else None


def _parse_target_id(t: str, m: Message) -> Optional[int]:
    """From reply, @username leftover, or numeric id in text."""
    rid = _reply_user_id(m)
    if rid is not None:
        return rid
    # numeric
    mobj = re.search(r"(\d{5,})", t)
    if mobj:
        return int(mobj.group(1))
    return None


def _user_display(user) -> str:
    if user is None:
        return "?"
    name = getattr(user, "first_name", None) or ""
    un = getattr(user, "username", None)
    if un:
        return f"{name} (@{un})".strip()
    return name or str(getattr(user, "id", "?"))


async def _fetch_user(bot, user_id: int):
    if bot is None:
        return None
    try:
        return await bot.get_user(user_id)
    except Exception:
        return None


# ===================== SPECIAL =====================
async def handle_special(m: Message, gid: int, user: int, t: str, bot) -> bool:
    nt = t.strip()
    low = nt.replace("\u200c", " ")

    if low in ("لیست ویژه", "لیست ویژه‌ها", "لیست ویژه ها"):
        ids = await list_special(gid)
        if not ids:
            await m.reply(info("لیست ویژه خالی است."))
            return True
        lines = [f"• `{uid}`" for uid in ids]
        await m.reply(info("⭐ کاربران ویژه:\n" + "\n".join(lines)))
        return True

    if low in ("پاکسازی ویژه ها", "پاکسازی ویژه‌ها", "پاکسازی ویژه"):
        if not is_special_admin(user):
            await m.reply(error("فقط Admin/Owner."))
            return True
        n = await clear_special(gid)
        await m.reply(success(f"{n} کاربر ویژه حذف شد."))
        return True

    if low.startswith("لغو ویژه"):
        if not is_special_admin(user):
            await m.reply(error("فقط Admin/Owner."))
            return True
        tid = _parse_target_id(low, m)
        if tid is None:
            await m.reply(error("ریپلای کن یا آیدی بده: لغو ویژه [آیدی]"))
            return True
        ok = await remove_special(gid, tid)
        await m.reply(success("ویژه لغو شد.") if ok else error("در لیست نبود."))
        return True

    if low == "ویژه" or low.startswith("ویژه "):
        if not is_special_admin(user):
            await m.reply(error("فقط Admin/Owner."))
            return True
        tid = _parse_target_id(low, m)
        if tid is None:
            await m.reply(error("ریپلای کن یا آیدی بده: ویژه [آیدی]"))
            return True
        await add_special(gid, tid, user)
        await m.reply(success(f"کاربر `{tid}` ویژه شد (معاف از قفل‌ها)."))
        return True

    return False


# ===================== INFO / ID =====================
async def handle_info(m: Message, gid: int, user: int, t: str, bot) -> bool:
    nt = t.strip().lower().replace("\u200c", "")
    if nt not in ("اطلاعات", "info", "آیدی", "ایدی", "id", "آی دی"):
        # also: اطلاعات with reply still same words only
        base = t.strip().split()[0] if t.strip() else ""
        if base not in ("اطلاعات", "info", "آیدی", "ایدی", "id"):
            return False

    tid = _parse_target_id(t, m) or user
    u = await _fetch_user(bot, tid)
    title = await get_title(gid, tid)
    special = await is_special_user(gid, tid)
    warns = await get_warnings(gid, tid)
    mute = await get_mute(gid, tid)
    protected = await is_protected(gid, tid)
    asl = await get_asl(gid, tid)

    role = "کاربر عادی"
    if is_owner(tid):
        role = "👑 مالک ربات"
    elif is_special_admin(tid):
        role = "🛡 پشتیبان / ادمین ربات"
    elif await is_bot_manager(gid, tid):
        role = "🎛 مدیر ربات"
    if special:
        role += " | ⭐ ویژه"

    name = _user_display(u) if u else str(tid)
    uname = getattr(u, "username", None) if u else None
    lines = [
        "🪪 کارت شناسایی",
        f"نام: {name}",
        f"یوزرنیم: @{uname}" if uname else "یوزرنیم: —",
        f"آیدی: `{tid}`",
        f"نقش: {role}",
    ]
    if title:
        lines.append(f"لقب: {title}")
    lines.append(f"اخطار: {warns}")
    if mute and mute.get("until_ts"):
        lines.append(f"سکوت تا: {mute['until_ts']}")
    if protected:
        lines.append("🛡 محافظت‌شده")
    if asl:
        lines.append(f"اصل: ثبت‌شده (👍 {asl.get('likes',0)} | 👁 {asl.get('views',0)})")
    # copy-friendly block
    lines.append("")
    lines.append("— کپی سریع —")
    lines.append(f"ID: {tid}")
    if uname:
        lines.append(f"@{uname}")
    await m.reply(info("\n".join(lines)))
    return True


# ===================== ASL =====================
def _asl_kb(target_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("❤️ لایک", callback_data=f"asl_like:{target_id}"), row=1)
    return kb


async def _show_asl(m: Message, gid: int, profile: dict, bot, viewer: int) -> None:
    uid = int(profile["user_id"])
    await inc_asl_view(gid, uid)
    u = await _fetch_user(bot, uid)
    name = _user_display(u)
    title = await get_title(gid, uid)
    ver = "✅ تاییدشده" if profile.get("verified") else ""
    body = profile.get("body") or ""
    text = (
        f"🪪 اصل {name} {ver}\n"
        f"{'لقب: ' + title + chr(10) if title else ''}"
        f"\n{body}\n\n"
        f"❤️ {profile.get('likes', 0)}  |  👁 {int(profile.get('views', 0)) + 1}"
    )
    await m.reply(info(text), components=_asl_kb(uid))


async def handle_asl(m: Message, gid: int, user: int, t: str, bot) -> bool:
    raw = t.strip()
    # admin: ثبت اصل (reply + text is the asl of target — or reply message text)
    if raw == "ثبت اصل" or raw.startswith("ثبت اصل "):
        tid = _reply_user_id(m)
        body = raw[len("ثبت اصل"):].strip()
        if tid is not None and not body:
            # use replied message text as body
            rt = getattr(m.reply_to_message, "text", None) or getattr(m.reply_to_message, "caption", None) or ""
            body = str(rt).strip()
        if tid is None:
            # self register if enabled
            if await get_asl_self_register(gid) or is_special_admin(user):
                if not body:
                    await m.reply(error("متن اصل را بنویس: ثبت اصل [متن]"))
                    return True
                await set_asl(gid, user, body, user)
                await m.reply(success("اصل شما ثبت شد."))
                return True
            await m.reply(error("ریپلای لازم است یا ثبت شخصی فعال نیست."))
            return True
        if not is_special_admin(user) and tid != user:
            await m.reply(error("فقط ادمین می‌تواند اصل دیگران را ثبت کند."))
            return True
        if not body:
            await m.reply(error("متن اصل را مشخص کن."))
            return True
        await set_asl(gid, tid, body, user)
        await m.reply(success("اصل ثبت شد."))
        return True

    if raw.startswith("ویرایش اصل"):
        body = raw[len("ویرایش اصل"):].strip()
        tid = _reply_user_id(m) or user
        if tid != user and not is_special_admin(user):
            await m.reply(error("اجازه ندارید."))
            return True
        if tid == user and not is_special_admin(user) and not await get_asl_self_register(gid):
            await m.reply(error("ثبت/ویرایش شخصی غیرفعال است."))
            return True
        if not body:
            await m.reply(error("ویرایش اصل [متن]"))
            return True
        await set_asl(gid, tid, body, user)
        await m.reply(success("اصل ویرایش شد."))
        return True

    if raw in ("حذف اصل",):
        if not is_special_admin(user):
            await m.reply(error("فقط Admin."))
            return True
        tid = _reply_user_id(m)
        if tid is None:
            await m.reply(error("ریپلای کن."))
            return True
        ok = await delete_asl(gid, tid)
        await m.reply(success("حذف شد.") if ok else error("نبود."))
        return True

    if raw in ("تایید اصل",):
        if not is_special_admin(user):
            await m.reply(error("فقط Admin."))
            return True
        tid = _reply_user_id(m)
        if tid is None:
            await m.reply(error("ریپلای کن."))
            return True
        await set_asl_verified(gid, tid, True)
        await m.reply(success("اصل تایید شد."))
        return True

    if raw in ("لغو تایید اصل",):
        if not is_special_admin(user):
            await m.reply(error("فقط Admin."))
            return True
        tid = _reply_user_id(m)
        if tid is None:
            await m.reply(error("ریپلای کن."))
            return True
        await set_asl_verified(gid, tid, False)
        await m.reply(success("تایید برداشته شد."))
        return True

    if raw in ("فعال سازی ثبت اصل شخصی", "فعال‌سازی ثبت اصل شخصی", "فعال سازی ثبت اصل"):
        if not is_special_admin(user):
            await m.reply(error("فقط Admin."))
            return True
        await set_asl_self_register(gid, True, user)
        await m.reply(success("ثبت اصل شخصی فعال شد."))
        return True

    if raw in ("غیرفعال سازی ثبت اصل شخصی", "غیرفعال‌سازی ثبت اصل شخصی", "غیرفعال سازی ثبت اصل"):
        if not is_special_admin(user):
            await m.reply(error("فقط Admin."))
            return True
        await set_asl_self_register(gid, False, user)
        await m.reply(success("ثبت اصل شخصی غیرفعال شد."))
        return True

    if raw in ("لیست اصل‌ها", "لیست اصل ها", "لیست اصل"):
        items = await list_asl(gid, 30)
        if not items:
            await m.reply(info("اصلی ثبت نشده."))
            return True
        lines = []
        for i, p in enumerate(items, 1):
            prev = (p["body"] or "")[:40].replace("\n", " ")
            lines.append(f"{i}. `{p['user_id']}` ❤️{p['likes']} — {prev}")
        await m.reply(info("📋 لیست اصل‌ها:\n" + "\n".join(lines)))
        return True

    if raw in ("اصل من",):
        p = await get_asl(gid, user)
        if not p:
            await m.reply(info("اصلی برای شما ثبت نشده."))
            return True
        await _show_asl(m, gid, p, bot, user)
        return True

    if raw in ("اصل رندوم", "اصل تصادفی"):
        p = await random_asl(gid)
        if not p:
            await m.reply(info("اصلی نیست."))
            return True
        await _show_asl(m, gid, p, bot, user)
        return True

    if raw in ("برترین اصل‌ها", "برترین اصل ها", "برترین اصل"):
        items = await top_asl(gid, 5)
        if not items:
            await m.reply(info("خالی."))
            return True
        lines = []
        for i, p in enumerate(items, 1):
            lines.append(f"{i}. `{p['user_id']}` ❤️{p['likes']} 👁{p['views']}")
        await m.reply(info("🏆 برترین اصل‌ها:\n" + "\n".join(lines)))
        return True

    if raw in ("آمار اصل", "امار اصل"):
        st = await asl_stats(gid)
        await m.reply(info(
            f"📊 آمار اصل\nتعداد: {st['total']}\nلایک: {st['likes']}\nبازدید: {st['views']}\nتاییدشده: {st['verified']}"
        ))
        return True

    if raw.startswith("جستجوی اصل") or raw.startswith("جستجو اصل"):
        q = raw.split("اصل", 1)[-1].strip()
        if not q:
            await m.reply(error("جستجوی اصل [کلمه]"))
            return True
        items = await search_asl(gid, q)
        if not items:
            await m.reply(info("چیزی پیدا نشد."))
            return True
        lines = [f"• `{p['user_id']}` ❤️{p['likes']}" for p in items[:15]]
        await m.reply(info("🔎 نتیجه:\n" + "\n".join(lines)))
        return True

    if raw in ("تاریخچه اصل",):
        tid = _reply_user_id(m) or user
        hist = await asl_history(gid, tid)
        if not hist:
            await m.reply(info("تاریخچه‌ای نیست."))
            return True
        lines = [f"• {h['created_at']}: {(h['body'] or '')[:60]}" for h in hist]
        await m.reply(info("تاریخچه اصل:\n" + "\n".join(lines)))
        return True

    if raw == "اصل":
        tid = _reply_user_id(m)
        if tid is None:
            await m.reply(error("روی پیام کاربر ریپلای کن: اصل"))
            return True
        p = await get_asl(gid, tid)
        if not p:
            await m.reply(info("اصلی ثبت نشده."))
            return True
        await _show_asl(m, gid, p, bot, user)
        return True

    return False


async def handle_asl_callback(cb: CallbackQuery, gid: int, user: int) -> bool:
    data = getattr(cb, "data", None) or ""
    if not data.startswith("asl_like:"):
        return False
    try:
        tid = int(data.split(":")[1])
    except Exception:
        return True
    liked, total = await toggle_asl_like(gid, tid, user)
    msg = getattr(cb, "message", None)
    try:
        from bot.bale_api import answer_callback_query
        cb_id = getattr(cb, "id", None) or getattr(cb, "callback_id", None)
        if cb_id:
            await answer_callback_query(
                cb_id,
                f"{'❤️ لایک شد' if liked else 'لایک برداشته شد'} — {total}",
                show_alert=False,
            )
    except Exception:
        pass
    if msg is not None:
        try:
            # soft update not required
            pass
        except Exception:
            pass
    return True


# ===================== TITLE / لقب =====================
async def handle_title(m: Message, gid: int, user: int, t: str, bot) -> bool:
    raw = t.strip()

    if raw.startswith("تنظیم لقب"):
        if not is_special_admin(user):
            await m.reply(error("فقط Admin."))
            return True
        tid = _reply_user_id(m)
        title = raw[len("تنظیم لقب"):].strip()
        if tid is None or not title:
            await m.reply(error("ریپلای + تنظیم لقب [متن]"))
            return True
        await set_title(gid, tid, title, user)
        ttl = await get_title_ttl(gid)
        sent = await m.reply(success(f"لقب تنظیم شد: {title}"))
        if ttl > 0 and sent is not None:
            # best-effort: cannot sleep-delete easily without task; skip auto-delete of bot msg
            pass
        return True

    if raw in ("حذف لقب",):
        if not is_special_admin(user):
            await m.reply(error("فقط Admin."))
            return True
        tid = _reply_user_id(m)
        if tid is None:
            await m.reply(error("ریپلای کن."))
            return True
        ok = await delete_title(gid, tid)
        await m.reply(success("لقب حذف شد.") if ok else error("لقب نداشت."))
        return True

    if raw.startswith("تنظیم ماندگاری لقب"):
        if not is_special_admin(user):
            await m.reply(error("فقط Admin."))
            return True
        mobj = re.search(r"(\d+)", raw)
        sec = int(mobj.group(1)) if mobj else 0
        await set_title_ttl(gid, sec, user)
        await m.reply(success(f"ماندگاری لقب: {sec} ثانیه (۰=بدون حذف خودکار)."))
        return True

    if raw in ("پاکسازی لقب ترک‌کرده‌ها", "پاکسازی لقب ترک کرده ها", "پاکسازی لقب ترک‌کرده ها"):
        if not is_special_admin(user):
            await m.reply(error("فقط Admin."))
            return True
        # without full member list API scan, just acknowledge
        await m.reply(info("در نسخه فعلی پاکسازی دستی با حذف لقب انجام شود."))
        return True

    if raw in ("لیست لقب ها", "لیست لقب‌ها", "لیست القاب"):
        items = await list_titles(gid)
        if not items:
            await m.reply(info("کسی لقب ندارد."))
            return True
        lines = [f"• `{x['user_id']}`: {x['title']}" for x in items[:50]]
        await m.reply(info("🎖 لیست لقب‌ها:\n" + "\n".join(lines)))
        return True

    if raw == "لقب":
        tid = _reply_user_id(m) or user
        title = await get_title(gid, tid)
        if not title:
            await m.reply(info("لقب ندارد."))
            return True
        await m.reply(info(f"🎖 لقب: {title}"))
        return True

    return False


# ===================== USER PANEL =====================
def _panel_kb(tid: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🚫 بن", callback_data=f"pnl:{tid}:ban"), row=1)
    kb.add(InlineKeyboardButton("✅ آنبن", callback_data=f"pnl:{tid}:unban"), row=1)
    kb.add(InlineKeyboardButton("🔇 سکوت ۱س", callback_data=f"pnl:{tid}:mute:1"), row=2)
    kb.add(InlineKeyboardButton("🔇 ۱ر", callback_data=f"pnl:{tid}:mute:24"), row=2)
    kb.add(InlineKeyboardButton("🔊 رفع سکوت", callback_data=f"pnl:{tid}:unmute"), row=2)
    kb.add(InlineKeyboardButton("⭐ ویژه", callback_data=f"pnl:{tid}:special"), row=3)
    kb.add(InlineKeyboardButton("⭐ لغو ویژه", callback_data=f"pnl:{tid}:unspecial"), row=3)
    kb.add(InlineKeyboardButton("🛡 محافظت", callback_data=f"pnl:{tid}:protect"), row=4)
    kb.add(InlineKeyboardButton("🧹 پاک اخطار", callback_data=f"pnl:{tid}:clearwarn"), row=4)
    kb.add(InlineKeyboardButton("🔒 قرنطینه", callback_data=f"pnl:{tid}:lockall"), row=5)
    kb.add(InlineKeyboardButton("🟢 آزادسازی", callback_data=f"pnl:{tid}:unlockall"), row=5)
    return kb


async def handle_panel(m: Message, gid: int, user: int, t: str, bot) -> bool:
    raw = t.strip()
    if not (raw == "پنل کاربر" or raw.startswith("پنل کاربر ")):
        return False
    if not is_special_admin(user):
        await m.reply(error("فقط Admin/Owner."))
        return True
    tid = _parse_target_id(raw, m)
    if tid is None:
        await m.reply(error("ریپلای یا آیدی: پنل کاربر [آیدی]"))
        return True

    u = await _fetch_user(bot, tid)
    title = await get_title(gid, tid)
    special = await is_special_user(gid, tid)
    warns = await get_warnings(gid, tid)
    mute = await get_mute(gid, tid)
    protected = await is_protected(gid, tid)
    plocks = await get_personal_locks(gid, tid)

    lines = [
        f"🪪 پنل کاربر `{tid}`",
        f"نام: {_user_display(u)}",
        f"لقب: {title or '—'}",
        f"ویژه: {'بله' if special else 'خیر'}",
        f"اخطار: {warns}",
        f"محافظت: {'بله' if protected else 'خیر'}",
        f"سکوت: {mute['until_ts'] if mute and mute.get('until_ts') else 'خیر'}",
        f"قفل اختصاصی: {len(plocks)} مورد",
    ]
    await m.reply(info("\n".join(lines)), components=_panel_kb(tid))
    return True


async def handle_panel_callback(cb: CallbackQuery, gid: int, user: int, bot) -> bool:
    data = getattr(cb, "data", None) or ""
    if not data.startswith("pnl:"):
        return False
    if not is_special_admin(user):
        return True
    parts = data.split(":")
    try:
        tid = int(parts[1])
        action = parts[2]
    except Exception:
        return True

    from bot.bale_api import answer_callback_query
    cb_id = getattr(cb, "id", None) or getattr(cb, "callback_id", None)
    msg = getattr(cb, "message", None)

    async def ok(text: str):
        if cb_id:
            await answer_callback_query(cb_id, text, show_alert=True)

    try:
        if action == "ban":
            if await is_protected(gid, tid) and not is_owner(user):
                await ok("کاربر محافظت‌شده است.")
                return True
            if bot:
                await bot.ban_chat_member(gid, tid)
            await ok("بن شد.")
        elif action == "unban":
            if bot:
                await bot.unban_chat_member(gid, tid)
            await ok("آنبن شد.")
        elif action == "mute":
            hours = int(parts[3]) if len(parts) > 3 else 1
            until = datetime.now(timezone.utc) + timedelta(hours=hours)
            await set_mute(gid, tid, until, user)
            await ok(f"سکوت {hours}س.")
        elif action == "unmute":
            await clear_mute(gid, tid)
            await ok("رفع سکوت.")
        elif action == "special":
            await add_special(gid, tid, user)
            await ok("ویژه شد.")
        elif action == "unspecial":
            await remove_special(gid, tid)
            await ok("لغو ویژه.")
        elif action == "protect":
            cur = await is_protected(gid, tid)
            await set_protection(gid, tid, not cur, user)
            await ok("محافظت تغییر کرد." if is_owner(user) else "فقط مالک.")
        elif action == "clearwarn":
            await clear_warnings(gid, tid)
            await ok("اخطارها پاک شد.")
        elif action == "lockall":
            for k in LOCK_LABELS:
                await set_personal_lock(gid, tid, k, "lock")
            await ok("قرنطینه کامل.")
        elif action == "unlockall":
            await clear_personal_locks(gid, tid)
            for k in LOCK_LABELS:
                await set_personal_lock(gid, tid, k, "open")
            await ok("آزادسازی کامل.")
    except Exception as e:
        log.warning("panel action: %s", e)
        await ok("خطا در انجام.")
    return True


# ===================== FORCE JOIN =====================
async def handle_force_join(m: Message, gid: int, user: int, t: str) -> bool:
    raw = t.strip()
    if raw.startswith("تنظیم قفل جوین"):
        if not is_special_admin(user):
            await m.reply(error("فقط Admin."))
            return True
        ch = raw[len("تنظیم قفل جوین"):].strip()
        if not ch:
            await m.reply(error("نمونه: تنظیم قفل جوین @possibly"))
            return True
        await set_force_join(gid, ch, user)
        await m.reply(success(f"قفل جوین روی {ch} تنظیم شد.\nربات باید در کانال ادمین باشد."))
        return True

    if raw.startswith("حذف قفل جوین"):
        if not is_special_admin(user):
            await m.reply(error("فقط Admin."))
            return True
        await clear_force_join(gid)
        await m.reply(success("قفل جوین حذف شد."))
        return True

    return False


async def check_force_join(m: Message, gid: int, user: int, bot) -> bool:
    """Return True if user is blocked (not in required channel)."""
    if is_special_admin(user) or await is_special_user(gid, user):
        return False
    ch = await get_force_join(gid)
    if not ch or bot is None:
        return False
    try:
        # channel id may be @username or numeric
        member = await bot.get_chat_member(ch, user)
        status = str(getattr(member, "status", "") or "").lower()
        if status in ("left", "kicked", "banned", "") or member is None:
            try:
                await m.delete()
            except Exception:
                pass
            try:
                await m.reply(
                    error(f"برای ارسال پیام باید عضو {ch} باشی."),
                    components=_force_join_kb(ch),
                )
            except Exception:
                pass
            return True
    except Exception as e:
        # if cannot check, don't block everyone
        log.info("force join check failed: %s", e)
    return False


def _force_join_kb(channel: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    url = channel if channel.startswith("http") else f"https://ble.ir/{channel.lstrip('@')}"
    try:
        kb.add(InlineKeyboardButton("عضویت در کانال", url=url), row=1)
    except Exception:
        pass
    return kb


# ===================== MUTE ENFORCE =====================
async def check_mute(m: Message, gid: int, user: int) -> bool:
    if is_special_admin(user):
        return False
    mute = await get_mute(gid, user)
    if not mute or not mute.get("until_ts"):
        return False
    until = mute["until_ts"]
    if getattr(until, "tzinfo", None) is None:
        until = until.replace(tzinfo=timezone.utc)
    if until > datetime.now(timezone.utc):
        try:
            await m.delete()
        except Exception:
            pass
        return True
    await clear_mute(gid, user)
    return False


async def process_extra(m: Message, gid: int, user: int, t: str, bot) -> bool:
    """Try all extra feature text commands. Return True if handled."""
    if await handle_special(m, gid, user, t, bot):
        return True
    if await handle_info(m, gid, user, t, bot):
        return True
    if await handle_asl(m, gid, user, t, bot):
        return True
    if await handle_title(m, gid, user, t, bot):
        return True
    if await handle_panel(m, gid, user, t, bot):
        return True
    if await handle_force_join(m, gid, user, t):
        return True
    return False
