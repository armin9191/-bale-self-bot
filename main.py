import time

from config import FORBIDDEN_COOLDOWN
from rss_reader import get_news, is_fresh
from storage import is_news_sent, mark_news_sent
from users import update_last_send
from sender import send_message, send_photo
from utils import add_emoji
from category_engine import detect_category_advanced, news_matches_channel
from ai import translate_news
from analytics import record_message, snapshot_members
from commenter import extract_message_id, post_comment, remember_post
from news_targets import active_news_channels


CHECK_INTERVAL = 15
_FORBIDDEN_UNTIL = {}
_LAST_EMPTY = 0
_LAST_SNAP = 0


def get_all_channels():
    return active_news_channels()


def needed_categories(channels):
    selected = set()
    for channel in channels:
        selected.update(channel.get("categories") or ["همه"])
    return list(selected)


def build_message(news, channel):
    title = (news.get("title") or "").strip()
    try:
        title = translate_news(title)
    except Exception:
        pass
    category = news.get("feed_category") or detect_category_advanced(
        title, news.get("source", ""), news.get("feed_category")
    )
    if channel.get("show_emoji", True):
        title = add_emoji(title, category)
    message = title
    footer = (channel.get("footer_text") or "").strip()
    if footer:
        message += f"\n\n{footer}"
    return message


def can_send(channel):
    channel_id = channel["id"]
    until = _FORBIDDEN_UNTIL.get(channel_id, 0)
    if until > time.time():
        return False
    now = time.time()
    last_send = float(channel.get("last_send") or 0)
    interval_minutes = int(channel.get("interval") or 10)
    return (now - last_send) >= max(interval_minutes, 1) * 60


def send_news_to_channel(channel, news):
    message = build_message(news, channel)
    image = news.get("image")
    if channel.get("send_image", True) and image:
        return send_photo(channel["id"], image, message)
    return send_message(channel["id"], message)


def maybe_comment(channel, result):
    if not channel.get("comment_on"):
        return
    text = (channel.get("comment_text") or "").strip()
    if not text:
        return
    message_id = extract_message_id(result)
    remember_post(channel.get("user_id"), channel["id"], message_id)
    time.sleep(0.4)
    comment = post_comment(channel["id"], text, message_id)
    if not comment.get("ok"):
        print(f"⚠️ کامنت {channel['id']} نرفت: {comment.get('description', '')[:120]}")


def mark_forbidden(channel_id):
    _FORBIDDEN_UNTIL[channel_id] = time.time() + FORBIDDEN_COOLDOWN
    print(f"⏰ {channel_id} به خاطر 403 برای {FORBIDDEN_COOLDOWN // 60} دقیقه نادیده شد.")


def run():
    global _LAST_EMPTY, _LAST_SNAP
    print("🚀 AutoNewsBot MultiChannel Started...")
    while True:
        try:
            channels = get_all_channels()
            if not channels:
                now = time.time()
                if now - _LAST_EMPTY > 120:
                    print("ℹ️ کانال فعالی برای ارسال نیست")
                    _LAST_EMPTY = now
                time.sleep(CHECK_INTERVAL)
                continue
            now = time.time()
            if now - _LAST_SNAP > 600:
                for channel in channels:
                    try:
                        snapshot_members(channel["id"])
                    except Exception:
                        pass
                _LAST_SNAP = now
            news_list = get_news(needed_categories(channels))
            if not news_list:
                time.sleep(CHECK_INTERVAL)
                continue
            for channel in channels:
                if not can_send(channel):
                    continue
                categories = channel.get("categories") or ["همه"]
                for latest_news in news_list:
                    link = (latest_news.get("link") or "").strip()
                    title = (latest_news.get("title") or "").strip()
                    if not link or not title:
                        continue
                    if not is_fresh(latest_news):
                        continue
                    if is_news_sent(channel["id"], link):
                        continue
                    if not news_matches_channel(
                        title,
                        latest_news.get("source", ""),
                        categories,
                        latest_news.get("feed_category"),
                    ):
                        continue
                    try:
                        result = send_news_to_channel(channel, latest_news)
                    except Exception as send_error:
                        print("❌ خطا در ارسال:", send_error)
                        result = {"ok": False, "forbidden": False}
                    if not isinstance(result, dict):
                        result = {"ok": bool(result), "forbidden": False}
                    if result.get("forbidden"):
                        mark_forbidden(channel["id"])
                        break
                    if not result.get("ok"):
                        print(f"❌ ارسال ناموفق بود: {channel['id']}")
                        break
                    mark_news_sent(channel["id"], link)
                    update_last_send(channel["user_id"], channel["id"], time.time())
                    maybe_comment(channel, result)
                    try:
                        record_message(channel["id"])
                    except Exception:
                        pass
                    age_min = max(0, int((time.time() - float(latest_news.get("published") or time.time())) // 60))
                    print(
                        f"✅ ارسال شد به {channel['id']}\n"
                        f"📂 دسته خبر: {latest_news.get('feed_category')}\n"
                        f"🏷 فیلتر کانال: {', '.join(categories)}\n"
                        f"⏱ عمر خبر: {age_min} دقیقه\n"
                        f"⏰ ارسال بعدی: {channel.get('interval', 10)} دقیقه دیگر"
                    )
                    break
            time.sleep(CHECK_INTERVAL)
        except Exception as error:
            print("❌ خطای اصلی:", error)
            time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    run()
