import sqlite3
from contextlib import contextmanager
from config import DATABASE_PATH
from typing import List, Dict, Optional, Tuple

class MarketDB:
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_PATH)
        self.cursor = self.conn.cursor()
        self._initialize_tables()

    @contextmanager
    def connection(self):
        yield self.conn
        self.conn.commit()

    def _initialize_tables(self):
        self.cursor.executescript("""
            CREATE TABLE IF NOT EXISTS tracked_stocks (
                user_id INTEGER,
                ticker TEXT,
                exchange TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(user_id, ticker)
            );

            CREATE TABLE IF NOT EXISTS subscriptions (
                user_id INTEGER PRIMARY KEY,
                enabled BOOLEAN DEFAULT 1,
                last_checked TIMESTAMP
            );
        """)
        self.conn.commit()

    def add_ticker(self, user_id: int, ticker: str, exchange: str = "") -> bool:
        try:
            with self.connection():
                self.cursor.execute(
                    "INSERT OR IGNORE INTO tracked_stocks (user_id, ticker, exchange) VALUES (?, ?, ?)",
                    (user_id, ticker.upper(), exchange.upper())
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def remove_ticker(self, user_id: int, ticker: str) -> bool:
        with self.connection():
            self.cursor.execute(
                "DELETE FROM tracked_stocks WHERE user_id = ? AND ticker = ?",
                (user_id, ticker.upper())
            )
        return self.cursor.rowcount > 0

    def get_subscribers(self) -> List[Tuple[int, str, str]]:
        with self.connection():
            self.cursor.execute("""
                SELECT t.user_id, t.ticker, t.exchange 
                FROM tracked_stocks t
                JOIN subscriptions s ON t.user_id = s.user_id
                WHERE s.enabled = 1
            """)
        return self.cursor.fetchall()

    def toggle_subscription(self, user_id: int, enabled: bool) -> bool:
        with self.connection():
            self.cursor.execute(
                "INSERT OR REPLACE INTO subscriptions (user_id, enabled, last_checked) VALUES (?, ?, datetime('now'))",
                (user_id, int(enabled))
            )
        return True

    def get_user_tracking(self, user_id: int) -> List[Tuple[str, str]]:
        with self.connection():
            self.cursor.execute(
                "SELECT ticker, exchange FROM tracked_stocks WHERE user_id = ?",
                (user_id,)
            )
        return self.cursor.fetchall()

    def is_subscribed(self, user_id: int) -> bool:
        with self.connection():
            self.cursor.execute("SELECT enabled FROM subscriptions WHERE user_id = ?", (user_id,))
            row = self.cursor.fetchone()
        return bool(row and row[0] == 1) if row else False
