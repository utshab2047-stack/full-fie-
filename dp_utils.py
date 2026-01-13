# dp_utils.py
# Helper functions for DP holdings scraping and atomic writes.
# Exports:
#  - scrape_dp_holdings(driver, dp_path, logger) -> dict
#  - atomic_write_json(path, obj)

import json
import time
import os
from pathlib import Path
from selenium.webdriver.common.by import By

def atomic_write_json(path: Path, obj) -> None:
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    tmp.replace(path)

def scrape_dp_holdings(driver, dp_path: Path, logger, max_attempts: int = 3):
    """
    Scrape DP holdings table and write to dp_path atomically.
    Returns the holdings dict: { symbol: { "free_balance": int, ... }, ... }
    Simple, robust approach using a handful of selectors.
    """
    holdings = {}
    DP_URL = "https://tms34.nepsetms.com.np/tms/me/dp-holding"
    for attempt in range(1, max_attempts + 1):
        try:
            logger.info(f"[DP] Loading DP page (attempt {attempt})")
            driver.get(DP_URL)
            time.sleep(4)

            # try multiple row selectors
            row_selectors = [
                "table.k-grid-table tbody tr[kendogridlogicalrow]",
                "table.k-grid-table tbody tr[role='row']",
                ".k-grid-table tbody tr",
                "kendo-grid tbody tr",
                "tr"
            ]
            rows = []
            for sel in row_selectors:
                try:
                    rows = driver.find_elements(By.CSS_SELECTOR, sel)
                    if rows:
                        logger.debug(f"[DP] Found {len(rows)} rows using '{sel}'")
                        break
                except Exception:
                    continue

            if not rows:
                logger.warning("[DP] No rows found; retrying")
                time.sleep(1 + attempt)
                continue

            for idx, row in enumerate(rows):
                try:
                    cells = row.find_elements(By.CSS_SELECTOR, "td")
                    if not cells or len(cells) < 3:
                        continue
                    # Heuristics: symbol in 1st-2nd cell, free balance in 3rd-4th
                    # Try to find text and clean it
                    def text_or_empty(el):
                        try:
                            return (el.text or "").strip()
                        except Exception:
                            return ""
                    # Attempt a few likely indices (safe access)
                    symbol = text_or_empty(cells[0]) or text_or_empty(cells[1])
                    if not symbol:
                        continue
                    # Remove whitespace and commas
                    symbol = "".join(ch for ch in symbol if ch.isalnum()).upper()
                    free_text = ""
                    # prefer a free/available column
                    for idx_col in (2, 3, 4):
                        if idx_col < len(cells):
                            t = text_or_empty(cells[idx_col])
                            if t and any(ch.isdigit() for ch in t):
                                free_text = t
                                break
                    if not free_text:
                        free = 0
                    else:
                        free = int(float(free_text.replace(",", "").replace(" ", "") or 0))
                    if free > 0:
                        holdings[symbol] = {"free_balance": int(free), "timestamp": time.time()}
                except Exception as e:
                    logger.debug(f"[DP] row parse error idx={idx}: {e}")

            # atomic write
            try:
                os.makedirs(dp_path.parent, exist_ok=True)
                atomic_write_json(dp_path, holdings)
                logger.info(f"[DP] Wrote DP holdings ({len(holdings)} symbols) to {dp_path}")
            except Exception as e:
                logger.warning(f"[DP] Failed to write DP file: {e}")

            return holdings

        except Exception as e:
            logger.warning(f"[DP] scrape attempt {attempt} failed: {e}")
            time.sleep(1 + attempt)

    logger.error("[DP] All scrape attempts failed")
    return holdings