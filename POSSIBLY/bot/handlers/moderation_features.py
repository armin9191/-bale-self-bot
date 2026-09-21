"""Group lock, group info, mute, warn, message purge."""
from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone, time as dtime
from typing import Optional

from bale import Message

from config import settings
from bot.messages import info, error, success
from bot.permissions import is_special_admin, is_owner
from bot.locks import LOCK_LABELS, format_locks_status
from database.repositories import (
    get_group_lock, set_group_lock_manual, set_group_lock_daily, clear_group_lock_daily,
    get_group_locks, get_group_settings, get_force_join,
    set_mute_full, clear_mute_full, list_mutes, clear_all_mutes, get_mute_full,
    add_warn_record, remove_one_warn, list_warns, clear_all_warns, clear_warnings,
    get_warnings, set_max_warns, get_max_warns, is_special_user, asl_stats,
    get_today_totals, is_protected,
)

log = logging.getLogger("POSSIBLY.modfeat")


def _reply_uid(m: Message) -> Optional[int]:
    reply = getattr(m, "reply_to_message", None)
    if not reply:
        return None
    au = getattr(reply, "author", None) or getattr(reply, "from_user", None)
    if not au or getattr(au, "id", None) is None:
        return None
    return int(au.id)


def _parse_uid(t: str, m: Message) -> Optional[int]:
    rid = _reply_uid(m)
    if rid is not None:
        return rid
    mobj = re.search(r"(\d{5,})", t)
    return int(mobj.group(1)) if mobj else None


def _parse_duration(s: str) -> Optional[timedelta]:
    s = s.strip().lower().replace(" ", "")
    m = re.fullmatch(r"(\d+)(s|m|h|d|ثانیه|دقیقه|ساعت|روز)?", s)
    if not m:
        return None
    n = int(m.group(1))
    unit = m.group(2) or "m"
    if unit in ("s", "ثانیه"):
        return timedelta(seconds=n)
    if unit in ("m", "دقیقه"):
        return timedelta(minutes=n)
    if unit in ("h", "ساعت"):
        return timedelta(hours=n)
    if unit in ("d", "روز"):
        return timedelta(days=n)
    return timedelta(minutes=n)


def _parse_hhmm(s: str) -> Optional[tuple[int, int]]:
    m = re.fullmatch(r"(\d{1,2}):(\d{2})", s.strip())
    if not m:
        return None
    h, mi = int(m.group(1)), int(m.group(2))
    if 0 <= h <= 23 and 0 <= mi <= 59:
        return h, mi
    return None


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _tehran_now() -> datetime:
    # Iran is UTC+3:30 (no DST currently observed in many systems; use fixed offset)
    return datetime.now(timezone(timedelta(hours=3, minutes=30)))


def _in_daily_window(start: str, end: str) -> bool:
    sp = _parse_hhmm(start)
    ep = _parse_hhmm(end)
    if not sp or not ep:
        return False
    now = _tehran_now().time()
    st = dtime(sp[0], sp[1])
    en = dtime(ep[0], ep[1])
    if st <= en:
        return st <= now < en
    # overnight e.g. 23:00-07:00
    return now >= st or now < en


async def is_group_effectively_locked(gid: int) -> bool:
    st = await get_group_lock(gid)
    # timed unlock
    if st.get("locked") and st.get("until_ts"):
        until = st["until_ts"]
        if getattr(until, "tzinfo", None) is None:
            until = until.replace(tzinfo=timezone.utc)
        if until <= _now_utc():
            await set_group_lock_manual(gid, False, 0, None)
            st["locked"] = False
        else:
            return True
    elif st.get("locked"):
        return True
    # daily schedule
    ds, de = st.get("daily_start"), st.get("daily_end")
    if ds and de and _in_daily_window(ds, de):
        return True
    return False


async def check_group_lock(m: Message, gid: int, user: int) -> bool:
    """If locked and user not admin/special → delete. Return True if blocked."""
    if is_special_admin(user):
        return False
    try:
        if await is_special_user(gid, user):
            return False
    except Exception:
        pass
    if not await is_group_effectively_locked(gid):
        return False
    try:
        await m.delete()
    except Exception:
        pass
    return True


