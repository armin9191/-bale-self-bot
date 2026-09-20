import logging
from datetime import date
from bale import Bot, Message, CallbackQuery
from config import settings
from bot.messages import info, error, success
from bot.permissions import is_special_admin, live_role, Role
from bot.keyboards import private_menu, ttt_keyboard
from database.postgres import init_db, get_pool
from database.repositories import upsert_user, upsert_member, increment_stat
from bot.games.tic_tac_toe import TicTacToe
from bot.handlers.backup import create_backup

log=logging.getLogger("POSSIBLY.dispatcher")
TTT={}

def uid(message):
    a=getattr(message,"author",None); return int(a.id) if a and getattr(a,"id",None) is not None else None

def text(message): return (getattr(message,"content",None) or "").strip()

def group_id(message):
    return int(getattr(message,"chat_id",getattr(getattr(message,"chat",None),"id",0)) or 0)

async def stats_record(message,gid,user):
    a=message.author
    await upsert_user(user,a.username,getattr(a,"first_name",None) or getattr(a,"name",None) or str(user))
    role=(await live_role(message.chat.bot if getattr(message,"chat",None) else None,user)) if False else Role.MEMBER
    await upsert_member(gid,user,role.value)
    kind="other"
    if getattr(message,"animation",None) is not None: kind="gifs"
    elif getattr(message,"voice",None) is not None: kind="voice"
    elif getattr(message,"photo",None) is not None: kind="photos"
    elif getattr(message,"video",None) is not None: kind="videos"
    await increment_stat(gid,user,"messages",date.today()); await increment_stat(gid,user,kind,date.today())

async def learning(message,gid,user,t):
    p=get_pool()
    if t.startswith("یاد بگیر"):
        if not is_special_admin(user): return await message.reply(error("فقط Admin یا Owner مجاز است."))
        raw=t[len("یاد بگیر"):].strip(); parts=raw.split(maxsplit=1)
        if len(parts)!=2: return await message.reply(error("فرمت: یاد بگیر trigger response"))
        trigger,response=parts
        n=await p.fetchval("SELECT COUNT(*) FROM learned_words WHERE group_id=$1",gid)
        if n>=settings.MAX_LEARNED_WORDS and not await p.fetchval("SELECT 1 FROM learned_words WHERE group_id=$1 AND trigger=$2",gid,trigger):
            return await message.reply(error("سقف ۳۰۰ یادگیری پر شده است."))
        await p.execute("""INSERT INTO learned_words(group_id,trigger,response,created_by) VALUES($1,$2,$3,$4)
        ON CONFLICT(group_id,trigger) DO UPDATE SET response=EXCLUDED.response,created_by=EXCLUDED.created_by,created_at=NOW()""",gid,trigger,response,user)
        return await message.reply(success(f"«{trigger}» یاد گرفته شد."))
    if t.startswith("فراموش کن"):
        if not is_special_admin(user): return await message.reply(error("فقط Admin یا Owner مجاز است."))
        trigger=t[len("فراموش کن"):].strip()
        r=await p.execute("DELETE FROM learned_words WHERE group_id=$1 AND trigger=$2",gid,trigger)
        return await message.reply(success("حذف شد.") if r.endswith("1") else error("پیدا نشد."))
    if t in ("لیست یادگیری","لیست یادگیری‌ها"):
        if not is_special_admin(user): return await message.reply(error("فقط Admin یا Owner مجاز است."))
        rows=await p.fetch("SELECT trigger FROM learned_words WHERE group_id=$1 ORDER BY id",gid)
        return await message.reply(info("🧠 یادگیری‌ها\n\n"+"\n".join(f"{i}. {r['trigger']}" for i,r in enumerate(rows,1)) if rows else "هنوز موردی ثبت نشده است."))
    if not t.startswith("/"):
        r=await p.fetchval("SELECT response FROM learned_words WHERE group_id=$1 AND trigger=$2",gid,t)
        if r is not None: return await message.reply(info(r))

async def admin(message,gid,user,t):
    if not is_special_admin(user): return False
    target=None; reply=getattr(message,"reply_to_message",None)
    if reply and getattr(reply,"author",None): target=int(reply.author.id)
    else:
        parts=t.split();
        if len(parts)>1:
            try: target=int(parts[1])
            except ValueError: pass
    if t.startswith("/ban") or t.startswith("/unban") or t.startswith("/kick"):
        if target is None: await message.reply(error("هدف را با User ID یا Reply مشخص کن.")); return True
        if target in (settings.OWNER_ID,settings.POSSIBLY_ADMIN_ID): await message.reply(error("این کاربر محافظت شده است.")); return True
        try:
            if t.startswith("/ban"): await message.chat.ban_chat_member(target); action="ban"
            elif t.startswith("/unban"): await message.chat.unban_chat_member(target,only_if_banned=True); action="unban"
            else: await message.chat.ban_chat_member(target); await message.chat.unban_chat_member(target,only_if_banned=False); action="kick"
            await get_pool().execute("INSERT INTO moderation_logs(group_id,actor_id,target_id,action) VALUES($1,$2,$3,$4)",gid,user,target,action)
            await message.reply(success(f"عملیات {action} برای {target} انجام شد."))
        except Exception as e:
            log.warning("moderation failed: %s",e); await message.reply(error("عملیات انجام نشد؛ دسترسی Admin و محدودیت API را بررسی کن."))
        return True
    return False

