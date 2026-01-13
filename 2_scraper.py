# 2_scraper_elite_final.py - DECEMBER 2025 - UNKILLABLE | NO DATA LOSS | ATOMIC WRITE
import json
import os
import time
import signal
import atexit
import threading
import shutil
import collections
from datetime import datetime
from pathlib import Path
import csv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# ==================== CONFIG ====================
ENABLE_SOUND = True
TARGET_INTERVAL = 8.5          # Refresh every ~8.5 seconds
DATA_RETENTION_DAYS = 7
# ===============================================

BASE_DIR = Path("market_logs")
SHARED_DIR = Path("shared")
BASE_DIR.mkdir(exist_ok=True)
SHARED_DIR.mkdir(exist_ok=True)

PRIVATE_JSON = SHARED_DIR / "market_data_live.json"   # Only scraper writes
SHARED_JSON  = SHARED_DIR / "market_data.json"        # Engine reads this
MOVES_PRIVATE = SHARED_DIR / "market_moves_live.json" # Private moves file
MOVES_SHARED = SHARED_DIR / "market_moves.json"       # UI reads this

RECENT_MOVES = collections.deque(maxlen=100)  # Keep last 100 movements

print("NEPSE 2025 ELITE SCANNER - FINAL UNBREAKABLE EDITION")
print("=" * 95)

# Graceful shutdown
shutdown_event = threading.Event()

def signal_handler(sig, frame):
    print("\nSHUTDOWN SIGNAL RECEIVED - CLEANING UP...")
    shutdown_event.set()

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
atexit.register(lambda: print("Scanner stopped gracefully."))

def beep():
    if not ENABLE_SOUND:
        return
    try:
        # Method 1: Windows native loud beep
        if os.name == 'nt':
            import ctypes
            ctypes.windll.user32.MessageBeep(0xFFFFFFFF)  # Loud system sound
            ctypes.windll.user32.MessageBeep(0x00000040)  # Exclamation
        else:
            # Method 2: Try to play Windows sound from WSL (yes this works!)
            os.system("powershell.exe -c (New-Object Media.SoundPlayer 'C:\\Windows\\Media\\chimes.wav').PlaySync() 2>/dev/null || echo -e '\\a'")
    except:
        print("\a" * 8, flush=True)

# ==================== SMART TAB REUSE ====================
def get_or_create_dashboard_tab(driver, target_url):
    print("Searching for existing NEPSE dashboard tab...")
    for handle in driver.window_handles:
        driver.switch_to.window(handle)
        if "tms" in driver.current_url.lower() or "dashboard" in driver.current_url.lower():
            print(f"Reusing existing tab -> {driver.current_url}")
            return handle

    print("No dashboard found -> Opening new tab")
    driver.execute_script("window.open('','_blank');")
    driver.switch_to.window(driver.window_handles[-1])
    driver.get(target_url)
    time.sleep(7)
    print(f"Dashboard loaded -> {driver.current_url}")
    return driver.current_window_handle

# ==================== DRIVER INITIALIZATION ====================
DASHBOARD_URL = "https://tms66.nepsetms.com.np/tms/mwDashboard"
try:
    with open("broker.json") as f:
        DASHBOARD_URL = json.load(f)["dashboard_url"]
except:
    pass

def initialize_driver_session():
    """Initializes and configures the Selenium driver session to connect 
    to the existing, logged-in Chrome session using the dynamic port."""
    global driver, dashboard_handle
    
    print("\n[RECOVERY] Waiting for browser_ready.txt...")
    while not (SHARED_DIR / "browser_ready.txt").exists():
        time.sleep(0.5)

    # --- CRITICAL FIX: Read port dynamically from environment ---
    # It checks the CHROME_PORT environment variable (set by the orchestrator)
    # It defaults to '9228' only if the environment variable is not set.
    chrome_port = os.environ.get("CHROME_PORT", "9228") 
    debugger_address = f"127.0.0.1:{chrome_port}"
    print(f"[RECOVERY] Connecting to existing Chrome session at {debugger_address}")
    
    options = Options()
    # Use the dynamic debuggerAddress
    options.add_experimental_option("debuggerAddress", debugger_address)
    driver = webdriver.Chrome(options=options)
    # -----------------------------------------------------------

    # Reuse or create dashboard tab - NO TAB LEAK EVER
    dashboard_handle = get_or_create_dashboard_tab(driver, DASHBOARD_URL)
    driver.switch_to.window(dashboard_handle)

    print("[RECOVERY] Loading full stock table...")
    for _ in range(15):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(0.15)
    time.sleep(3)
    
    return driver, dashboard_handle

