#!/usr/bin/env python3
# 4_order_executor_A.py — UPDATED FOR EMAIL-BASED FORM SUBMISSION
# - No longer needs browser/TMS automation
# - Reads signals and generates email forms
# - Sends forms to broker email: avinaya@miyo66.com
# - Compatible with existing pipeline (scraper + signal engine)

import os
import sys
import time
import json
import logging
from pathlib import Path
from datetime import datetime

# Accept both MANAGER_MODE and legacy MANAGED_MODE
MANAGER_MODE = os.environ.get("MANAGER_MODE", os.environ.get("MANAGED_MODE", "0")) == "1"
MANAGER_LAUNCHED = os.environ.get("MANAGER_LAUNCHED", "0") == "1"
AUTO_START = os.environ.get("AUTO_START", "0") == "1"

ACCOUNT_ID = os.environ.get("ACCOUNT_ID", "").strip()
if not ACCOUNT_ID:
    ACCOUNT_ID = os.environ.get("ACCOUNT", "A").strip()
ACCOUNT_NAME = f"TRADER_{ACCOUNT_ID}"

# This ensures both scripts use the exact same folder
BASE_DIR = Path(__file__).resolve().parent 
SHARED = BASE_DIR / "shared"

# Signal file
SIGNAL_FILE = SHARED / "signals.json"

