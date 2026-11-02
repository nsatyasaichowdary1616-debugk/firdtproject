"""
TradeLens AI - Database Engine
PostgreSQL compatible schema with built-in zero-config SQLite persistence.
"""
import os
import sqlite3
from typing import Optional, Dict, Any, List
from pathlib import Path

DB_FILE = Path(__file__).resolve().parent.parent / "data" / "tradelens.db"
DB_FILE.parent.mkdir(parents=True, exist_ok=True)

class Database:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = str(db_path or DB_FILE)
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                full_name TEXT NOT NULL,
                is_demo INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # Portfolios table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolios (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                broker_name TEXT DEFAULT 'Zerodha',
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """)

            # Trades table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id TEXT PRIMARY KEY,
                portfolio_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                segment TEXT NOT NULL,
                instrument_type TEXT,
                strike_price REAL,
                option_type TEXT,
                direction TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL NOT NULL,
                open_date TEXT NOT NULL,
                close_date TEXT NOT NULL,
                trade_date TEXT NOT NULL,
                duration_minutes INTEGER DEFAULT 15,
                turnover REAL NOT NULL,
                gross_pnl REAL NOT NULL,
                net_pnl REAL NOT NULL,
                brokerage REAL NOT NULL,
                stt_ctt REAL NOT NULL,
                exchange_charges REAL NOT NULL,
                gst REAL NOT NULL,
                sebi_charges REAL NOT NULL,
                stamp_duty REAL NOT NULL,
                total_charges REAL NOT NULL,
                is_win INTEGER NOT NULL,
                strategy_tag TEXT DEFAULT 'Discretionary',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE
            );
            """)

            # Broker Settings table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS broker_settings (
                user_id TEXT PRIMARY KEY,
                broker_name TEXT DEFAULT 'Zerodha',
                equity_delivery_brokerage REAL DEFAULT 0.0,
                equity_intraday_brokerage REAL DEFAULT 20.0,
                futures_brokerage REAL DEFAULT 20.0,
                options_brokerage REAL DEFAULT 20.0,
                stt_delivery_pct REAL DEFAULT 0.1,
                stt_intraday_pct REAL DEFAULT 0.025,
                stt_futures_pct REAL DEFAULT 0.02,
                stt_options_pct REAL DEFAULT 0.1,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """)

            # AI Reviews table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_reviews (
                id TEXT PRIMARY KEY,
                portfolio_id TEXT NOT NULL,
                review_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE
            );
            """)

            conn.commit()

db = Database()
