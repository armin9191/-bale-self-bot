# ==============================
# Group Manager - Database
# ==============================

import os
import sqlite3
import time


# ==============================
# تنظیمات دیتابیس
# ==============================

DATABASE_NAME = os.getenv(
    "DATABASE_PATH",
    "data/bot.db"
)


# ==============================
# اتصال به دیتابیس
# ==============================

def get_connection():

    db_dir = os.path.dirname(DATABASE_NAME)

    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    connection = sqlite3.connect(
        DATABASE_NAME,
        timeout=30
    )

    connection.row_factory = sqlite3.Row

    return connection


# ==============================
# ساخت دیتابیس
# ==============================

def init_db():

    connection = get_connection()
    cursor = connection.cursor()

    # --------------------------
    # گروه‌ها
    # --------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            group_id INTEGER PRIMARY KEY,
            group_name TEXT,
            enabled INTEGER DEFAULT 1,
            created_at INTEGER,
            updated_at INTEGER
        )
    """)

    # --------------------------
    # کاربران
    # --------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            created_at INTEGER,
            last_active_at INTEGER
        )
    """)

    # --------------------------
    # تنظیمات گروه
    # --------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_settings (
            group_id INTEGER PRIMARY KEY,

            welcome_enabled INTEGER DEFAULT 1,
            anti_spam_enabled INTEGER DEFAULT 0,
            anti_link_enabled INTEGER DEFAULT 0,
            bad_words_enabled INTEGER DEFAULT 0,

            updated_at INTEGER,

            FOREIGN KEY (group_id)
                REFERENCES groups(group_id)
                ON DELETE CASCADE
        )
    """)

    connection.commit()
    connection.close()