# Initialize the session for the first time
driver, dashboard_handle = initialize_driver_session()
# ==================== MANUAL LOGIN HOLD ====================
# ==================== MANUAL LOGIN HOLD (30s MAX) ====================
LOGIN_READY_FILE = SHARED_DIR / "login_ready.txt"
LOGIN_WAIT_SECONDS = 30

print("\n🛑 MANUAL LOGIN WINDOW 🛑")
print("→ Enter USERNAME / PASSWORD")
print("→ Solve CAPTCHA")
print(f"→ Auto-start in {LOGIN_WAIT_SECONDS} seconds")
print(f"→ Or create file early: {LOGIN_READY_FILE}")
print("=" * 80)

start_wait = time.time()

while True:
    if LOGIN_READY_FILE.exists():
        print("✅ LOGIN CONFIRMED VIA FILE")
        break

    if time.time() - start_wait >= LOGIN_WAIT_SECONDS:
        print("⏱ LOGIN TIMEOUT REACHED — CONTINUING AUTOMATICALLY")
        break

    time.sleep(1)

print("🚀 SCANNER STARTING")
print("=" * 80 + "\n")
# ====================================================================

# ==================== REFRESH BUTTON ====================
def click_refresh():
    # 1. Broadest possible set of selectors for NEPSE TMS 2025
    selectors = [
        (By.CSS_SELECTOR, "button .fa-sync"),
        (By.CSS_SELECTOR, "button .fa-redo"),         # Common in newer TMS
        (By.CSS_SELECTOR, ".refresh-icon"),           # Dashboard specific
        (By.XPATH, "//button[contains(@class, 'refresh')]"),
        (By.XPATH, "//i[contains(@class, 'sync')]/parent::button"),
        (By.XPATH, "//span[contains(text(), 'Refresh')]")
    ]
    
    for by, sel in selectors:
        try:
            # Short timeout so we don't hang if one fails
            btn = driver.find_element(by, sel)
            if btn.is_displayed():
                # Try standard click first (triggers JS events better)
                try:
                    btn.click()
                except:
                    # Fallback to JS click if blocked by an overlay
                    driver.execute_script("arguments[0].click();", btn)
                
                print(f" -> Refresh Triggered via {sel}")
                # CRITICAL: Wait for the network to actually fetch new data
                time.sleep(1.5) 
                return True
        except:
            continue
            
    # 2. FINAL FALLBACK: If no button works, force a browser-level refresh
    print(" -> WARNING: Refresh button not found. Using Browser-Level Refresh.")
    driver.refresh()
    time.sleep(3) # Give the page more time to reload completely
    return True

