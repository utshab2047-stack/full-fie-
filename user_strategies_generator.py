"""
backend/user_strategies_generator.py
Generate shared/user_strategies.json from the SQLite DB.

Used by:
 - trading_config_router (after writes)
 - can be run in a background thread periodically
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime

DATABASE_PATH = Path(__file__).parent / "trading_system.db"
STRATEGIES_FILE = Path(__file__).parent.parent / "shared" / "user_strategies.json"
STRATEGIES_TMP = STRATEGIES_FILE.with_suffix(".tmp")

def generate_user_strategies_json() -> bool:
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        users_data = cursor.execute("""
            SELECT 
                u.user_id,
                u.email,
                u.full_name,
                p.total_budget,
                p.risk_tolerance,
                p.selected_categories
            FROM users u
            JOIN user_portfolios p ON u.user_id = p.user_id
        """).fetchall()

        strategies = {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "reload_interval": 30,
            "total_users": len(users_data),
            "users": {}
        }

        for user_row in users_data:
            user_id = user_row["user_id"]
            max_loss_per_trade = (user_row["total_budget"] * user_row["risk_tolerance"]) / 100

            stocks_data = cursor.execute("""
                SELECT * FROM user_stocks
                WHERE user_id = ? AND is_active = 1
                ORDER BY symbol
            """, (user_id,)).fetchall()

            user_stocks = {}
            for stock_row in stocks_data:
                user_stocks[stock_row["symbol"]] = {
                    "category": stock_row["category"],
                    "purchase_price": stock_row["purchase_price"],
                    "target_sell_price": stock_row["target_sell_price"],
                    "current_price": stock_row["current_price"],
                    "purchase_qty": stock_row["purchase_qty"],
                    "selling_qty": stock_row["selling_qty"],
                    "weight": stock_row["weight"],
                    "order_type": stock_row["order_type"],
                    "triggers": {
                        "buy_trigger": stock_row["buy_trigger"],
                        "sell_trigger": stock_row["sell_trigger"],
                        "stop_loss": stock_row["stop_loss"],
                        "partial_fill_enabled": bool(stock_row["partial_fill_enabled"]),
                        "min_fill_qty": stock_row["min_fill_qty"]
                    },
                    "status": "ACTIVE"
                }

            strategies["users"][user_id] = {
                "email": user_row["email"],
                "full_name": user_row["full_name"],
                "portfolio": {
                    "total_budget": user_row["total_budget"],
                    "risk_tolerance": user_row["risk_tolerance"],
                    "max_loss_per_trade": max_loss_per_trade,
                    "auto_stop_loss_percent": 10,
                    "selected_categories": json.loads(user_row["selected_categories"])
                },
                "stocks": user_stocks,
                "total_stocks": len(user_stocks)
            }

        conn.close()

        STRATEGIES_FILE.parent.mkdir(parents=True, exist_ok=True)
        with STRATEGIES_TMP.open("w", encoding="utf-8") as f:
            json.dump(strategies, f, indent=2)
        STRATEGIES_TMP.replace(STRATEGIES_FILE)

        print(f"✅ Generated user_strategies.json - {len(strategies['users'])} users")
        return True

    except Exception as e:
        print(f"❌ Failed to generate user_strategies.json: {e}")
        return False

# Allow importing and calling directly
if __name__ == "__main__":
    generate_user_strategies_json()