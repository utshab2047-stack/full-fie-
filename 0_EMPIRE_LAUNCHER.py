# 0_EMPIRE_LAUNCHER.py — ULTIMATE ONE-CLICK NEPSE EMPIRE
# Launches: Master Chrome → Scraper → Signal Engine → Executor (Account A)
# Fully Integrated Pipeline with Auto-Launch Logic

import subprocess
import time
import os
import sys
from pathlib import Path
SYSTEM_SHUTDOWN_FLAG = Path("shared/shutdown_system.flag")

# ================== CONFIG — PIPELINE ==================
LAUNCH_ORDER = [
    "1_master_browser.py",  # Master Chrome for manual login
    "2_scraper.py",         # Market data scraper
    "3_signal_engine.py",   # Signal generator (BUY/SELL)
    "4_order_executor_A.py", # Executor for Account A
    "4_order_executor_B.py", # Executor for Account B
]

DELAY_BETWEEN = 5  # seconds between launches

# ================== BANNER ==================
def print_banner():
    banner = """
╔══════════════════════════════════════════════════════════════════════╗
║               NEPSE EMPIRE 2025 — FULLY INTEGRATED MODE              ║
║               ONE CLICK = TRUE ALGO POWER FOR ACCOUNT A              ║
║                          Scraper + Signals + Executor                ║
╚══════════════════════════════════════════════════════════════════════╝
"""
    print("\n" + "═" * 78)
    print(banner)
    print("═" * 78 + "\n")


# ================== FUNCTIONAL HELPERS ==================
def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def launch_file(script_name, extra_env=None):
    """Launch a script file with appropriate environment variables."""
    if not Path(script_name).exists():
        print(f"ERROR: {script_name} NOT FOUND!")
        return False
    
    print(f"Launching → {script_name}")
    env = os.environ.copy()  # Base Execution Environment
    
    # Set environment for executor
    if script_name.startswith("4_order_executor_"):
        account_id = script_name.split("_")[-1].replace(".py", "")
        env["ACCOUNT_ID"] = account_id
        env["CHROME_PORT"] = "9228"
        env["NEW_CONSOLE"] = account_id
        
    # Apply any additional environment variables
    if extra_env:
        env.update(extra_env)
    
    try:
        subprocess.Popen(
            [sys.executable, script_name],
            env=env,
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0,
        )
        print(f"SUCCESS: {script_name} → Running")
        return True
    except Exception as e:
        print(f"FAILED: {script_name} → {e}")
        return False


# ================== MAIN LAUNCHER ==================
if __name__ == "__main__":
    clear_screen()
    print_banner()
    
    print("Starting your Integrated NEPSE Trading Empire...\n")
    
    success_count = 0
    for i, script in enumerate(LAUNCH_ORDER, 1):

        if i == 1:
            status = "MASTER BROWSER"
        elif i == 2:
            status = "SCRAPER"
        elif i == 3:
            status = "SIGNAL ENGINE"
        elif script.startswith("4_order_executor_"):
            acc = script.split("_")[-1].replace(".py", "")
            status = f"EXECUTOR — ACCOUNT {acc}"
        else:
            status = "UNKNOWN"

        print(f"[{i}/{len(LAUNCH_ORDER)}] Launching {status}")
        print(f"     → {script}")

        
        # Launch the file and check success
        if launch_file(script):
            success_count += 1
        
        # Delay between launches
        if i < len(LAUNCH_ORDER):
            print(f"     Waiting {DELAY_BETWEEN} seconds...\n")
            time.sleep(DELAY_BETWEEN)
    
    # ================== FINAL STATUS ==================
    print("\n" + "═" * 78)
    if success_count == len(LAUNCH_ORDER):
        print("PIPELINE FULLY ACTIVATED — SCRAPER + SIGNAL ENGINE + EXECUTOR")
        print("Account A is now LIVE")
        print("Zero lag │ Automated orders │ Real DP validation")
        print("Welcome to the future of algo trading!")
    else:
        print(f"WARNING: Only {success_count}/{len(LAUNCH_ORDER)} components launched!")
        print("   Check file names above and try again.")
    
    print("═" * 78)
    print("Empire is running in background. Close this window anytime.")
    print("To stop: Press Ctrl+C in each window or manually kill Python processes.")
    print("[LAUNCHER] Watching for system shutdown flag...")

try:
    while True:
        if SYSTEM_SHUTDOWN_FLAG.exists():
            print("[LAUNCHER] System shutdown flag detected. Exiting launcher.")
            break
        time.sleep(1)
except KeyboardInterrupt:
    print("[LAUNCHER] Manual interrupt received. Exiting.")

print("[LAUNCHER] Launcher stopped.")