# ==========================
# AutoNewsBot Launcher
# Version 1.2
# ==========================

import subprocess
import sys
import time
import os


BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


def start_bot():

    print("🤖 Starting User Bot...")


    subprocess.Popen(
        [
            sys.executable,
            os.path.join(
                BASE_DIR,
                "bot.py"
            )
        ]
    )


def start_news():

    print("📰 Starting News Engine...")


    subprocess.Popen(
        [
            sys.executable,
            os.path.join(
                BASE_DIR,
                "main.py"
            )
        ]
    )


if __name__ == "__main__":

    print(
        "🚀 Starting AutoNewsBot System..."
    )


    start_bot()

    time.sleep(3)


    start_news()


    print(
        "✅ All systems started!"
    )


    while True:

        time.sleep(60)