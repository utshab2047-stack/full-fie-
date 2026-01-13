"""
backend/main_fastapi.py
Main FastAPI application with all routes including trading config and email tracking. 
Run:  uvicorn backend.main_fastapi:app --host 0.0.0.0 --port 8002 --reload
"""
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pathlib import Path
from typing import List, Optional, Dict, Any
import json
import time
import logging
import hashlib
import uuid
import sqlite3
from datetime import datetime

# ------------------------------------------------------------------
# App & Middleware
# ------------------------------------------------------------------

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("nepse-api")

app = FastAPI(title="NEPSE Empire API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# Paths & Storage
# ------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
SHARED_DIR = BASE_DIR.parent / "shared"
EXECUTED_DIR = SHARED_DIR / "executed"
STATUS_DIR = SHARED_DIR / "status"
LOGS_DIR = SHARED_DIR / "logs"

MARKET_FILE = SHARED_DIR / "market_data.json"
SIGNALS_FILE = SHARED_DIR / "signals.json"
DATABASE_PATH = BASE_DIR / "trading_system.db"

for d in (SHARED_DIR, EXECUTED_DIR, STATUS_DIR, LOGS_DIR):
    d.mkdir(parents=True, exist_ok=True)

DP_HOLDINGS_FILE = SHARED_DIR / "dp_holdings.json"
USERS_FILE = SHARED_DIR / "users.json"

# ------------------------------------------------------------------
# Database Setup
# ------------------------------------------------------------------

def init_db():
    """Initialize SQLite database with required tables."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            full_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # User portfolios table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_portfolios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL,
            total_budget REAL NOT NULL,
            risk_tolerance REAL NOT NULL,
            selected_categories TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)
    
    # User stocks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            category TEXT,
            purchase_price REAL NOT NULL,
            target_sell_price REAL NOT NULL,
            current_price REAL,
            purchase_qty INTEGER NOT NULL,
            selling_qty INTEGER NOT NULL,
            weight REAL DEFAULT 5.0,
            order_type TEXT DEFAULT 'LIMIT',
            partial_fill_enabled INTEGER DEFAULT 1,
            min_fill_qty INTEGER,
            buy_trigger REAL,
            sell_trigger REAL,
            stop_loss REAL,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            UNIQUE(user_id, symbol)
        )
    """)
    
    # Signal history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS signal_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            action TEXT NOT NULL,
            price REAL NOT NULL,
            qty INTEGER NOT NULL,
            reason TEXT,
            status TEXT DEFAULT 'PENDING',
            executor TEXT DEFAULT 'SYSTEM',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Email/Notification history table (NEW)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient_email TEXT NOT NULL,
            subject TEXT NOT NULL,
            body TEXT,
            email_type TEXT DEFAULT 'NOTIFICATION',
            status TEXT DEFAULT 'SENT',
            related_user_id TEXT,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # System logs table (ensure exists)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_level TEXT DEFAULT 'INFO',
            category TEXT DEFAULT 'GENERAL',
            message TEXT NOT NULL,
            details TEXT,
            user_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# ------------------------------------------------------------------
# Pydantic Models for Trading Configuration
# ------------------------------------------------------------------

class StockStrategy(BaseModel):
    id: int | str
    name: str
    category: str
    purchasePrice: float
    targetSellPrice: float
    currentPrice: float
    purchase_qty: Optional[int] = 10 # Default quantity if not specified

class PortfolioConfig(BaseModel):
    totalBudget: float
    riskTolerance: float
    selectedCategories: List[str]
    stocks: List[StockStrategy]

class UserStrategyPayload(BaseModel):
    user_id: str
    period: str
    portfolio: PortfolioConfig

# Initialize database on startup
init_db()

# ------------------------------------------------------------------
# Auth Helpers & Models
# ------------------------------------------------------------------

class UserRegister(BaseModel):
    email: str
    password: str
    phone: Optional[str] = None
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class VerifyEmail(BaseModel):
    email: str
    code: str

