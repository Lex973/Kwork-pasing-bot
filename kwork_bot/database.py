import os
import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.environ.get("DB_PATH", "kwork_bot.db")
        self.conn = sqlite3.connect(db_path)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                title TEXT,
                description TEXT,
                budget TEXT,
                budget_limit TEXT,
                time_left TEXT,
                offers_count TEXT,
                url TEXT,
                last_updated DATETIME
            )
        ''')
        self.conn.commit()

    def order_exists(self, order_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM orders WHERE id = ?", (order_id,))
        return cursor.fetchone() is not None

    def get_order(self, order_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        return cursor.fetchone()

    def save_order(self, order_data):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO orders (id, title, description, budget, budget_limit, time_left, offers_count, url, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            order_data['id'],
            order_data['title'],
            order_data['description'],
            order_data['budget'],
            order_data['budget_limit'],
            order_data['time_left'],
            order_data['offers_count'],
            order_data['url'],
            datetime.now()
        ))
        self.conn.commit()

    def get_last_orders(self, limit=5):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM orders ORDER BY last_updated DESC LIMIT ?", (limit,))
        return cursor.fetchall()

    def clear_history(self):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM orders")
        self.conn.commit()
