# 1_master_browser.py - SAFE MASTER BROWSER (patched)
# Starts Chrome for manual login, detects successful login and writes shared/browser_ready files.
#
# Usage: python 1_master_browser.py
# Environment:
#   CHROME_PORT (optional) - remote debugging port, default 9228
#   PROFILE_PATH (optional) - path to Chrome user data dir (default ./chrome_profile_master)

import os
import time
import json
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

# Configuration
DEFAULT_PORT = os.environ.get("CHROME_PORT", "9228")
PROFILE_PATH = os.environ.get("PROFILE_PATH", str(Path.cwd() / "chrome_profile_master"))
BROWSER_READY_TXT = Path("shared") / "browser_ready.txt"
BROWSER_READY_JSON = Path("shared") / "browser_ready.json"
LOGIN_DETECT_TIMEOUT = int(os.environ.get("MASTER_LOGIN_TIMEOUT", "900"))  # seconds (default 15 minutes)
LOGIN_POLL = 10.0  # seconds

Path(PROFILE_PATH).mkdir(parents=True, exist_ok=True)
Path("shared").mkdir(parents=True, exist_ok=True)

options = Options()
options.add_argument(f"--user-data-dir={PROFILE_PATH}")
options.add_argument(f"--remote-debugging-port={DEFAULT_PORT}")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--start-maximized")
# keep automation switches minimal
options.add_experimental_option("excludeSwitches", ["enable-automation"])

print(f"[master] Starting Master Chrome on port {DEFAULT_PORT} with profile: {PROFILE_PATH!s}")

try:
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
except WebDriverException as e:
    print(f"[master] Failed to start Chrome webdriver: {e}")
    raise

# Open login page
LOGIN_URL = "https://tms66.nepsetms.com.np/tms/login"
try:
    driver.get(LOGIN_URL)
except Exception as e:
    print(f"[master] Warning: initial get() failed: {e}")

print("[master] MASTER BROWSER OPENED – Please log in manually (captcha may be required).")
print("[master] The script will detect successful login and then signal readiness to other components.")

def detect_login_complete(timeout: int = LOGIN_DETECT_TIMEOUT, poll: float = LOGIN_POLL) -> bool:
    """
    Heuristics to detect successful login:
      - Dashboard path in current_url ("mwDashboard") OR
      - Presence of elements likely only visible when logged in (Logout, Sign out, profile avatar).
    Adjust selectors if your site differs.
    """
    start = time.time()
    while True:
        try:
            cur = (driver.current_url or "").lower()
            if "mwdashboard" in cur or "mwDashboard".lower() in cur:
                print(f"[master] detect_login_complete: dashboard URL detected: {cur}")
                return True

            # Try common button/text selectors
            try:
                # logout-like buttons or links
                logout_candidates = driver.find_elements("xpath", "//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'logout') or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'sign out') or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'signout')]")
                if logout_candidates and len(logout_candidates) > 0:
                    return True
            except Exception:
                pass

            # Profile avatar or username elements (example heuristics)
            try:
                avatar = driver.find_elements("css selector", "img.user-avatar, img.profile-img, .user-avatar")
                if avatar and len(avatar) > 0:
                    return True
            except Exception:
                pass

        except Exception:
            # ignore and keep polling
            pass

        if time.time() - start > timeout:
            return False
        time.sleep(poll)

def write_browser_ready(port: str = DEFAULT_PORT):
    """
    Atomically write both a simple txt and a JSON file for compatibility.
    JSON contains pid, timestamp and port.
    """
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    data = {"pid": os.getpid(), "ts": ts, "port": str(port)}
    try:
        # json atomic write
        tmp = BROWSER_READY_JSON.with_suffix(".json.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f)
            f.flush()
            os.fsync(f.fileno())
        tmp.replace(BROWSER_READY_JSON)

        # txt write (legacy)
        tmp2 = BROWSER_READY_TXT.with_suffix(".txt.tmp")
        with open(tmp2, "w", encoding="utf-8") as f:
            f.write(f"http://127.0.0.1:{port}\n")
            f.flush()
            os.fsync(f.fileno())
        tmp2.replace(BROWSER_READY_TXT)

        print(f"[master] WROTE {BROWSER_READY_JSON} and {BROWSER_READY_TXT} -> ready")
    except Exception as e:
        print(f"[master] Failed to write browser_ready files: {e}")

# Detect login and signal readiness
ok = detect_login_complete()
if ok:
    write_browser_ready(DEFAULT_PORT)
    print("[master] MASTER BROWSER READY – continuing to keep process alive.")
else:
    print(f"[master] Login not detected within {LOGIN_DETECT_TIMEOUT}s. You can still manually create 'shared/browser_ready.txt' or restart this script.")
    # Still write a partial file if you want to allow manual override? Do not write by default to avoid false positives.

# Keep the browser process alive until user terminates this script
try:
    while True:
        time.sleep(10)
except KeyboardInterrupt:
    print("[master] Master browser shutting down (KeyboardInterrupt).")
finally:
    try:
        driver.quit()
    except Exception:
        pass
    print("[master] Exiting.")