def get_users():
    if not USERS_FILE.exists():
        return {}
    try:
        return json.loads(USERS_FILE.read_text(encoding="utf-8"))
    except:
        return {}

@app.get("/api/market")
def get_market_data():
    """Serve live market data from shared JSON file."""
    try:
        if not MARKET_FILE.exists():
            return {"timestamp": "", "stocks": {}}
        return json.loads(MARKET_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        log.error(f"Failed to read market data: {e}")
        return {"error": str(e)}

def save_users(users):
    USERS_FILE.write_text(json.dumps(users, indent=2), encoding="utf-8")

def hash_password(password:  str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def get_db():
    conn = sqlite3.connect(DATABASE_PATH, timeout=5, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

# ------------------------------------------------------------------
# Calendar & Status Logic
# ------------------------------------------------------------------
import requests
import re

def get_nepali_date_real():
    """Scrapes HamroPatro for real-time Nepali Date."""
    try:
        url = "https://www.hamropatro.com/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=3)
        if response.status_code == 200:
            html = response.text
            # Heuristic search
            match = re.search(r'<div class="date">\s*(\d{4})\s*<br>\s*<span>(.*?)</span>\s*(\d{1,2})', html)
            
            # fallback to specific class search
            day_match = re.search(r'<span class="nep">(\d+)</span>', html)
            month_match = re.search(r'<span class="nep">([a-zA-Z]+)</span>', html)
            year_match = re.search(r'<span class="nep">(\d{4})</span>', html)
            
            if day_match and month_match and year_match:
                return f"{year_match.group(1)} {month_match.group(1)} {day_match.group(1)}"
            
    except Exception as e:
        log.error(f"Calendar scrape failed: {e}")
    
    return "Nepali Date Unavailable"

def get_market_status():
    now = datetime.now()
    wd = now.weekday() # 0=Mon, ... 6=Sun
    # NEPSE: Sun(6) to Thu(3)
    
    # Python: Mon=0, Tue=1, Wed=2, Thu=3, Fri=4, Sat=5, Sun=6
    is_weekend = (wd == 4 or wd == 5) # Fri, Sat closed
    
    current_hour = now.hour
    status = "CLOSED"
    
    # Logic
    if is_weekend:
        status = "CLOSED (Weekend)"
    elif 11 <= current_hour < 15:
        status = "OPEN"
    elif 10 <= current_hour < 11:
        status = "PRE-OPEN"
    else:
        status = "CLOSED"

    # Get Date
    nep_date = get_nepali_date_real()
    if "Unavailable" in nep_date:
        # Fallback to English
        nep_date = now.strftime("%Y %B %d (AD)")

    return {
        "status": status,
        "nepali_date": nep_date,
        "english_date": now.strftime("%Y-%m-%d, %A"),
        "is_open": (status == "OPEN" or status == "PRE-OPEN")
    }

@app.get("/api/calendar")
def api_calendar():
    return get_market_status()

# ------------------------------------------------------------------
# Email & Logging Functions (NEW)
# ------------------------------------------------------------------

def log_to_db(level:  str, category: str, message: str, details: str = None, user_id:  str = None):
    """Log a message to the system_logs table."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO system_logs (log_level, category, message, details, user_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (level, category, message, details, user_id, datetime.now().isoformat()))
        conn.commit()
        conn.close()
    except Exception as e: 
        log.error(f"Failed to log to DB: {e}")

def log_email_to_db(recipient:  str, subject: str, body: str, email_type: str = "NOTIFICATION", 
                    status: str = "SENT", user_id: str = None, metadata: dict = None):
    """Log an email to the email_history table."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO email_history (recipient_email, subject, body, email_type, status, related_user_id, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            recipient, 
            subject, 
            body, 
            email_type, 
            status, 
            user_id, 
            json.dumps(metadata) if metadata else None,
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        log.error(f"Failed to log email to DB: {e}")
        return False

def send_email(to_email: str, subject: str, body:  str, email_type: str = "NOTIFICATION", user_id: str = None):
    """Send email and log it to history."""
    print(f"\n[EMAIL SIMULATION] -------------------------")
    print(f"To: {to_email}")
    print(f"Subject: {subject}")
    print(f"Body:  {body}")
    print(f"--------------------------------------------\n")
    
    # Log to email_history table
    log_email_to_db(
        recipient=to_email,
        subject=subject,
        body=body,
        email_type=email_type,
        status="SENT",
        user_id=user_id,
        metadata={"sent_at": datetime.now().isoformat()}
    )
    
    # Log to system_logs table
    log_to_db(
        level="INFO",
        category="EMAIL",
        message=f"Email sent to {to_email}:  {subject}",
        details=body[:200] if body else None,
        user_id=user_id
    )
    
    return True

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        log.warning("Failed to read %s: %s", path, e)
        return None

def executed_files():
    files = list(EXECUTED_DIR.glob("done_*.json"))
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)

def trade_timestamp(t: Dict[str, Any]) -> float:
    for k in ("ts", "timestamp", "time", "executed_at", "created_at"):
        if k in t:
            try:
                if isinstance(t[k], str):
                    # Parse ISO format datetime
                    dt = datetime.fromisoformat(t[k]. replace('Z', '+00:00'))
                    return dt.timestamp()
                return float(t[k])
            except Exception: 
                pass
    return 0.0

# ------------------------------------------------------------------
# Trading Config Models
# ------------------------------------------------------------------

class StockConfig(BaseModel):
    symbol: str = Field(..., example="NABIL")
    category: str = Field(..., example="Banking")
    purchase_price: float = Field(..., gt=0, example=1050.0)
    target_sell_price: float = Field(... , gt=0, example=1155.0)
    current_price: Optional[float] = Field(None, example=1105.0)
    purchase_qty: int = Field(..., gt=0, example=10)
    selling_qty: int = Field(..., gt=0, example=10)
    weight: float = Field(default=5.0, ge=0, le=100, example=5.0)
    order_type: str = Field(default="LIMIT", example="LIMIT")
    partial_fill_enabled: bool = Field(default=True)
    min_fill_qty: Optional[int] = Field(None, example=5)

class Portfolio(BaseModel):
    total_budget:  float = Field(..., gt=0, example=1000000)
    risk_tolerance: float = Field(... , ge=0, le=100, example=25)
    selected_categories: List[str] = Field(... , example=["Banking", "Hydropower"])

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

# ------------------------------------------------------------------
# User Strategies Generator
# ------------------------------------------------------------------

def generate_user_strategies_json() -> bool:
    """Generate shared/user_strategies.json from the SQLite DB."""
    try:
        conn = get_db()
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
            try:
                selected = json.loads(user_row["selected_categories"])
            except Exception:
                selected = []
            max_loss_per_trade = (user_row["total_budget"] * user_row["risk_tolerance"]) / 100

            stocks_data = cursor.execute("""
                SELECT * FROM user_stocks
                WHERE user_id = ?  AND is_active = 1
                ORDER BY symbol
            """, (user_id,)).fetchall()

            user_stocks = {}
            for stock_row in stocks_data:
                user_stocks[stock_row["symbol"]] = {
                    "category": stock_row["category"],
                    "purchase_price":  stock_row["purchase_price"],
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
                    "selected_categories": selected
                },
                "stocks": user_stocks,
                "total_stocks":  len(user_stocks)
            }

        conn.close()

        # Write to the exact filename 3_signal_engine expects
        STRATEGIES_FILE = SHARED_DIR / "user_strategies.json"
        STRATEGIES_TMP = STRATEGIES_FILE.with_suffix(".tmp")
        
        with STRATEGIES_TMP.open("w", encoding="utf-8") as f:
            json.dump(strategies, f, indent=2)
        STRATEGIES_TMP.replace(STRATEGIES_FILE)

        log.info(f"Generated user_strategies.json - {len(strategies['users'])} users")
        log_to_db("INFO", "SYSTEM", f"Generated user_strategies.json with {len(strategies['users'])} users")
        return True

    except Exception as e: 
        log.error(f"Failed to generate user_strategies.json: {e}")
        log_to_db("ERROR", "SYSTEM", f"Failed to generate user_strategies.json: {e}")
        return False

def calculate_triggers(purchase_price: float, target_sell_price: float, risk_tolerance: float) -> Dict: 
    buy_trigger = purchase_price * 0.98
    sell_trigger = target_sell_price * 0.99
    stop_loss = purchase_price * 0.90
    return {
        "buy_trigger": round(buy_trigger, 2),
        "sell_trigger":  round(sell_trigger, 2),
        "stop_loss": round(stop_loss, 2)
    }

# ------------------------------------------------------------------
# Auth Endpoints
# ------------------------------------------------------------------

@app.post("/api/auth/register")
def register(user: UserRegister):
    users = get_users()
    if user.email in users: 
        log_to_db("WARNING", "AUTH", f"Registration attempt for existing user: {user.email}")
        return {"ok": False, "error": "User already exists"}
    
    code = str(uuid.uuid4().int)[:6]
    user_id = hashlib.md5(user.email.encode()).hexdigest()[:12]
    
    users[user.email] = {
        "user_id": user_id,
        "password": hash_password(user.password),
        "phone": user.phone,
        "full_name": user.full_name,
        "verified": False,
        "verification_code": code,
        "created_at": time.time()
    }
    save_users(users)
    
    # Persist user to DB (so generator can see users once they have portfolios)
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT OR IGNORE INTO users (user_id, email, full_name, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, user.email, user.full_name, datetime.now().isoformat(), datetime.now().isoformat()))
        conn.commit()
        conn.close()
    except Exception as e:
        log.error(f"Failed to persist user to DB on register: {e}")
    
    # Send verification email (this now logs to DB)
    send_email(
        to_email=user.email, 
        subject="Verify your PMS Account", 
        body=f"Your verification code is: {code}",
        email_type="VERIFICATION",
        user_id=user_id
    )
    
    log_to_db("INFO", "AUTH", f"New user registered: {user.email}", user_id=user_id)
    
    return {"ok": True, "message": "Verification code sent to email"}

