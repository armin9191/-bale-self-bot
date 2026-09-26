import json
import os

from config import SENT_NEWS_FILE, USERS_FILE, MAX_SENT_NEWS


def _pick_existing_path(preferred, filename):
    folder = os.path.dirname(preferred)
    candidates = []

    if folder:
        candidates.append(preferred)
        other = "Data" if os.path.basename(folder) == "data" else "data"
        candidates.append(os.path.join(other, filename))
    else:
        candidates.append(preferred)
        candidates.append(os.path.join("data", filename))
        candidates.append(os.path.join("Data", filename))

    for path in candidates:
        if os.path.exists(path):
            return path

    target_folder = folder or "data"
    os.makedirs(target_folder, exist_ok=True)
    return os.path.join(target_folder, filename) if folder else os.path.join("data", filename)


def sent_news_path():
    return _pick_existing_path(SENT_NEWS_FILE, os.path.basename(SENT_NEWS_FILE))


def users_path():
    return _pick_existing_path(USERS_FILE, os.path.basename(USERS_FILE))


def _empty_sent_store():
    return {"channels": {}}


def _normalize_sent_store(raw):
    store = _empty_sent_store()

    if isinstance(raw, dict) and isinstance(raw.get("channels"), dict):
        for channel_id, links in raw["channels"].items():
            if isinstance(links, list):
                store["channels"][str(channel_id)] = [str(item) for item in links]
        return store

    if isinstance(raw, list):
        store["legacy"] = [str(item) for item in raw]
        return store

    return store


def load_sent_store():
    path = sent_news_path()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    if not os.path.exists(path):
        save_sent_store(_empty_sent_store())
        return _empty_sent_store()

    try:
        with open(path, "r", encoding="utf-8") as file:
            return _normalize_sent_store(json.load(file))
    except (json.JSONDecodeError, OSError):
        return _empty_sent_store()


def save_sent_store(store):
    path = sent_news_path()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    clean = _empty_sent_store()
    if isinstance(store, dict):
        channels = store.get("channels", {})
        if isinstance(channels, dict):
            for channel_id, links in channels.items():
                unique = []
                seen = set()
                for link in links or []:
                    link = str(link)
                    if link and link not in seen:
                        seen.add(link)
                        unique.append(link)
                clean["channels"][str(channel_id)] = unique[-MAX_SENT_NEWS:]
        if isinstance(store.get("legacy"), list):
            clean["legacy"] = [str(item) for item in store["legacy"]][-MAX_SENT_NEWS:]

    with open(path, "w", encoding="utf-8") as file:
        json.dump(clean, file, ensure_ascii=False, indent=2)


def is_news_sent(channel_id, link):
    if not channel_id or not link:
        return True

    store = load_sent_store()
    channel_id = str(channel_id)
    link = str(link).strip()
    return link in store.get("channels", {}).get(channel_id, [])


def mark_news_sent(channel_id, link):
    if not channel_id or not link:
        return

    store = load_sent_store()
    channel_id = str(channel_id)
    link = str(link).strip()
    links = store.setdefault("channels", {}).setdefault(channel_id, [])
    if link not in links:
        links.append(link)
        save_sent_store(store)


def load_sent_news():
    store = load_sent_store()
    links = []
    for channel_links in store.get("channels", {}).values():
        links.extend(channel_links)
    links.extend(store.get("legacy", []))
    return list(dict.fromkeys(links))


def save_sent_news(sent_news):
    store = load_sent_store()
    store["legacy"] = list(sent_news)
    save_sent_store(store)


def load_users():
    path = users_path()
    if not os.path.exists(path):
        return {}

    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError) as error:
        print("❌ خطا در خواندن users.json:", error)
        return {}
