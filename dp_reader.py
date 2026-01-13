# dp_holding_reader.py — DP HOLDING SCRAPER MODULE (v2.1 - More Flexible XPaths)

import json
import time
import logging
from pathlib import Path
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# --- CONFIG ---
DP_HOLDING_URL = "https://tms34.nepsetms.com.np/tms/me/dp-holding"
SHARED_FOLDER = Path("shared")
DP_HOLDINGS_FILE = SHARED_FOLDER / "dp_holdings.json"
LOG_FILE = Path("logs/dp_reader.log")

SHARED_FOLDER.mkdir(parents=True, exist_ok=True)
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DP_READER')


def clean_number(text):
    text = text.strip()
    if not text or text in ('-', 'N/A'):
        return 0
    try:
        return int(float(text.replace(',', '')))
    except ValueError:
        logger.warning(f"Unexpected non-numeric value in quantity field: '{text}'. Returning 0.")
        return 0


def get_column_indices(driver):
    """
    Dynamically map column header text to its 0‑based index.
    More generic XPath: any <th> under <thead> of any table within the page.
    """
    HEADER_MAPPING = {
        "Symbol": None,
        "Free Balance": None,
        "TMS Balance": None
    }

    # More generic header XPath
    header_xpath = "//table//thead//th"

    try:
        headers = WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.XPATH, header_xpath))
        )
    except TimeoutException:
        logger.error("Timed out waiting for any table headers to load.")
        return None

    for index, th in enumerate(headers):
        header_text = th.text.strip()
        # Normalize header text (lowercase) for matching
        h = header_text.lower()
        if "symbol" == h or "symbol" in h:
            HEADER_MAPPING["Symbol"] = index
        elif "free balance" in h or ("balance" in h and "free" in h.lower()):
            HEADER_MAPPING["Free Balance"] = index
        elif "tms balance" in h or ("balance" in h and "tms" in h.lower()):
            HEADER_MAPPING["TMS Balance"] = index

    if all(v is not None for v in HEADER_MAPPING.values()):
        logger.info(f"Dynamic column indices found: {HEADER_MAPPING}")
        return HEADER_MAPPING
    else:
        logger.error(f"Could not map all required headers. Found: {[(i, th.text.strip()) for i, th in enumerate(headers)]}")
        return None


def scrape_dp_holdings(driver):
    logger.info("START: Scrape DP holdings...")
    try:
        driver.get(DP_HOLDING_URL)
        # Wait for table body or any table rows
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//table//tbody"))
            )
            WebDriverWait(driver, 10).until(
                lambda d: len(d.find_elements(By.XPATH, "//table//tbody//tr")) > 0
            )
        except TimeoutException:
            logger.error("Timed out waiting for DP Holding table or rows to load.")
            return {}

        column_map = get_column_indices(driver)
        if not column_map:
            return {}

        rows = driver.find_elements(By.XPATH, "//table//tbody//tr")
        holdings = {}
        for idx, row in enumerate(rows):
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) <= max(column_map.values()):
                    continue

                sym_idx = column_map["Symbol"]
                free_idx = column_map["Free Balance"]
                tms_idx = column_map["TMS Balance"]

                try:
                    symbol_element = cells[sym_idx].find_element(By.TAG_NAME, "span")
                    symbol = symbol_element.text.strip()
                except NoSuchElementException:
                    symbol = cells[sym_idx].text.strip()

                cds_free = clean_number(cells[free_idx].text)
                tms_bal = clean_number(cells[tms_idx].text)

                if symbol and (cds_free > 0 or tms_bal > 0):
                    holdings[symbol] = {
                        "free_balance": cds_free,
                        "tms_balance": tms_bal,
                        "timestamp": time.time()
                    }
            except Exception as e:
                row_html = row.get_attribute('outerHTML')
                logger.error(f"ROW_ERR idx={idx}: {e} — HTML: {row_html[:200]}")
                continue

        with open(DP_HOLDINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(holdings, f, indent=4)

        logger.info(f"SUCCESS: Scraped {len(holdings)} holdings.")
        return holdings

    except WebDriverException as e:
        logger.critical(f"WebDriver error during scrape: {e}", exc_info=True)
        return {}
    except Exception as e:
        logger.critical(f"Unexpected error during scrape: {e}", exc_info=True)
        return {}