@app.post("/api/auth/login")
def login(creds: UserLogin):
    users = get_users()
    u = users.get(creds.email)
    if not u: 
        log_to_db("WARNING", "AUTH", f"Login attempt for non-existent user: {creds.email}")
        return {"ok":  False, "error":  "Invalid credentials"}
    
    if u["password"] != hash_password(creds.password):
        log_to_db("WARNING", "AUTH", f"Failed login attempt for:  {creds.email}")
        return {"ok": False, "error": "Invalid credentials"}
        
    if not u.get("verified", False):
        return {"ok": False, "error": "Email not verified", "needs_verification": True}
    
    user_id = u.get("user_id") or hashlib.md5(creds.email.encode()).hexdigest()[:12]
    
    log_to_db("INFO", "AUTH", f"User logged in: {creds.email}", user_id=user_id)
    
    # Send login notification email
    send_email(
        to_email=creds.email,
        subject="Login Notification - NEPSE Empire",
        body=f"You have successfully logged in at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        email_type="LOGIN_NOTIFICATION",
        user_id=user_id
    )
    
    return {
        "ok":  True, 
        "token": f"token-{user_id}", 
        "user":  {
            "email": creds.email, 
            "name": u.get("full_name"),
            "user_id": user_id
        }
    }

@app.post("/api/auth/verify")
def verify(data: VerifyEmail):
    users = get_users()
    u = users.get(data.email)
    if not u:
        return {"ok": False, "error": "User not found"}
    
    user_id = u.get("user_id") or hashlib.md5(data.email.encode()).hexdigest()[:12]
    
    if u.get("verification_code") == data.code:
        u["verified"] = True
        save_users(users)
        
        log_to_db("INFO", "AUTH", f"Email verified for: {data.email}", user_id=user_id)
        
        # Send welcome email
        send_email(
            to_email=data.email,
            subject="Welcome to NEPSE Empire! ",
            body=f"Congratulations! Your account has been verified.  You can now start trading.",
            email_type="WELCOME",
            user_id=user_id
        )
        
        return {"ok":  True, "message":  "Verified successfully"}
    
    log_to_db("WARNING", "AUTH", f"Invalid verification code attempt for: {data.email}", user_id=user_id)
    return {"ok": False, "error": "Invalid code"}

