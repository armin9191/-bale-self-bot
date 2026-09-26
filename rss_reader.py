import calendar
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

import feedparser
import requests

from config import CATEGORY_FEEDS, MAX_NEWS_AGE_SECONDS, RSS_CACHE_SECONDS

try:
    from config import FALLBACK_NEWS_AGE_SECONDS
except Exception:
    FALLBACK_NEWS_AGE_SECONDS = 3 * 60 * 60


_CACHE = {"key": None, "at": 0, "items": []}
_DEAD_FEEDS = {}
DEAD_FOR = 600
HEADERS = {"User-Agent": "Mozilla/5.0 AutoNewsBot/2.4"}
_EMPTY_LOG_AT = 0


def extract_image(entry):
    media = entry.get("media_content")
    if isinstance(media, list) and media:
        url = media[0].get("url")
        if isinstance(url, str) and url.startswith("http"):
            return url
    media_thumb = entry.get("media_thumbnail")
    if isinstance(media_thumb, list) and media_thumb:
        url = media_thumb[0].get("url")
        if isinstance(url, str) and url.startswith("http"):
            return url
    enclosures = entry.get("enclosures")
    if isinstance(enclosures, list) and enclosures:
        url = enclosures[0].get("href")
        if isinstance(url, str) and url.startswith("http"):
            return url
    return None


def source_name(feed_url):
    try:
        return urlparse(feed_url).netloc.replace("www.", "") or feed_url
    except Exception:
        return feed_url


def _timestamp_from_struct(value):
    if not value:
        return 0
    try:
        return int(calendar.timegm(value))
    except Exception:
        return 0


def entry_published(entry, fallback=0):
    for key in ("published_parsed", "updated_parsed"):
        stamp = _timestamp_from_struct(entry.get(key))
        if stamp:
            return stamp
    for key in ("published", "updated"):
        raw = entry.get(key)
        if not raw:
            continue
        try:
            dt = parsedate_to_datetime(raw)
            if dt.tzinfo is None:
                stamp = int(dt.timestamp()) - 3 * 3600 - 1800
            else:
                stamp = int(dt.timestamp())
            if stamp:
                return stamp
        except Exception:
            continue
    return fallback


def is_fresh(news, now=None, max_age=None):
    now = now or time.time()
    published = float(news.get("published") or 0)
    if published <= 0:
        return False
    if published > now + 180:
        published = now
    return (now - published) <= (max_age or FALLBACK_NEWS_AGE_SECONDS)


def _feeds_for(categories):
    if not categories or "همه" in categories:
        categories = list(CATEGORY_FEEDS.keys())
    now = time.time()
    seen = set()
    selected = []
    for category in categories:
        for url in CATEGORY_FEEDS.get(category, []):
            if url in seen:
                continue
            if _DEAD_FEEDS.get(url, 0) > now:
                continue
            seen.add(url)
            selected.append((category, url))
    return selected


def _mark_dead(feed_url, error):
    _DEAD_FEEDS[feed_url] = time.time() + DEAD_FOR
    print(f"⚠️ RSS نادست شد: {feed_url} | {error}")


def _fetch_one(category, feed_url):
    items = []
    try:
        response = requests.get(feed_url, timeout=10, headers=HEADERS)
        if response.status_code >= 400:
            _mark_dead(feed_url, f"HTTP {response.status_code}")
            return items
        feed = feedparser.parse(response.content)
    except Exception as error:
        _mark_dead(feed_url, error)
        return items
    host = source_name(feed_url)
    now = time.time()
    for index, entry in enumerate(feed.entries[:12]):
        title = (entry.get("title") or "").strip()
        link = (entry.get("link") or "").strip()
        if not title or not link:
            continue
        fallback = now - index * 120
        published = entry_published(entry, fallback=fallback)
        if published <= 0:
            published = fallback
        items.append({
            "title": title,
            "link": link,
            "image": extract_image(entry),
            "source": feed_url,
            "source_name": host,
            "feed_category": category,
            "published": published,
        })
    return items


def _rank(items, now):
    fresh = [item for item in items if is_fresh(item, now, MAX_NEWS_AGE_SECONDS)]
    if fresh:
        fresh.sort(key=lambda item: item.get("published") or 0, reverse=True)
        return fresh
    older = [item for item in items if is_fresh(item, now, FALLBACK_NEWS_AGE_SECONDS)]
    older.sort(key=lambda item: item.get("published") or 0, reverse=True)
    return older[:8]


def get_news(categories=None):
    global _EMPTY_LOG_AT
    feeds = _feeds_for(categories)
    cache_key = tuple(sorted({url for _, url in feeds}))
    now = time.time()
    if _CACHE["key"] == cache_key and now - _CACHE["at"] < RSS_CACHE_SECONDS:
        return _rank(_CACHE["items"], now)
    all_news = []
    seen_links = set()
    if not feeds:
        return []
    workers = min(8, len(feeds))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_fetch_one, category, url) for category, url in feeds]
        for future in as_completed(futures):
            for item in future.result():
                if item["link"] in seen_links:
                    continue
                seen_links.add(item["link"])
                all_news.append(item)
    all_news.sort(key=lambda item: item.get("published") or 0, reverse=True)
    _CACHE["key"] = cache_key
    _CACHE["at"] = now
    _CACHE["items"] = all_news
    ranked = _rank(all_news, now)
    if not ranked and now - _EMPTY_LOG_AT > 120:
        _EMPTY_LOG_AT = now
        print(f"⚠️ خبر جدید نیست. فیدها: {len(feeds)} آیتم‌ها: {len(all_news)}")
    return ranked
