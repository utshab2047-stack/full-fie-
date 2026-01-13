"""
backend/database_init.py
Initialize SQLite database with all required tables.
Run once:  python database_init.py
"""
import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).parent / "trading_system.db"

def init_database():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Enable WAL mode for better concurrency
    cursor. execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA foreign_keys=ON;")
    
    # Table 1: Users
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            full_name TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Table 2: User Portfolios
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_portfolios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL UNIQUE,
            total_budget REAL NOT NULL CHECK(total_budget > 0),
            risk_tolerance REAL NOT NULL CHECK(risk_tolerance >= 0 AND risk_tolerance <= 100),
            selected_categories TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
    """)
    
    # Table 3: User Stocks
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            category TEXT NOT NULL,
            purchase_price REAL NOT NULL CHECK(purchase_price > 0),
            target_sell_price REAL NOT NULL CHECK(target_sell_price > 0),
            current_price REAL,
            purchase_qty INTEGER NOT NULL CHECK(purchase_qty > 0),
            selling_qty INTEGER NOT NULL CHECK(selling_qty > 0),
            weight REAL DEFAULT 0.0 CHECK(weight >= 0 AND weight <= 100),
            order_type TEXT DEFAULT 'LIMIT' CHECK(order_type IN ('LIMIT', 'MARKET')),
            partial_fill_enabled BOOLEAN DEFAULT TRUE,
            min_fill_qty INTEGER,
            buy_trigger REAL,
            sell_trigger REAL,
            stop_loss REAL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            UNIQUE(user_id, symbol)
        )
    """)
    
    # Table 4: Signal History
    cursor. execute("""
        CREATE TABLE IF NOT EXISTS signal_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            action TEXT NOT NULL CHECK(action IN ('BUY', 'SELL')),
            price REAL NOT NULL,
            qty INTEGER NOT NULL,
            reason TEXT,
            status TEXT DEFAULT 'PENDING' CHECK(status IN ('PENDING', 'EXECUTED', 'FAILED', 'PARTIAL')),
            executed_qty INTEGER DEFAULT 0,
            executed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
    """)
    
    # Table 5: Order Executions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_executions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            signal_id INTEGER NOT NULL,
            user_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            action TEXT NOT NULL,
            requested_qty INTEGER NOT NULL,
            executed_qty INTEGER NOT NULL,
            remaining_qty INTEGER NOT NULL,
            avg_price REAL NOT NULL,
            status TEXT DEFAULT 'COMPLETED' CHECK(status IN ('COMPLETED', 'PARTIAL', 'FAILED')),
            execution_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (signal_id) REFERENCES signal_history(id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_stocks_active ON user_stocks(user_id, is_active)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_signal_history_user ON signal_history(user_id, created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_order_executions_signal ON order_executions(signal_id)")
    
    conn.commit()
    conn.close()
    
    print("✅ Database initialized successfully")
    print(f"📁 Location: {DATABASE_PATH}")

if __name__ == "__main__": 
    init_database()