import sqlite3
from auth import create_users_table

def init_db():
    conn = sqlite3.connect("claims.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS claims (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id TEXT,
        username TEXT,
        merchant TEXT,
        date TEXT,
        amount REAL,
        currency TEXT,
        purpose TEXT,
        status TEXT,
        explanation TEXT
    )
    """)

    conn.commit()
    conn.close()

    create_users_table()