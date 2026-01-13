"""
backend/3_signal_engine_v2.py -> Moved to root as 3_signal_engine.py
Real-time personalized signal engine that:
 - reads shared/market_data.json
 - reads shared/user_strategies.json every STRATEGY_RELOAD_INTERVAL seconds
 - writes enriched signals.json and signals_legacy.json (backward-compatible)
 - logs signals to DB (signal_history) and CSV

Run:
    python 3_signal_engine.py
"""
import json
import os
import time
import csv
import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SHARED_DIR = BASE_DIR / "shared"
DATA_FILE = SHARED_DIR / "market_data_live.json"
STRATEGIES_FILE = SHARED_DIR / "user_strategies.json"
SIGNAL_FILE = SHARED_DIR / "signals.json"
SIGNAL_LEGACY = SHARED_DIR / "signals_legacy.json"
LOG_DIR = BASE_DIR / "logs"
CSV_LOG = LOG_DIR / "SIGNALS_HISTORY.csv"
DATABASE_PATH = BASE_DIR / "backend" / "trading_system.db"

LOG_DIR.mkdir(exist_ok=True)
SHARED_DIR.mkdir(exist_ok=True)

if not CSV_LOG.exists():
    with CSV_LOG.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([
            "Time", "User_ID", "Symbol", "Action", "Price", "Qty", "Reason", "Order_Type"
        ])

print("=" * 100)
print("🚀 NEPAL PERSONALIZED SIGNAL ENGINE 2025 - REAL-TIME EDITION (INTEGRATED)")
print("=" * 100)

def safe_load_json(path, default=None):
    if default is None:
        default = {}
    if not path.exists():
        return default
    for _ in range(3):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError, PermissionError):
            time.sleep(0.05)
    print(f"⚠️  WARNING: Corrupted JSON {path.name}, using default")
    return default

def atomic_write(path, data):
    tmp = path.with_suffix(".tmp")
    try:
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=None)
        tmp.replace(path)
    except Exception as e:
        print(f"❌ WRITE FAILED {path.name}: {e}")

def log_signal_to_db(user_id, symbol, action, price, qty, reason):
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("""
            INSERT INTO signal_history (user_id, symbol, action, price, qty, reason, status)
            VALUES (?, ?, ?, ?, ?, ?, 'PENDING')
        """, (user_id, symbol, action, price, qty, reason))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"⚠️  DB LOG FAILED: {e}")

user_strategies = {}
last_strategy_reload = 0
STRATEGY_RELOAD_INTERVAL = 5 # Faster reload for responsiveness
last_heartbeat = time.time()

print("🔄 Starting signal engine loop...\n")