# Logs will stay organized within the project folder
LOG_DIR = BASE_DIR / "Executor_Logs" / ACCOUNT_NAME / datetime.now().strftime("%Y-%m-%d")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Logging
log_path = LOG_DIR / f"log_{ACCOUNT_ID}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    handlers=[
        logging.FileHandler(log_path, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("executor")

# Import order execution function (NEW VERSION)
from order_utils import execute_order

def print_banner():
    """Print startup banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════════╗
║              NEPSE ORDER EXECUTOR - EMAIL MODE (2025)                ║
║                    Form-Based Broker Submission                       ║
╚══════════════════════════════════════════════════════════════════════╝
"""
    print(banner)
    print(f"Account: {ACCOUNT_NAME}")
    print(f"Mode: {'MANAGER' if MANAGER_MODE else 'STANDALONE'}")
    print(f"Broker Email: avinaya@miyo66.com")
    print("="*70)


def wait_for_startup(timeout: int = 30):
    """Wait for user confirmation or auto-start"""
    if AUTO_START:
        logger.info("AUTO_START=1 -> Starting immediately")    
        return True
    
    # Check if running in interactive terminal
    try:
        if sys.stdin and sys.stdin.isatty():
            logger.info("Press ENTER to start, or wait 30 seconds for auto-start...")
            import select
            
            # Wait with timeout
            start = time.time()
            while time.time() - start < timeout:
                # Check if Enter was pressed (Unix/Linux)
                if sys.platform != 'win32':
                    i, o, e = select.select([sys.stdin], [], [], 1)
                    if i:
                        sys.stdin.readline()
                        return True
                else:
                    # Windows: just sleep
                    time.sleep(1)
                
                # Check for browser_ready signal
                if (SHARED / "browser_ready.txt").exists() or (SHARED / "browser_ready.json").exists():
                    logger.info("Detected browser_ready signal")
                    return True
            
            logger.info("Timeout reached, starting automatically")
            return True
    except Exception:
        pass
    
    # Non-interactive: just wait a bit
    logger.info(f"Waiting {timeout}s for system to stabilize...")
    time.sleep(timeout)
    return True


def verify_configuration():
    """Verify that required configuration files exist"""
    required_files = [
        (BASE_DIR / "user_profile.json", "User profile configuration"),
        (BASE_DIR / "form_template.html", "HTML form template"),
        (BASE_DIR / "order_utils.py", "Order utilities module")
    ]
    
    missing = []
    for file_path, description in required_files:
        if not file_path.exists():
            missing.append(f"  - {description}: {file_path}")
            logger.error(f"Missing: {file_path}")
    
    if missing:
        logger.error("="*70)
        logger.error("CONFIGURATION ERROR - Missing required files:")
        for item in missing:
            logger.error(item)
        logger.error("="*70)
        logger.error("Please create these files before running the executor.")
        return False
    
    logger.info("✓ All configuration files found")
    return True


def process_signals_loop():
    """
    Main signal processing loop (SIMPLIFIED - No browser needed)
    Waits for signals.json and processes them by generating email forms
    """
    logger.info("="*70)
    logger.info("EXECUTOR ONLINE - Monitoring for signals...")
    logger.info("Signal file: " + str(SIGNAL_FILE))
    logger.info("="*70)
    
    heartbeat_path = SHARED / "executor_heartbeat" / f"{ACCOUNT_ID}.txt"
    heartbeat_path.parent.mkdir(parents=True, exist_ok=True)
    last_hb = 0
    
    while True:
        try:
            # Check for signals
            if SIGNAL_FILE.exists():
                logger.info("="*70)
                logger.info("SIGNAL DETECTED - Processing orders...")
                logger.info("="*70)
                
                try:
                    with open(SIGNAL_FILE, "r", encoding="utf-8") as f:
                        signals = json.load(f)
                except Exception as e:
                    logger.error(f"Failed to read signals.json: {e}")
                    time.sleep(1)
                    continue
                
                if not isinstance(signals, list):
                    signals = [signals]
                
                processed = []
                failed = []
                
                for sig in signals:
                    try:
                        symbol = sig.get('symbol', 'UNKNOWN')
                        action = sig.get('action', 'BUY')
                        
                        logger.info(f"Processing: {action} {symbol}")
                        
                        # Add timestamp if not present
                        if 'timestamp' not in sig:
                            sig['timestamp'] = time.time()
                        
                        # Execute order (generates form + sends email)
                        success = execute_order(
                            driver=None,  # Not needed in email mode
                            signal=sig,
                            logger=logger
                        )
                        
                        if success:
                            sig["processed_ts"] = time.time()
                            processed.append(sig)
                            logger.info(f"✓ {action} {symbol} - Form sent to broker")
                        else:
                            failed.append(sig)
                            logger.warning(f"✗ {action} {symbol} - Failed to send")
                    
                    except Exception as e:
                        logger.exception(f"Exception while processing signal {sig}: {e}")
                        failed.append(sig)
                
                # Archive or remove signals
                try:
                    if processed:
                        archive = SHARED / "executed"
                        archive.mkdir(parents=True, exist_ok=True)
                        ts = int(time.time())
                        archive_file = archive / f"done_{ACCOUNT_ID}_{ts}.json"
                        with open(archive_file, "w", encoding="utf-8") as af:
                            json.dump(processed, af, indent=2)
                        logger.info(f"Archived {len(processed)} processed signals")
                    
                    if failed:
                        failed_dir = SHARED / "failed"
                        failed_dir.mkdir(parents=True, exist_ok=True)
                        ts = int(time.time())
                        failed_file = failed_dir / f"failed_{ACCOUNT_ID}_{ts}.json"
                        with open(failed_file, "w", encoding="utf-8") as ff:
                            json.dump(failed, ff, indent=2)
                        logger.warning(f"Saved {len(failed)} failed signals")
                    
                    # Remove signals file
                    SIGNAL_FILE.unlink(missing_ok=True)
                    logger.info("Signals file processed and removed")
                
                except Exception as e:
                    logger.warning(f"Failed to archive/remove signals file: {e}")
                
                logger.info("="*70)
                logger.info(f"Batch complete: {len(processed)} sent, {len(failed)} failed")
                logger.info("="*70)
            
            # Heartbeat
            if time.time() - last_hb > 5:
                try:
                    heartbeat_path.write_text(str(time.time()))
                except Exception:
                    pass
                last_hb = time.time()
            
            # Check for shutdown flag
            if (SHARED / f"shutdown_{ACCOUNT_ID}.flag").exists():
                logger.info("Shutdown flag detected; exiting loop")
                break
            
            # Sleep briefly
            time.sleep(0.6)
        
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received; stopping")
            break
        
        except Exception as e:
            logger.exception(f"Unexpected error in main loop: {e}")
            time.sleep(5)


def main():
    """Main entry point"""
    print_banner()
    
    logger.info(f"Executor starting for {ACCOUNT_NAME} (ACCOUNT_ID={ACCOUNT_ID})")
    logger.info(f"Log file: {log_path}")
    
    # Clean up stale shutdown flag
    shutdown_flag = SHARED / f"shutdown_{ACCOUNT_ID}.flag"
    if shutdown_flag.exists():
        try:
            shutdown_flag.unlink()
            logger.info("Removed stale shutdown flag")
        except Exception as e:
            logger.warning(f"Failed to remove stale shutdown flag: {e}")
    
    # Verify configuration
    if not verify_configuration():
        logger.error("Configuration check failed. Exiting.")
        input("Press ENTER to exit...")
        sys.exit(1)
    
    # Wait for startup
    wait_for_startup(timeout=30)
    
    # Start processing
    try:
        process_signals_loop()
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
    finally:
        logger.info("="*70)
        logger.info("Executor exiting")
        logger.info("="*70)


if __name__ == "__main__":
    main()