import sqlite3

def init_db():
    conn = sqlite3.connect("claims.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS claims (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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