# ==================== BULLETPROOF ATOMIC WRITE ====================
def write_market_data_atomic(data):
    """NEVER LOSE DATA - Survives file locks, PermissionError, crashes"""
    max_retries = 6
    for attempt in range(max_retries):
        try:
            # Step 1: Write to private file (100% safe)
            with open(PRIVATE_JSON, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=None)
                f.flush()
                os.fsync(f.fileno())

            # Step 2: Atomic replace - BEST METHOD ON WINDOWS
            os.replace(PRIVATE_JSON, SHARED_JSON)
            print("Data updated (atomic replace)")
            return True

        except PermissionError:
            wait = 0.15 * (2 ** attempt)
            print(f"Shared file locked by engine - retry {attempt + 1}/{max_retries} in {wait:.2f}s...")
            time.sleep(wait)

        except Exception as e:
            print(f"Write error (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                print("FINAL FALLBACK -> Direct write to shared file")
                try:
                    with open(SHARED_JSON, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=None)
                    print("Direct write succeeded")
                    return True
                except:
                    print("ALL METHODS FAILED - DATA SAFE IN PRIVATE FILE")
                    return False
            time.sleep(0.3)
    return False

def write_moves_data_atomic(moves_list):
    """Write recent price movements to JSON for UI consumption"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            payload = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "moves": list(moves_list),  # Convert deque to list
                "count": len(moves_list)
            }
            
            # Step 1: Write to private file
            with open(MOVES_PRIVATE, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=None)
                f.flush()
                os.fsync(f.fileno())
            
            # Step 2: Atomic replace
            os.replace(MOVES_PRIVATE, MOVES_SHARED)
            return True
            
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"Failed to write moves: {e}")
            time.sleep(0.1)
    return False

# ==================== LOGGING SETUP ====================
def cleanup_old_logs():
    cutoff = time.time() - (DATA_RETENTION_DAYS * 86400)
    for p in BASE_DIR.rglob("*"):
        if p.is_dir() and p.stat().st_mtime < cutoff:
            shutil.rmtree(p, ignore_errors=True)
cleanup_old_logs()

csv_full = csv_moves = None
writer_full = writer_moves = None
current_hour = None

def open_hourly_files():
    global csv_full, csv_moves, writer_full, writer_moves, current_hour
    hour = datetime.now().strftime("%Y-%m-%d_%H")
    if hour == current_hour: return
    current_hour = hour
    for f in (csv_full, csv_moves):
        if f and not f.closed: f.close()

    path = BASE_DIR / f"NEPSE_{hour}"
    path.mkdir(exist_ok=True)

    full_path = path / "FULL_SNAPSHOT.csv"
    csv_full = open(full_path, "a", newline="", encoding="utf-8", buffering=1)
    writer_full = csv.writer(csv_full)
    if os.path.getsize(full_path) == 0:
        writer_full.writerow(["Time","Symbol","LTP","Open","High","Low","Close","Vol","%Chg"])

    moves_path = path / "MOVES.csv"
    csv_moves = open(moves_path, "a", newline="", encoding="utf-8", buffering=1)
    writer_moves = csv.writer(csv_moves)
    if os.path.getsize(moves_path) == 0:
        writer_moves.writerow(["Time","Symbol","LTP","From","Change","Dir","Vol","%Chg"])

    print(f"LOGGING -> {path.name}")

open_hourly_files()
last_full_write = 0

# ==================== MAIN LOOP - IMMORTAL ====================
all_stocks = {}
last_refresh = 0
heartbeat_counter = 0
# FIX: Initialize loop_start to ensure it's defined even if an exception occurs before the try block starts
loop_start = time.time()
print("SCANNER ONLINE - DOMINATING THE MARKET")
print("=" * 95)

while not shutdown_event.is_set():
    try:
        loop_start = time.time()
        now_full = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        now_short = datetime.now().strftime("%H:%M:%S")

        if datetime.now().hour != int(current_hour.split("_")[-1]):
            open_hourly_files()

        if loop_start - last_refresh >= TARGET_INTERVAL:
            if click_refresh():
                beep()
                print(f"[{now_full}] MARKET REFRESHED")
            last_refresh = loop_start
            time.sleep(1.2)

        data = driver.execute_script("""
            return Array.from(document.querySelectorAll('tbody tr')).map(tr => {
                const tds = tr.querySelectorAll('td');
                if (tds.length < 8) return null;
                const txt = i => (tds[i]?.innerText || '').replace(/,/g, '').trim();
                const num = i => parseFloat(txt(i)) || 0;
                return {
                    sym: txt(0),
                    ltp: num(1),
                    pct: num(2),
                    open: num(3),
                    high: num(4),
                    low: num(5),
                    close: num(6),
                    vol: num(7) || 0
                };
            }).filter(x => x && x.sym && x.ltp > 0);
        """)

        print(f"[{now_short}] Scraped {len(data)} stocks", end="")

        moved = []
        for item in data:
            sym = item["sym"]
            ltp = round(item["ltp"], 2)
            close = round(item["close"], 2)
            vol = int(item["vol"])

            prev = all_stocks.get(sym, {})
            old_ltp = prev.get("ltp", 0)
            ref = old_ltp if old_ltp > 0 else close
            change = ltp - ref

            if time.time() - last_full_write > 58:
                writer_full.writerow([now_full, sym, ltp, item["open"], item["high"], item["low"], close, vol, f"{item['pct']:+.2f}"])

            if abs(change) >= 0.01:
                direction = "UP" if change > 0 else "DOWN"
                moved.append((sym, ltp, ref, change, direction, vol, item["pct"]))
                beep()
                writer_moves.writerow([now_full, sym, ltp, f"{ref:.2f}", f"{change:+.2f}", direction, f"{vol:,}", f"{item['pct']:+.2f}"])

            all_stocks[sym] = {"ltp": ltp, "close": close, "volume": vol, "pct_change": item["pct"], "time": now_short}

        if moved:
            print(f" -> {len(moved)} MOVING!")
            print("=" * 95)
            for m in moved:
                print(f" {m[4]} {m[0]:8} | {m[2]:7.2f} -> {m[1]:7.2f} ({m[3]:+6.2f}) | Vol:{m[5]:>9,} | {m[6]:+6.2f}%")
                
                # NEW CODE - Store move for UI
                move_entry = {
                    "timestamp": now_full,
                    "time": now_short,
                    "symbol": m[0],
                    "direction": m[4],
                    "from_price": round(m[2], 2),
                    "to_price": round(m[1], 2),
                    "change": round(m[3], 2),
                    "volume": m[5],
                    "pct_change": round(m[6], 2)
                }
                RECENT_MOVES.append(move_entry)
            
            print("=" * 95 + "\n")
            
            # NEW CODE - Write moves to JSON for UI
            write_moves_data_atomic(RECENT_MOVES)
        else:
            print(" -> Quiet market")

        payload = {"timestamp": now_full, "total": len(all_stocks), "stocks": all_stocks.copy()}
        write_market_data_atomic(payload)

        if time.time() - last_full_write > 58:
            csv_full.flush()
            last_full_write = time.time()

        heartbeat_counter += 1
        if heartbeat_counter % 100 == 0:
            print(f"HEARTBEAT @ {now_full} | {len(all_stocks)} stocks | Running strong")

    except Exception as e:
        error_message = str(e).lower()
        print(f"\nRECOVERABLE ERROR: {e}")
        
        # Check for session termination errors (tab crashed, connection lost, invalid session)
        if "invalid session id" in error_message or "tab crashed" in error_message or "connection refused" in error_message:
            print("CRITICAL ERROR DETECTED: SESSION LOST OR TAB CRASHED. Attempting full re-initialization...")
            try:
                # Attempt to safely quit the broken session first
                driver.quit()
            except:
                pass
            
            # Re-run the initialization steps to reconnect
            try:
                driver, dashboard_handle = initialize_driver_session()
                print("RE-INITIALIZATION SUCCESSFUL. Resuming scan.")
            except Exception as reconnect_error:
                print(f"RE-INITIALIZATION FAILED: {reconnect_error}")
                # If reconnect fails, wait longer before next attempt
                time.sleep(15) 
        
        time.sleep(3) # Short wait for general errors

    elapsed = time.time() - loop_start
    if elapsed < 1.0:
        time.sleep(1.0 - elapsed)

# FINAL CLEANUP
for f in (csv_full, csv_moves):
    if f and not f.closed: f.close()
try: driver.quit()
except: pass
print("ELITE SCANNER STOPPED - THE EMPIRE IS ETERNAL - GOODBYE KING")