# ---------- commands: group lock ----------
async def handle_group_lock_cmd(m: Message, gid: int, user: int, t: str) -> bool:
    raw = t.strip()
    low = raw.replace("\u200c", " ")

    if low in ("باز کردن گروه", "بازکردن گروه", "باز گروه"):
        if not is_special_admin(user):
            await m.reply(error("فقط Admin."))
            return True
        await set_group_lock_manual(gid, False, user, None)
        await m.reply(success("گروه باز شد."))
        return True

    if low.startswith("قفل گروه روزانه"):
        if not is_special_admin(user):
            await m.reply(error("فقط Admin."))
            return True
        rest = low.split("روزانه", 1)[-1].strip()
        mobj = re.search(r"(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})", rest)
        if not mobj:
            await m.reply(error("نمونه: قفل گروه روزانه 23:00-07:00"))
            return True
        await set_group_lock_daily(gid, mobj.group(1), mobj.group(2), user)
        await m.reply(success(f"قفل روزانه تنظیم شد: {mobj.group(1)} تا {mobj.group(2)}"))
        return True

    if low.startswith("قفل گروه تا"):
        if not is_special_admin(user):
            await m.reply(error("فقط Admin."))
            return True
        rest = low[len("قفل گروه تا"):].strip()
        hh = _parse_hhmm(rest)
        if not hh:
            await m.reply(error("نمونه: قفل گروه تا 23:00"))
            return True
        now = _tehran_now()
        target = now.replace(hour=hh[0], minute=hh[1], second=0, microsecond=0)
        if target <= now:
            target = target + timedelta(days=1)
        # store as UTC
        until = target.astimezone(timezone.utc)
        await set_group_lock_manual(gid, True, user, until)
        await m.reply(success(f"گروه تا {rest} قفل شد (خودکار باز می‌شود)."))
        return True

    if low in ("قفل گروه", "بستن گروه"):
        if not is_special_admin(user):
            await m.reply(error("فقط Admin."))
            return True
        await set_group_lock_manual(gid, True, user, None)
        await m.reply(success("گروه قفل شد. فقط مدیران می‌توانند پیام بفرستند."))
        return True

    return False


# ---------- group info ----------
async def handle_group_info(m: Message, gid: int, user: int, t: str) -> bool:
    if t.strip() not in ("اطلاعات گروه", "وضعیت گروه", "info group"):
        return False
    locks = await get_group_locks(gid)
    gl = await get_group_lock(gid)
    settings_g = await get_group_settings(gid)
    fj = await get_force_join(gid)
    max_w = await get_max_warns(gid)
    asls = await asl_stats(gid)
    totals = await get_today_totals(gid, datetime.now().date())

    eff = await is_group_effectively_locked(gid)
    lines = [
        "📊 اطلاعات گروه",
        f"آیدی گروه: `{gid}`",
        f"قفل کلی گروه: {'🔒 فعال' if eff else '🔓 غیرفعال'}",
    ]
    if gl.get("until_ts"):
        lines.append(f"قفل تا: {gl['until_ts']}")
    if gl.get("daily_start") and gl.get("daily_end"):
        lines.append(f"قفل روزانه: {gl['daily_start']}-{gl['daily_end']}")
    lines.append("")
    lines.append("🔹 قفل‌های محتوا:")
    for k, label in LOCK_LABELS.items():
        on = locks.get(k, False)
        lines.append(f"{'✅' if on else '❌'} {label}")
    lines.append("")
    lines.append(f"جوین اجباری: {fj or '❌'}")
    lines.append(f"قوانین: {'✅' if (settings_g.get('rules_text') or '').strip() else '❌'}")
    lines.append(f"خوشامد: {'✅' if (settings_g.get('welcome_text') or '').strip() else '❌'}")
    lines.append(f"بدرقه: {'✅' if (settings_g.get('farewell_text') or '').strip() else '❌'}")
    lines.append(f"حد نصاب اخطار: {max_w}")
    lines.append(f"اصل‌ها: {asls.get('total', 0)}")
    lines.append(f"پیام امروز: {totals.get('messages', 0) if isinstance(totals, dict) else totals}")
    await m.reply(info("\n".join(lines)))
    return True