async def show_stats(message,gid):
    p=get_pool(); d=date.today()
    total=await p.fetchrow("SELECT COALESCE(SUM(messages),0) messages,COALESCE(SUM(gifs),0) gifs,COALESCE(SUM(voice),0) voice,COALESCE(SUM(photos),0) photos,COALESCE(SUM(videos),0) videos FROM daily_stats WHERE group_id=$1 AND date=$2",gid,d)
    rows=await p.fetch("SELECT u.username,u.display_name,ds.messages FROM daily_stats ds LEFT JOIN users u ON u.user_id=ds.user_id WHERE ds.group_id=$1 AND ds.date=$2 ORDER BY ds.messages DESC LIMIT 3",gid,d)
    lines=["📊 آمار امروز",f"💬 پیام‌ها: {total['messages']}",f"🎞 GIF: {total['gifs']}",f"🎤 Voice: {total['voice']}",f"🖼 عکس: {total['photos']}",f"🎬 ویدیو: {total['videos']}","","🏆 فعال‌ترین اعضا:"]
    medals=["🥇","🥈","🥉"]
    lines += [f"{medals[i]} @{r['username']} — {r['messages']} پیام" if r['username'] else f"{medals[i]} {r['display_name']} — {r['messages']} پیام" for i,r in enumerate(rows)]
    await message.reply(info("\n".join(lines)))

async def private_menu_handler(message,user):
    role=await live_role(message.chat.bot,user) if getattr(message,"chat",None) and getattr(message.chat,"bot",None) else Role.ADMIN if is_special_admin(user) else Role.MEMBER
    await message.reply(info("منوی خصوصی POSSIBLY\n\nسطح دسترسی: "+role.value),components=private_menu(role in (Role.ADMIN,Role.OWNER),role==Role.OWNER))

async def on_message(message: Message):
    user=uid(message)
    if user is None: return
    t=text(message); gid=group_id(message)
    is_private=getattr(getattr(message,"chat",None),"type","") in ("private","Private") or gid==user
    if is_private:
        if t in ("/start","start","menu","منو"):
            return await private_menu_handler(message,user)
        if t=="بکاپ" and user==settings.POSSIBLY_ADMIN_ID:
            path=await create_backup()
            if path: return await message.reply_document(path,caption="POSSIBLY PostgreSQL backup")
            return await message.reply(error("ساخت بکاپ انجام نشد یا pg_dump در محیط موجود نیست."))
        return
    if gid!=settings.ALLOWED_GROUP_ID:
        return await message.reply(info("این ربات فقط برای گروه مجاز فعال است."))
    try: await stats_record(message,gid,user)
    except Exception: log.exception("stats failed")
    if await admin(message,gid,user,t): return
    if t in ("امار","آمار"): return await show_stats(message,gid)
    if t.startswith("اکو"):
        payload=t[len("اکو"):].strip()
        if not payload: return await message.reply(error("بعد از اکو متن بنویس."))
        try: await message.delete()
        except Exception: pass
        return await message.chat.send(info(payload))
    await learning(message,gid,user,t)

async def on_callback(callback: CallbackQuery):
    data=callback.data or ""; user=int(callback.from_user.id) if getattr(callback,"from_user",None) else None
    msg=callback.message
    if data=="about": return await msg.reply(info("POSSIBLY\nGroup Management + Fun + Games\nفقط برای @possibly"))
    if data=="games": return await msg.reply(info("🎮 بازی‌ها\n\nفعلاً دوز آماده است: در گروه بنویس «دوز»"))
    if data=="group_stats": return await show_stats(msg,settings.ALLOWED_GROUP_ID)
    if data.startswith("ttt:"):
        game=TTT.get(int(msg.chat_id))
        if not game: return await msg.reply(error("بازی منقضی شده است."))
        if user not in (game.x,game.o): return await msg.reply(error("این بازی برای شما نیست."))
        expected=game.x if game.turn=="X" else game.o
        if user!=expected: return await msg.reply(error("نوبت شما نیست."))
        game.move(int(data.split(":")[1])); winner=game.winner()
        if winner: return await msg.edit(info("🎮 دوز\n\n"+str(game.board)+"\n\nنتیجه: "+winner))
        return await msg.edit(info("🎮 دوز\n\nنوبت: "+("X" if game.turn=="X" else "O")),components=ttt_keyboard(game.board))


def register_handlers(bot: Bot):
    @bot.listen("on_message")
    async def _message(message): await on_message(message)
    @bot.listen("on_callback")
    async def _callback(callback): await on_callback(callback)