while True:
    try:
        now = time.time()
        now_str = datetime.now().strftime("%H:%M:%S")

        # Reload strategies
        if now - last_strategy_reload >= STRATEGY_RELOAD_INTERVAL:
            user_strategies = safe_load_json(STRATEGIES_FILE, {"users": {}})
            total_users = len(user_strategies.get("users", {}))
            total_stocks = sum(len(u.get("stocks", {})) for u in user_strategies.get("users", {}).values())
            print(f"🔄 {now_str} -> Reloaded strategies: {total_users} users, {total_stocks} stocks")
            last_strategy_reload = now

        # Read market
        market = safe_load_json(DATA_FILE, {"stocks": {}, "timestamp": now_str})
        market_stocks = market.get("stocks", {})

        if not market_stocks:
            if now - last_heartbeat > 15:
                print(f"⏳ {now_str} -> Waiting for market data...")
                last_heartbeat = now
            time.sleep(0.7)
            continue

        all_signals = []
        legacy_signals = []

        for user_id, user_config in user_strategies.get("users", {}).items():
            user_stocks = user_config.get("stocks", {})
            for symbol, stock_config in user_stocks.items():
                if symbol not in market_stocks:
                    continue

                try:
                    current_price = float(market_stocks[symbol].get("ltp", 0))
                except Exception:
                    continue
                if current_price <= 0:
                    continue

                triggers = stock_config.get("triggers", {}) or {}
                buy_trigger = triggers.get("buy_trigger", 0)
                sell_trigger = triggers.get("sell_trigger", 0)
                stop_loss = triggers.get("stop_loss", 0)

                purchase_qty = stock_config.get("purchase_qty", 10)
                selling_qty = stock_config.get("selling_qty", 10)
                order_type = stock_config.get("order_type", "LIMIT")

                partial_fill_enabled = bool(triggers.get("partial_fill_enabled", True))
                min_fill_qty = triggers.get("min_fill_qty") or max(1, purchase_qty // 2)
                
                # Check for WEEKLY strategy tag if needed (Optional but safe)
                # Currently we process ALL active strategies in user_strategies.json

                # BUY
                if buy_trigger and current_price <= buy_trigger:
                    reason = f"Buy trigger hit: {current_price} <= {buy_trigger}"
                    qty_to_buy = purchase_qty
                    signal = {
                        "user_id": user_id,
                        "symbol": symbol,
                        "action": "BUY",
                        "price": round(current_price, 2),
                        "qty": qty_to_buy,
                        "min_qty": min_fill_qty if partial_fill_enabled else qty_to_buy,
                        "order_type": order_type,
                        "partial_fill": partial_fill_enabled,
                        "reason": reason,
                        "timestamp": datetime.now().isoformat()
                    }
                    all_signals.append(signal)
                    legacy_signals.append({
                        "symbol": symbol,
                        "action": "BUY",
                        "price": round(current_price, 2),
                        "qty": qty_to_buy,
                        "reason": reason
                    })
                    print(f"🟢 {now_str} -> BUY  | {user_id[:8]}... | {symbol:8} @ {current_price:7.2f} | Qty: {qty_to_buy} | {reason}")
                    # CSV
                    try:
                        with CSV_LOG.open("a", newline="", encoding="utf-8") as f:
                            csv.writer(f).writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id, symbol, "BUY", round(current_price, 2), qty_to_buy, reason, order_type])
                    except:
                        pass
                    log_signal_to_db(user_id, symbol, "BUY", current_price, qty_to_buy, reason)

                # SELL (target)
                elif sell_trigger and current_price >= sell_trigger:
                    reason = f"Target reached: {current_price} >= {sell_trigger}"
                    qty_to_sell = selling_qty
                    signal = {
                        "user_id": user_id,
                        "symbol": symbol,
                        "action": "SELL",
                        "price": round(current_price, 2),
                        "qty": qty_to_sell,
                        "min_qty": min_fill_qty if partial_fill_enabled else qty_to_sell,
                        "order_type": order_type,
                        "partial_fill": partial_fill_enabled,
                        "reason": reason,
                        "timestamp": datetime.now().isoformat()
                    }
                    all_signals.append(signal)
                    legacy_signals.append({
                        "symbol": symbol,
                        "action": "SELL",
                        "price": round(current_price, 2),
                        "qty": qty_to_sell,
                        "reason": reason
                    })
                    print(f"🔴 {now_str} -> SELL | {user_id[:8]}... | {symbol:8} @ {current_price:7.2f} | Qty: {qty_to_sell} | {reason}")
                    try:
                        with CSV_LOG.open("a", newline="", encoding="utf-8") as f:
                            csv.writer(f).writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id, symbol, "SELL", round(current_price, 2), qty_to_sell, reason, order_type])
                    except:
                        pass
                    log_signal_to_db(user_id, symbol, "SELL", current_price, qty_to_sell, reason)

                # STOP LOSS (force market sell)
                elif stop_loss and current_price <= stop_loss:
                    reason = f"STOP LOSS TRIGGERED: {current_price} <= {stop_loss}"
                    qty_to_sell = selling_qty
                    signal = {
                        "user_id": user_id,
                        "symbol": symbol,
                        "action": "SELL",
                        "price": round(current_price, 2),
                        "qty": qty_to_sell,
                        "min_qty": qty_to_sell,
                        "order_type": "MARKET",
                        "partial_fill": False,
                        "reason": reason,
                        "timestamp": datetime.now().isoformat()
                    }
                    all_signals.append(signal)
                    legacy_signals.append({
                        "symbol": symbol,
                        "action": "SELL",
                        "price": round(current_price, 2),
                        "qty": qty_to_sell,
                        "reason": reason
                    })
                    print(f"⛔ {now_str} -> STOP | {user_id[:8]}... | {symbol:8} @ {current_price:7.2f} | Qty: {qty_to_sell} | {reason}")
                    try:
                        with CSV_LOG.open("a", newline="", encoding="utf-8") as f:
                            csv.writer(f).writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id, symbol, "SELL", round(current_price, 2), qty_to_sell, reason, "MARKET"])
                    except:
                        pass
                    log_signal_to_db(user_id, symbol, "SELL", current_price, qty_to_sell, reason)

        # Write signals files
        if all_signals:
            atomic_write(SIGNAL_FILE, all_signals)
            # Write legacy adapter
            atomic_write(SIGNAL_LEGACY, legacy_signals)
            print(f"📤 {now_str} -> {len(all_signals)} SIGNAL(S) WRITTEN\n")
        else:
            # Remove existing to avoid stale signals
            if SIGNAL_FILE.exists():
                try: SIGNAL_FILE.unlink()
                except: pass
            if SIGNAL_LEGACY.exists():
                try: SIGNAL_LEGACY.unlink()
                except: pass

        if now - last_heartbeat > 12:
            print(f"💓 {now_str} -> Market stocks: {len(market_stocks)} | Users: {len(user_strategies.get('users', {}))} | Alive")
            last_heartbeat = now

    except Exception as e:
        print(f"⚠️  {datetime.now().strftime('%H:%M:%S')} -> RECOVERED FROM ERROR: {e}")

    time.sleep(0.7)
