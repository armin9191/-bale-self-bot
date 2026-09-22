# ==============================
# Group Manager - Database
# ==============================

import os
import sqlite3
import time

from config import DATABASE_NAME


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
# ساخت جداول
# ==============================

def init_db():

    connection = get_connection()
    cursor = connection.cursor()

    # ==========================
    # گروه‌ها
    # ==========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            group_id INTEGER PRIMARY KEY,
            group_name TEXT,
            enabled INTEGER DEFAULT 1,
            created_at INTEGER,
            updated_at INTEGER
        )
    """)

    # ==========================
    # کاربران
    # ==========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            created_at INTEGER,
            last_active_at INTEGER
        )
    """)

    # ==========================
    # تنظیمات گروه
    # ==========================

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


# ==============================
# ثبت / بروزرسانی گروه
# ==============================

def save_group(group_id, group_name):

    connection = get_connection()
    cursor = connection.cursor()

    now = int(time.time())

    cursor.execute("""
        INSERT INTO groups (
            group_id,
            group_name,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?)

        ON CONFLICT(group_id)
        DO UPDATE SET
            group_name = excluded.group_name,
            updated_at = excluded.updated_at
    """, (
        group_id,
        group_name,
        now,
        now
    ))

    # ==========================
    # ساخت تنظیمات اولیه گروه
    # ==========================

    cursor.execute("""
        INSERT OR IGNORE INTO group_settings (
            group_id,
            updated_at
        )
        VALUES (?, ?)
    """, (
        group_id,
        now
    ))

    connection.commit()
    connection.close()


# ==============================
# ثبت / بروزرسانی کاربر
# ==============================

def save_user(user_id, username, first_name):

    connection = get_connection()
    cursor = connection.cursor()

    now = int(time.time())

    cursor.execute("""
        INSERT INTO users (
            user_id,
            username,
            first_name,
            created_at,
            last_active_at
        )
        VALUES (?, ?, ?, ?, ?)

        ON CONFLICT(user_id)
        DO UPDATE SET
            username = excluded.username,
            first_name = excluded.first_name,
            last_active_at = excluded.last_active_at
    """, (
        user_id,
        username,
        first_name,
        now,
        now
    ))

    connection.commit()
    connection.close()
