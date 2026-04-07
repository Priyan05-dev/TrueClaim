import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "claims.db")


def create_users_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT,
        role TEXT,
        company_id TEXT
    )
    """)

    conn.commit()
    conn.close()


def register_user(username, password, role, company_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO users (username, password, role, company_id)
    VALUES (?, ?, ?, ?)
    """, (username, password, role, company_id))

    conn.commit()
    conn.close()


def login_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM users WHERE username=? AND password=?
    """, (username, password))

    user = cursor.fetchone()
    conn.close()

    return user