# ------------------------------------------------------------------
# History & Logs Endpoints (NEW/UPDATED)
# ------------------------------------------------------------------

@app.get("/api/history")
def api_history(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    since: Optional[float] = None,
    sort: str = Query("desc", pattern="^(asc|desc)$"),
    include_emails: bool = Query(True, description="Include email history"),
    include_signals: bool = Query(True, description="Include signal history"),
):
    """Get combined history of trades, signals, and emails."""
    trades:  List[Dict[str, Any]] = []
    
    # Get executed trades from files
    for f in executed_files():
        data = load_json(f)
        if isinstance(data, list):
            for item in data:
                item["source"] = "TRADE"
            trades.extend(data)
        elif isinstance(data, dict):
            data["source"] = "TRADE"
            trades.append(data)
    
    # Get signal history from DB
    if include_signals: 
        try:
            conn = get_db()
            cursor = conn.cursor()
            signals = cursor.execute("""
                SELECT 
                    id, user_id, symbol, action, price, qty, reason, status, executor, created_at
                FROM signal_history 
                ORDER BY created_at DESC
                LIMIT 500
            """).fetchall()
            
            for s in signals:
                trades.append({
                    "id": s["id"],
                    "symbol": s["symbol"],
                    "action": s["action"],
                    "price": s["price"],
                    "qty": s["qty"],
                    "reason": s["reason"],
                    "status": s["status"],
                    "executor": s["executor"] or "SYSTEM",
                    "created_at":  s["created_at"],
                    "source": "SIGNAL"
                })
            conn.close()
        except Exception as e: 
            log.error(f"Failed to get signal history: {e}")
    
    # Get email history from DB
    if include_emails: 
        try:
            conn = get_db()
            cursor = conn.cursor()
            emails = cursor.execute("""
                SELECT 
                    id, recipient_email, subject, email_type, status, related_user_id, created_at
                FROM email_history 
                ORDER BY created_at DESC
                LIMIT 500
            """).fetchall()
            
            for e in emails: 
                trades.append({
                    "id": e["id"],
                    "symbol": e["email_type"],
                    "action": "EMAIL",
                    "price": 0,
                    "qty":  1,
                    "reason": f"To:  {e['recipient_email']} - {e['subject']}",
                    "status": e["status"],
                    "executor": "EMAIL_SERVICE",
                    "created_at": e["created_at"],
                    "source": "EMAIL"
                })
            conn.close()
        except Exception as e: 
            log.error(f"Failed to get email history: {e}")
    
    # Filter by timestamp if provided
    if since is not None:
        trades = [t for t in trades if trade_timestamp(t) >= since]
    
    # Sort
    trades.sort(key=trade_timestamp, reverse=(sort == "desc"))
    
    total = len(trades)
    sliced = trades[offset:  offset + limit]
    
    return {
        "total": total,
        "count": len(sliced),
        "offset": offset,
        "limit": limit,
        "data": sliced,
    }