# ---------- mute ----------
async def handle_mute_cmd(m: Message, gid: int, user: int, t: str, bot) -> bool:
    raw = t.strip()

    if raw in ("لیست سکوت",):
        if not (is_special_admin(user) or await is_special_user(gid, user)):
            await m.reply(error("فقط ادمین/ویژه."))
            return True
        items = await list_mutes(gid)
        if not items:
            await m.reply(info("لیست سکوت خالی است."))
            return True
        lines = []
        for x in items[:40]:
            lines.append(f"• `{x['user_id']}` تا {x.get('until_ts') or '∞'} | {x.get('reason') or '-'}")
        await m.reply(info("🤐 لیست سکوت:\n" + "\n".join(lines)))
        return True

    if raw in ("پاکسازی سکوت",):
        if not is_special_admin(user):
            await m.reply(error("فقط Admin."))
            return True
        n = await clear_all_mutes(gid)
        await m.reply(success(f"{n} سکوت پاک شد."))
        return True

    if raw.startswith("تمدید سکوت"):
        if not is_special_admin(user):
            await m.reply(error("فقط Admin."))
            return True
        tid = _parse_uid(raw, m)
        rest = raw[len("تمدید سکوت"):].strip()
        # remove id if present
        rest = re.sub(r"\d{5,}", "", rest).strip()
        dur = _parse_duration(rest.split()[0]) if rest else timedelta(minutes=10)
        if tid is None:
            await m.reply(error("ریپلای یا آیدی + مدت"))
            return True
        cur = await get_mute_full(gid, tid)
        base = _now_utc()
        if cur and cur.get("until_ts"):
            u = cur["until_ts"]
            if getattr(u, "tzinfo", None) is None:
                u = u.replace(tzinfo=timezone.utc)
            if u > base:
                base = u
        until = base + (dur or timedelta(minutes=10))
        await set_mute_full(gid, tid, until, user, cur.get("reason") if cur else None)
        await m.reply(success(f"سکوت تمدید شد تا {until}"))
        return True

    # حذف سکوت
    if raw.startswith("حذف سکوت") or raw.startswith("رفع سکوت"):
        if not is_special_admin(user):
            await m.reply(error("فقط Admin."))
            return True
        # optional reason after :
        tid = _parse_uid(raw, m)
        if tid is None:
            await m.reply(error("ریپلای یا آیدی"))
            return True
        await clear_mute_full(gid, tid)
        await m.reply(success("سکوت برداشته شد."))
        return True

    # سکوت / سکوت: 10m reason
    if raw == "سکوت" or raw.startswith("سکوت ") or raw.startswith("سکوت:"):
        if not is_special_admin(user):
            await m.reply(error("فقط Admin."))
            return True
        tid = _parse_uid(raw, m)
        if tid is None:
            await m.reply(error("ریپلای یا آیدی بده."))
            return True
        if await is_protected(gid, tid) and not is_owner(user):
            await m.reply(error("کاربر محافظت‌شده است."))
            return True
        reason = None
        dur = timedelta(hours=1)
        body = raw
        if ":" in raw:
            body = raw.split(":", 1)[-1].strip()
        else:
            body = re.sub(r"^سکوت\s*", "", raw).strip()
            body = re.sub(r"\d{5,}", "", body).strip()
        # parse duration token
        parts = body.split()
        if parts:
            d = _parse_duration(parts[0])
            if d:
                dur = d
                reason = " ".join(parts[1:]).strip() or None
            else:
                reason = body or None
        until = _now_utc() + dur
        await set_mute_full(gid, tid, until, user, reason)
        await m.reply(success(
            f"کاربر `{tid}` سکوت شد تا {until.strftime('%Y-%m-%d %H:%M')} UTC"
            + (f"\nدلیل: {reason}" if reason else "")
        ))
        return True

    return False


# ---------- warn ----------
async def handle_warn_cmd(m: Message, gid: int, user: int, t: str, bot) -> bool:
    raw = t.strip()

    if raw.startswith("تنظیم اخطار"):
        if not is_special_admin(user):
            await m.reply(error("فقط Admin."))
            return True
        mobj = re.search(r"(\d+)", raw)
        if not mobj:
            await m.reply(error("نمونه: تنظیم اخطار ۵"))
            return True
        n = max(1, min(20, int(mobj.group(1))))
        await set_max_warns(gid, n, user)
        await m.reply(success(f"حد نصاب اخطار: {n}"))
        return True

    if raw in ("لیست اخطار", "لیست اخطارها", "لیست اخطار ها"):
        if not (is_special_admin(user) or await is_special_user(gid, user)):
            await m.reply(error("فقط ادمین/ویژه."))
            return True
        items = await list_warns(gid)
        if not items:
            await m.reply(info("لیست اخطار خالی است."))
            return True
        lines = [f"• `{x['user_id']}`: {x['count']}" for x in items[:50]]
        await m.reply(info("⚠️ لیست اخطار:\n" + "\n".join(lines)))
        return True

    if raw in ("پاکسازی لیست اخطار", "پاکسازی اخطار"):
        if not is_special_admin(user):
            await m.reply(error("فقط Admin."))
            return True
        n = await clear_all_warns(gid)
        await m.reply(success(f"{n} رکورد اخطار پاک شد."))
        return True

    if raw in ("حذف اخطار ها", "حذف اخطارها") or raw.startswith("حذف اخطار"):
        if not is_special_admin(user):
            await m.reply(error("فقط Admin."))
            return True
        tid = _parse_uid(raw, m)
        if tid is None:
            await m.reply(error("ریپلای یا آیدی"))
            return True
        if raw.strip() in ("حذف اخطار ها", "حذف اخطارها"):
            await clear_warnings(gid, tid)
            await m.reply(success("همه اخطارهای کاربر پاک شد."))
            return True
        c = await remove_one_warn(gid, tid)
        await m.reply(success(f"یک اخطار حذف شد. مانده: {c}"))
        return True

    if raw == "اخطار" or raw.startswith("اخطار ") or raw.startswith("اخطار:"):
        if not is_special_admin(user):
            await m.reply(error("فقط Admin."))
            return True
        tid = _parse_uid(raw, m)
        if tid is None:
            await m.reply(error("ریپلای یا آیدی"))
            return True
        if await is_protected(gid, tid) and not is_owner(user):
            await m.reply(error("کاربر محافظت‌شده است."))
            return True
        reason = None
        if ":" in raw:
            reason = raw.split(":", 1)[-1].strip() or None
        count = await add_warn_record(gid, tid, user, reason)
        max_w = await get_max_warns(gid)
        msg = f"اخطار به `{tid}` — تعداد: {count}/{max_w}"
        if reason:
            msg += f"\nدلیل: {reason}"
        await m.reply(success(msg))
        if count >= max_w:
            # kick (ban+unban style) or mute
            try:
                if bot:
                    await bot.ban_chat_member(gid, tid)
                    try:
                        await bot.unban_chat_member(gid, tid)
                    except Exception:
                        pass
                await m.reply(warning_or_info(f"حد نصاب اخطار رسید — کاربر `{tid}` اخراج شد."))
            except Exception as e:
                log.warning("warn kick: %s", e)
                until = _now_utc() + timedelta(hours=24)
                await set_mute_full(gid, tid, until, user, "حد نصاب اخطار")
                await m.reply(success("اخراج ممکن نشد؛ ۲۴س سکوت اعمال شد."))
        return True

    return False


