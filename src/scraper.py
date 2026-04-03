"""
J-League transfer & injury scraper.
HTML structure TBD — update parse_* functions once confirmed.
"""

import json
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# --- Target URLs (update if needed) ---
TARGETS = {
    "j1": "https://example.com/j1",  # TODO: replace with actual URL
    "j2": "https://example.com/j2",  # TODO: replace with actual URL
    "j3": "https://example.com/j3",  # TODO: replace with actual URL
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; jleague-tracker/1.0)"
}

OUTPUT_DIR = Path(__file__).parent.parent / "output"


def fetch(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "lxml")


def parse_transfers(soup: BeautifulSoup) -> list[dict]:
    """TODO: implement after HTML structure is confirmed."""
    return []


def parse_injuries(soup: BeautifulSoup) -> list[dict]:
    """TODO: implement after HTML structure is confirmed."""
    return []


def scrape_division(division: str, url: str) -> dict:
    soup = fetch(url)
    return {
        "division": division,
        "transfers": parse_transfers(soup),
        "injuries": parse_injuries(soup),
    }


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    jst = timezone(timedelta(hours=9))
    now = datetime.now(jst).isoformat()

    results = {
        "updated_at": now,
        "divisions": [],
    }

    for division, url in TARGETS.items():
        print(f"Scraping {division.upper()}...")
        data = scrape_division(division, url)
        results["divisions"].append(data)
        time.sleep(2)  # polite delay between requests

    out_path = OUTPUT_DIR / "data.json"
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"Saved to {out_path}")


if __name__ == "__main__":
    main()