@app.get("/api/emails")
def api_emails(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    email_type: Optional[str] = None,
):
    """Get email history."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        query = "SELECT * FROM email_history"
        params = []
        
        if email_type: 
            query += " WHERE email_type = ?"
            params.append(email_type)
        
        query += " ORDER BY created_at DESC LIMIT ?  OFFSET ?"
        params.extend([limit, offset])
        
        emails = cursor.execute(query, params).fetchall()
        total = cursor.execute("SELECT COUNT(*) FROM email_history").fetchone()[0]
        conn.close()
        
        return {
            "ok": True,
            "total": total,
            "count":  len(emails),
            "data": [dict(e) for e in emails]
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/logs")
def api_logs(
    limit: int = Query(200, ge=1, le=5000),
    category: Optional[str] = None,
    level: Optional[str] = None,
):
    """Get system logs from database and log files."""
    output = []
    
    # Get logs from database
    try: 
        conn = get_db()
        cursor = conn.cursor()
        
        query = "SELECT * FROM system_logs"
        conditions = []
        params = []
        
        if category: 
            conditions.append("category = ?")
            params.append(category)
        if level:
            conditions.append("log_level = ?")
            params.append(level)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        db_logs = cursor.execute(query, params).fetchall()
        conn.close()
        
        output.append({
            "source": "database",
            "file": "system_logs",
            "lines": [
                f"[{log['created_at']}] [{log['log_level']}] [{log['category']}] {log['message']}"
                for log in db_logs
            ]
        })
    except Exception as e: 
        log.error(f"Failed to get DB logs: {e}")
    
    # Get logs from files
    for lf in sorted(LOGS_DIR.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            lines = lf.read_text(encoding="utf-8", errors="ignore").splitlines()
            output.append({
                "source": "file",
                "file": lf.name,
                "lines": lines[-limit: ],
            })
        except Exception as e:
            log.error(f"Failed to read log file {lf}:  {e}")
    
    return {"files": output}

@app.get("/api/logs/summary")
def api_logs_summary():
    """Get summary of logs by category and level."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Count by level
        level_counts = cursor.execute("""
            SELECT log_level, COUNT(*) as count 
            FROM system_logs 
            GROUP BY log_level
        """).fetchall()
        
        # Count by category
        category_counts = cursor.execute("""
            SELECT category, COUNT(*) as count 
            FROM system_logs 
            GROUP BY category
        """).fetchall()
        
        # Recent activity (last 24 hours)
        recent_count = cursor.execute("""
            SELECT COUNT(*) FROM system_logs 
            WHERE created_at > datetime('now', '-1 day')
        """).fetchone()[0]
        
        # Email stats
        email_stats = cursor.execute("""
            SELECT email_type, COUNT(*) as count 
            FROM email_history 
            GROUP BY email_type
        """).fetchall()
        
        conn.close()
        
        return {
            "ok": True,
            "by_level": {row["log_level"]: row["count"] for row in level_counts},
            "by_category": {row["category"]:  row["count"] for row in category_counts},
            "recent_24h": recent_count,
            "email_stats": {row["email_type"]: row["count"] for row in email_stats}
        }
    except Exception as e: 
        return {"ok": False, "error": str(e)}