def warning_or_info(text: str) -> str:
    from bot.messages import warning
    return warning(text)


# ---------- purge messages ----------
async def handle_purge(m: Message, gid: int, user: int, t: str, bot) -> bool:
    raw = t.strip()
    if not is_special_admin(user):
        if raw in ("حذف", "حذف همه") or raw.startswith("حذف "):
            await m.reply(error("فقط Admin."))
            return True
        return False

    if raw in ("حذف همه",):
        # try delete last N message ids downward from current
        mid = getattr(m, "message_id", None) or getattr(m, "message_id", None)
        if mid is None or bot is None:
            await m.reply(error("شناسه پیام در دسترس نیست."))
            return True
        deleted = 0
        for limit in (300, 200, 100, 50):
            deleted = 0
            for i in range(int(mid), max(int(mid) - limit, 0), -1):
                try:
                    await bot.delete_message(gid, i)
                    deleted += 1
                except Exception:
                    pass
            if deleted > 0:
                break
        await m.reply(success(f"تلاش پاکسازی انجام شد. حذف‌شده تقریبی: {deleted}"))
        return True

    if raw.startswith("حذف ") and re.search(r"\d+", raw):
        mobj = re.search(r"(\d+)", raw)
        n = min(300, max(1, int(mobj.group(1))))
        mid = getattr(m, "message_id", None)
        if mid is None or bot is None:
            await m.reply(error("امکان حذف انبوه نیست."))
            return True
        deleted = 0
        for i in range(int(mid), max(int(mid) - n, 0), -1):
            try:
                await bot.delete_message(gid, i)
                deleted += 1
            except Exception:
                pass
        await m.reply(success(f"{deleted} پیام حذف شد (درخواست {n})."))
        return True

    if raw == "حذف":
        reply = getattr(m, "reply_to_message", None)
        if reply is None:
            await m.reply(error("روی پیام ریپلای کن: حذف"))
            return True
        start_id = getattr(reply, "message_id", None)
        end_id = getattr(m, "message_id", None)
        if start_id is None or end_id is None or bot is None:
            try:
                await reply.delete()
                await m.delete()
            except Exception:
                pass
            await m.reply(success("پیام ریپلای‌شده حذف شد."))
            return True
        a, b = int(start_id), int(end_id)
        if a > b:
            a, b = b, a
        # cap 300
        if b - a > 300:
            a = b - 300
        deleted = 0
        for i in range(a, b + 1):
            try:
                await bot.delete_message(gid, i)
                deleted += 1
            except Exception:
                pass
        # may fail to reply if own message deleted
        try:
            await bot.send_message(gid, success(f"{deleted} پیام حذف شد."))
        except Exception:
            pass
        return True

    return False


async def process_moderation_features(m: Message, gid: int, user: int, t: str, bot) -> bool:
    if await handle_group_lock_cmd(m, gid, user, t):
        return True
    if await handle_group_info(m, gid, user, t):
        return True
    if await handle_mute_cmd(m, gid, user, t, bot):
        return True
    if await handle_warn_cmd(m, gid, user, t, bot):
        return True
    if await handle_purge(m, gid, user, t, bot):
        return True
    return False
