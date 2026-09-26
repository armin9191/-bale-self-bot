import requests
import feedparser


# =========================================================
# AutoNewsBot - Source Test
# =========================================================


SOURCES = {

    # =====================================================
    # ⚔️ جنگ
    # =====================================================

    "جنگ - MAIN - جنگاوران": {
        "type": "rss",
        "urls": [
            "https://jangaavaran.ir/feed/",
        ]
    },

    "جنگ - BACKUP - تسنیم": {
        "type": "page",
        "urls": [
            "https://www.tasnimnews.ir/fa/service/11/نظامی-دفاعی-امنیتی",
        ]
    },


    # =====================================================
    # 💻 فناوری و اینترنت
    # =====================================================

    "فناوری - MAIN - دیجیاتو": {
        "type": "rss",
        "urls": [
            "https://digiato.com/feed",
        ]
    },

    "فناوری - BACKUP - زومیت": {
        "type": "rss",
        "urls": [
            "https://www.zoomit.ir/feed/",
        ]
    },


    # =====================================================
    # 💰 اقتصاد
    # =====================================================

    "اقتصاد - MAIN - فردای اقتصاد": {
        "type": "rss",
        "urls": [
            "https://www.fardayeeghtesad.com/rss",
        ]
    },

    "اقتصاد - BACKUP - تجارت نیوز": {
        "type": "rss",
        "urls": [
            "https://tejaratnews.com/feed",
        ]
    },


    # =====================================================
    # ⚽ ورزش
    # =====================================================

    "ورزش - MAIN - ورزش3": {
        "type": "page",
        "urls": [
            "https://www.varzesh3.com/",
        ]
    },

    "ورزش - BACKUP - خبرورزشی": {
        "type": "rss",
        "urls": [
            "https://www.khabarvarzeshi.com/rss",
        ]
    },


    # =====================================================
    # 🌦️ آب و هوا
    # =====================================================

    "آب و هوا - MAIN - SkyWeather": {
        "type": "page",
        "urls": [
            "https://www.skyweather.ir/",
        ]
    },

    "آب و هوا - BACKUP - IA8": {
        "type": "page",
        "urls": [
            "https://ia8.ir/weather",
        ]
    },
}


# =========================================================
# HTTP Request
# =========================================================

def get_page(url):

    try:

        response = requests.get(
            url,
            timeout=15,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/142.0 Safari/537.36"
                )
            }
        )

        return response

    except Exception as e:

        print(
            "❌ CONNECTION ERROR:",
            repr(e)
        )

        return None


# =========================================================
# Test RSS
# =========================================================

def test_rss(url):

    print("-" * 70)
    print("TYPE: RSS")
    print("URL:", url)

    response = get_page(url)

    if response is None:

        return False


    print(
        "HTTP:",
        response.status_code
    )

    print(
        "CONTENT-TYPE:",
        response.headers.get(
            "content-type",
            "unknown"
        )
    )


    if response.status_code != 200:

        print("❌ HTTP FAILED")

        return False


    feed = feedparser.parse(
        response.content
    )


    print(
        "ENTRIES:",
        len(feed.entries)
    )


    if not feed.entries:

        print(
            "❌ RSS سالم نیست یا خبر ندارد"
        )

        return False


    print(
        "TITLE:",
        feed.entries[0].get(
            "title",
            "بدون عنوان"
        )
    )


    print("✅ RSS OK")

    return True


# =========================================================
# Test Normal Page
# =========================================================

def test_page(url):

    print("-" * 70)
    print("TYPE: PAGE")
    print("URL:", url)

    response = get_page(url)

    if response is None:

        return False


    print(
        "HTTP:",
        response.status_code
    )

    print(
        "CONTENT-TYPE:",
        response.headers.get(
            "content-type",
            "unknown"
        )
    )


    if response.status_code != 200:

        print("❌ PAGE FAILED")

        return False


    content = response.text


    print(
        "SIZE:",
        len(content),
        "bytes"
    )


    if len(content) < 500:

        print(
            "⚠️ صفحه خیلی کوچک است"
        )

        return False


    print("✅ PAGE OK")

    return True


# =========================================================
# Test Source
# =========================================================

def test_source(name, data):

    print("\n")
    print("=" * 70)
    print(name)
    print("=" * 70)


    source_type = data.get(
        "type"
    )

    urls = data.get(
        "urls",
        []
    )


    for url in urls:

        if source_type == "rss":

            if test_rss(url):

                return {
                    "name": name,
                    "url": url,
                    "type": "rss",
                    "status": True
                }


        elif source_type == "page":

            if test_page(url):

                return {
                    "name": name,
                    "url": url,
                    "type": "page",
                    "status": True
                }


    return {
        "name": name,
        "url": None,
        "type": source_type,
        "status": False
    }


# =========================================================
# MAIN
# =========================================================

def main():

    print("=" * 70)
    print("🚀 AutoNewsBot SOURCE TEST v2")
    print("=" * 70)


    successful = []
    failed = []


    for name, data in SOURCES.items():

        result = test_source(
            name,
            data
        )


        if result["status"]:

            successful.append(
                result
            )

        else:

            failed.append(
                result
            )


    # =====================================================
    # FINAL RESULT
    # =====================================================

    print("\n\n")

    print("=" * 70)
    print("📊 FINAL RESULT")
    print("=" * 70)


    print("\n✅ منابع سالم:")


    if successful:

        for item in successful:

            print(
                f"  ✅ {item['name']}"
            )

            print(
                f"     TYPE: {item['type']}"
            )

            print(
                f"     URL: {item['url']}"
            )

    else:

        print(
            "  هیچ منبع سالمی پیدا نشد"
        )


    print("\n❌ منابع مشکل‌دار:")


    if failed:

        for item in failed:

            print(
                f"  ❌ {item['name']}"
            )

            print(
                f"     TYPE: {item['type']}"
            )

    else:

        print(
            "  همه منابع سالم هستند"
        )


    print("\n")

    print("=" * 70)
    print("🏁 TEST FINISHED")
    print("=" * 70)


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    main()