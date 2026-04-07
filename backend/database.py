import sqlite3
import os
from auth import create_users_table

DB_PATH = os.path.join(os.path.dirname(__file__), "claims.db")


def get_db():
    """Get a database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the database with fresh schema."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS claims (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id TEXT,
        username TEXT,
        merchant TEXT,
        date TEXT,
        claimed_date TEXT,
        amount REAL,
        currency TEXT,
        purpose TEXT,
        status TEXT,
        explanation TEXT,
        risk_level TEXT DEFAULT 'low',
        policy_snippet TEXT,
        receipt_path TEXT,
        ocr_confidence REAL DEFAULT 0.0,
        raw_text TEXT,
        override_status TEXT,
        override_comment TEXT,
        override_by TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        claim_id INTEGER,
        message TEXT,
        type TEXT DEFAULT 'info',
        is_read INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (claim_id) REFERENCES claims(id)
    )
    """)

    conn.commit()
    conn.close()

    create_users_table()