# ------------------------------------------------------------------
# Trading Config Endpoints (DB-backed)
# ------------------------------------------------------------------

@app.post("/api/user/trading-config", response_model=TradingConfigResponse)
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

        # 3.  Soft-delete existing stocks for user
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
        
        # Log the config save
        log_to_db("INFO", "CONFIG", f"Trading config saved for user {config.user_id} with {len(config.stocks)} stocks", user_id=config.user_id)
        
        # Send confirmation email
        send_email(
            to_email=config.email,
            subject="Trading Configuration Updated - NEPSE Empire",
            body=f"Your trading configuration has been updated with {len(config.stocks)} stocks.",
            email_type="CONFIG_UPDATE",
            user_id=config.user_id
        )

        return TradingConfigResponse(
            ok=True,
            message="Trading configuration saved successfully",
            user_id=config.user_id,
            total_stocks=len(config.stocks),
            generated_file=generated
        )
    except Exception as e:
        log.error(f"Failed to save config: {e}")
        log_to_db("ERROR", "CONFIG", f"Failed to save config: {e}", user_id=config.user_id)
        return TradingConfigResponse(
            ok=False,
            message=f"Failed to save config: {e}",
            user_id=config.user_id,
            total_stocks=0,
            generated_file=False
        )

@app.get("/api/user/trading-config")
async def get_trading_config(user_id: str = Query(..., description="User ID")):
    try:
        conn = get_db()
        cursor = conn.cursor()

        user = cursor.execute("SELECT * FROM users WHERE user_id = ? ", (user_id,)).fetchone()
        if not user:
            return {"ok": False, "error": "User not found"}

        portfolio = cursor.execute("SELECT * FROM user_portfolios WHERE user_id = ?", (user_id,)).fetchone()
        if not portfolio: 
            return {"ok":  False, "error":  "Portfolio not found"}

        stocks = cursor.execute("SELECT * FROM user_stocks WHERE user_id = ?  AND is_active = 1", (user_id,)).fetchall()
        conn.close()

        return {
            "ok": True,
            "user_id": user["user_id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "portfolio":  {
                "total_budget": portfolio["total_budget"],
                "risk_tolerance": portfolio["risk_tolerance"],
                "selected_categories": json.loads(portfolio["selected_categories"])
            },
            "stocks": [dict(s) for s in stocks],
            "total_stocks": len(stocks)
        }
    except Exception as e:
        return {"ok": False, "error": f"Failed to get config: {e}"}

