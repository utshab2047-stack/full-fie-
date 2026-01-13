"""
backend/trading_config_router.py
FastAPI router implementing the trading-config APIs.
Import and include this router into your main_fastapi.py:
    from backend.trading_config_router import router as trading_router
    app.include_router(trading_router, prefix="/api")
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import sqlite3
import json
from pathlib import Path
from datetime import datetime
import threading
import time

# Paths
BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "trading_system.db"

# Import generator
from user_strategies_generator import generate_user_strategies_json

router = APIRouter()

# Ensure DB exists
def get_db():
    conn = sqlite3.connect(DATABASE_PATH, timeout=5, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Enable WAL for this connection
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
    except:
        pass
    return conn

# Pydantic models
class StockConfig(BaseModel):
    symbol: str = Field(..., example="NABIL")
    category: str = Field(..., example="Banking")
    purchase_price: float = Field(..., gt=0, example=1050.0)
    target_sell_price: float = Field(..., gt=0, example=1155.0)
    current_price: Optional[float] = Field(None, example=1105.0)
    purchase_qty: int = Field(..., gt=0, example=10)
    selling_qty: int = Field(..., gt=0, example=10)
    weight: float = Field(default=5.0, ge=0, le=100, example=5.0)
    order_type: str = Field(default="LIMIT", example="LIMIT")
    partial_fill_enabled: bool = Field(default=True)
    min_fill_qty: Optional[int] = Field(None, example=5)

class Portfolio(BaseModel):
    total_budget: float = Field(..., gt=0, example=1000000)
    risk_tolerance: float = Field(..., ge=0, le=100, example=25)
    selected_categories: List[str] = Field(..., example=["Banking", "Hydropower"])

class TradingConfigRequest(BaseModel):
    user_id: str = Field(..., example="user_123")
    email: str = Field(..., example="ram@example.com")
    full_name: Optional[str] = Field(None, example="Ram Thapa")
    portfolio: Portfolio
    stocks: List[StockConfig]

class TradingConfigResponse(BaseModel):
    ok: bool
    message: str
    user_id: str
    total_stocks: int
    generated_file: bool

# Trigger calculation
def calculate_triggers(purchase_price: float, target_sell_price: float, risk_tolerance: float) -> Dict:
    buy_trigger = purchase_price * 0.98
    sell_trigger = target_sell_price * 0.99
    stop_loss = purchase_price * 0.90
    return {
        "buy_trigger": round(buy_trigger, 2),
        "sell_trigger": round(sell_trigger, 2),
        "stop_loss": round(stop_loss, 2)
    }

# Background thread: periodically regenerate strategies (defensive)
def _background_generator_loop(interval=30):
    while True:
        try:
            generate_user_strategies_json()
        except Exception:
            pass
        time.sleep(interval)

_bg_thread_started = False

@router.on_event("startup")
def start_background_generator():
    global _bg_thread_started
    if not _bg_thread_started:
        t = threading.Thread(target=_background_generator_loop, args=(30,), daemon=True)
        t.start()
        _bg_thread_started = True

# Endpoints
@router.post("/user/trading-config", response_model=TradingConfigResponse)
async def save_trading_config(config: TradingConfigRequest):
    try:
        conn = get_db()
        cursor = conn.cursor()

        # 1. Insert/Update user
        cursor.execute("""
            INSERT INTO users (user_id, email, full_name, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                email = excluded.email,
                full_name = excluded.full_name,
                updated_at = excluded.updated_at
        """, (config.user_id, config.email, config.full_name, datetime.now()))

        # 2. Insert/Update portfolio
        cursor.execute("""
            INSERT INTO user_portfolios (user_id, total_budget, risk_tolerance, selected_categories, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                total_budget = excluded.total_budget,
                risk_tolerance = excluded.risk_tolerance,
                selected_categories = excluded.selected_categories,
                updated_at = excluded.updated_at
        """, (
            config.user_id,
            config.portfolio.total_budget,
            config.portfolio.risk_tolerance,
            json.dumps(config.portfolio.selected_categories),
            datetime.now()
        ))

        # 3. Soft-delete existing stocks for user
        cursor.execute("UPDATE user_stocks SET is_active = 0 WHERE user_id = ?", (config.user_id,))

        # 4. Insert/Update each stock
        for stock in config.stocks:
            triggers = calculate_triggers(
                purchase_price=stock.purchase_price,
                target_sell_price=stock.target_sell_price,
                risk_tolerance=config.portfolio.risk_tolerance
            )
            min_fill = stock.min_fill_qty if stock.min_fill_qty is not None else max(1, stock.purchase_qty // 2)
            cursor.execute("""
                INSERT INTO user_stocks (
                    user_id, symbol, category, purchase_price, target_sell_price,
                    current_price, purchase_qty, selling_qty, weight, order_type,
                    partial_fill_enabled, min_fill_qty, buy_trigger, sell_trigger,
                    stop_loss, is_active, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                ON CONFLICT(user_id, symbol) DO UPDATE SET
                    category = excluded.category,
                    purchase_price = excluded.purchase_price,
                    target_sell_price = excluded.target_sell_price,
                    current_price = excluded.current_price,
                    purchase_qty = excluded.purchase_qty,
                    selling_qty = excluded.selling_qty,
                    weight = excluded.weight,
                    order_type = excluded.order_type,
                    partial_fill_enabled = excluded.partial_fill_enabled,
                    min_fill_qty = excluded.min_fill_qty,
                    buy_trigger = excluded.buy_trigger,
                    sell_trigger = excluded.sell_trigger,
                    stop_loss = excluded.stop_loss,
                    is_active = 1,
                    updated_at = excluded.updated_at
            """, (
                config.user_id, stock.symbol, stock.category, stock.purchase_price,
                stock.target_sell_price, stock.current_price, stock.purchase_qty,
                stock.selling_qty, stock.weight, stock.order_type,
                int(stock.partial_fill_enabled), min_fill,
                triggers["buy_trigger"], triggers["sell_trigger"], triggers["stop_loss"],
                datetime.now()
            ))

        conn.commit()
        conn.close()

        # Regenerate strategies JSON
        generated = generate_user_strategies_json()

        return TradingConfigResponse(
            ok=True,
            message="Trading configuration saved successfully",
            user_id=config.user_id,
            total_stocks=len(config.stocks),
            generated_file=generated
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save config: {e}")

@router.get("/user/trading-config")
async def get_trading_config(user_id: str = Query(..., description="User ID")):
    try:
        conn = get_db()
        cursor = conn.cursor()

        user = cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        portfolio = cursor.execute("SELECT * FROM user_portfolios WHERE user_id = ?", (user_id,)).fetchone()
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")

        stocks = cursor.execute("SELECT * FROM user_stocks WHERE user_id = ? AND is_active = 1", (user_id,)).fetchall()
        conn.close()

        return {
            "ok": True,
            "user_id": user["user_id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "portfolio": {
                "total_budget": portfolio["total_budget"],
                "risk_tolerance": portfolio["risk_tolerance"],
                "selected_categories": json.loads(portfolio["selected_categories"])
            },
            "stocks": [dict(s) for s in stocks],
            "total_stocks": len(stocks)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get config: {e}")

from pydantic import BaseModel as _BaseModel
class UpdateStockRequest(_BaseModel):
    user_id: str = Field(..., example="user_123")
    purchase_price: Optional[float] = Field(None, gt=0)
    target_sell_price: Optional[float] = Field(None, gt=0)
    purchase_qty: Optional[int] = Field(None, gt=0)
    selling_qty: Optional[int] = Field(None, gt=0)
    order_type: Optional[str] = Field(None, example="LIMIT")
    partial_fill_enabled: Optional[bool] = None
    min_fill_qty: Optional[int] = None

@router.put("/user/stock/{symbol}")
async def update_stock(symbol: str, update: UpdateStockRequest):
    try:
        conn = get_db()
        cursor = conn.cursor()

        existing = cursor.execute(
            "SELECT * FROM user_stocks WHERE user_id = ? AND symbol = ? AND is_active = 1",
            (update.user_id, symbol)
        ).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail=f"Stock {symbol} not found for user")

        portfolio = cursor.execute(
            "SELECT risk_tolerance FROM user_portfolios WHERE user_id = ?",
            (update.user_id,)
        ).fetchone()

        purchase_price = update.purchase_price if update.purchase_price is not None else existing["purchase_price"]
        target_sell_price = update.target_sell_price if update.target_sell_price is not None else existing["target_sell_price"]

        triggers = calculate_triggers(purchase_price=purchase_price, target_sell_price=target_sell_price, risk_tolerance=portfolio["risk_tolerance"])

        update_fields = []
        update_values = []

        if update.purchase_price is not None:
            update_fields.append("purchase_price = ?")
            update_values.append(update.purchase_price)

        if update.target_sell_price is not None:
            update_fields.append("target_sell_price = ?")
            update_values.append(update.target_sell_price)

        if update.purchase_qty is not None:
            update_fields.append("purchase_qty = ?")
            update_values.append(update.purchase_qty)

        if update.selling_qty is not None:
            update_fields.append("selling_qty = ?")
            update_values.append(update.selling_qty)

        if update.order_type:
            update_fields.append("order_type = ?")
            update_values.append(update.order_type)

        if update.partial_fill_enabled is not None:
            update_fields.append("partial_fill_enabled = ?")
            update_values.append(int(update.partial_fill_enabled))

        if update.min_fill_qty is not None:
            update_fields.append("min_fill_qty = ?")
            update_values.append(update.min_fill_qty)

        update_fields.extend(["buy_trigger = ?", "sell_trigger = ?", "stop_loss = ?", "updated_at = ?"])
        update_values.extend([triggers["buy_trigger"], triggers["sell_trigger"], triggers["stop_loss"], datetime.now()])

        update_values.extend([update.user_id, symbol])

        query = f"UPDATE user_stocks SET {', '.join(update_fields)} WHERE user_id = ? AND symbol = ?"
        cursor.execute(query, update_values)
        conn.commit()
        conn.close()

        # Regenerate JSON
        generate_user_strategies_json()

        return {"ok": True, "message": f"Stock {symbol} updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update stock: {e}")

@router.delete("/user/stock/{symbol}")
async def delete_stock(symbol: str, user_id: str = Query(...)):
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE user_stocks SET is_active = 0, updated_at = ? WHERE user_id = ? AND symbol = ?",
            (datetime.now(), user_id, symbol)
        )

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")

        conn.commit()
        conn.close()

        generate_user_strategies_json()

        return {"ok": True, "message": f"Stock {symbol} removed from portfolio"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete stock: {e}")

@router.get("/admin/active-users")
async def get_active_users():
    try:
        conn = get_db()
        cursor = conn.cursor()

        users = cursor.execute("""
            SELECT 
                u.user_id,
                u.email,
                u.full_name,
                p.total_budget,
                p.risk_tolerance,
                COUNT(s.id) as total_stocks
            FROM users u
            JOIN user_portfolios p ON u.user_id = p.user_id
            LEFT JOIN user_stocks s ON u.user_id = s.user_id AND s.is_active = 1
            GROUP BY u.user_id
            ORDER BY u.updated_at DESC
        """).fetchall()

        conn.close()
        return {
            "ok": True,
            "total_users": len(users),
            "users": [dict(u) for u in users]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get users: {e}")