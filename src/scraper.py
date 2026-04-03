"""
J-League transfer & injury scraper.
Fetches news from J-League official site for J1/J2/J3.
"""

import json
import re
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

TARGETS = {
    "j1": "https://www.jleague.jp/news/search/?category=2&team=&year=&month=",
    "j2": "https://www.jleague.jp/news/search/?category=4&team=&year=&month=",
    "j3": "https://www.jleague.jp/news/search/?category=6&team=&year=&month=",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; jleague-tracker/1.0)"
}

OUTPUT_DIR = Path(__file__).parent.parent / "output"

# e.g. "2026年4月3日(金) 17:30" -> "2026年4月3日(金)"
DATE_RE = re.compile(r"(\d+年\d+月\d+日\([^)]+\))")


def fetch(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "lxml")


def parse_articles(soup: BeautifulSoup) -> list[dict]:
    items = []
    for li in soup.select("ul.newsList li"):
        title_tag = li.select_one("h3.articleTit a")
        date_tag = li.select_one("p.timeStamp")
        if not title_tag or not date_tag:
            continue

        title = title_tag.get_text(strip=True)
        date_raw = date_tag.get_text(strip=True)
        m = DATE_RE.search(date_raw)
        date = m.group(1) if m else date_raw

        items.append({"title": title, "date": date})
    return items


def scrape_division(url: str) -> list[dict]:
    soup = fetch(url)
    return parse_articles(soup)


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    jst = timezone(timedelta(hours=9))
    now = datetime.now(jst).isoformat()

    all_articles = []
    for division, url in TARGETS.items():
        print(f"Scraping {division.upper()}...")
        articles = scrape_division(url)
        print(f"  -> {len(articles)} articles")
        all_articles.extend(articles)
        time.sleep(2)

    results = {
        "updated_at": now,
        "articles": all_articles,
    }

    out_path = OUTPUT_DIR / "data.json"
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"Saved to {out_path}")


if __name__ == "__main__":
    main()