# ------------------------------------------------------------------
# Stats Endpoint (UPDATED)
# ------------------------------------------------------------------

@app.get("/api/stats")
def api_stats():
    files = executed_files()

    executed_entries = 0
    for f in files: 
        data = load_json(f)
        if isinstance(data, list):
            executed_entries += len(data)
        elif isinstance(data, dict):
            executed_entries += 1

    active_accounts = len(list(STATUS_DIR.glob("*_status.json")))

    active_stocks = 0
    market = load_json(MARKET_FILE)
    if isinstance(market, list):
        active_stocks = len(market)
    elif isinstance(market, dict) and isinstance(market.get("data"), list):
        active_stocks = len(market["data"])

    # Get counts from database
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        email_count = cursor.execute("SELECT COUNT(*) FROM email_history").fetchone()[0]
        log_count = cursor.execute("SELECT COUNT(*) FROM system_logs").fetchone()[0]
        signal_count = cursor.execute("SELECT COUNT(*) FROM signal_history").fetchone()[0]
        
        conn.close()
    except: 
        email_count = 0
        log_count = 0
        signal_count = 0

    return {
        "total_signals": signal_count + executed_entries,
        "executed_orders": executed_entries,
        "executed_files": len(files),
        "active_accounts": active_accounts,
        "active_stocks": active_stocks,
        "emails_sent": email_count,
        "log_entries": log_count,
        "system_uptime": None,
    }

# ------------------------------------------------------------------
# Core API Endpoints
# ------------------------------------------------------------------

@app.get("/api/health")
def health():
    return {"status": "OK", "time": time.time()}

@app.get("/api/market")
def api_market():
    return load_json(MARKET_FILE) or {} if MARKET_FILE.exists() else {}

@app.get("/api/signals")
def api_signals():
    return load_json(SIGNALS_FILE) or [] if SIGNALS_FILE.exists() else []

@app.get("/api/portfolio")
def api_portfolio():
    return load_json(DP_HOLDINGS_FILE) or {} if DP_HOLDINGS_FILE.exists() else {}

# ------------------------------------------------------------------
# Legacy Compatibility Aliases
# ------------------------------------------------------------------

@app.get("/market")
def market_alias():
    return api_market()

@app.get("/signals")
def signals_alias():
    return api_signals()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)