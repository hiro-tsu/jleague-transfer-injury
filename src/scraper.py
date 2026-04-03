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
# e.g. "2026年4月3日(金)" -> "2026-04-03" for sorting
DATE_SORT_RE = re.compile(r"(\d+)年(\d+)月(\d+)日")


def date_sort_key(article: dict) -> str:
    m = DATE_SORT_RE.search(article.get("date", ""))
    if not m:
        return "0000-00-00"
    return f"{m.group(1)}-{m.group(2).zfill(2)}-{m.group(3).zfill(2)}"


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
        href = title_tag.get("href", "")
        url = href if href.startswith("http") else f"https://www.jleague.jp{href}"
        date_raw = date_tag.get_text(strip=True)
        m = DATE_RE.search(date_raw)
        date = m.group(1) if m else date_raw

        items.append({"title": title, "date": date, "url": url})
    return items


def load_existing(out_path: Path) -> list[dict]:
    if not out_path.exists():
        return []
    try:
        data = json.loads(out_path.read_text())
        return data.get("articles", [])
    except (json.JSONDecodeError, KeyError):
        return []


def merge(existing: list[dict], new: list[dict]) -> list[dict]:
    seen = {a["url"] for a in existing if a.get("url")}
    for article in new:
        if article.get("url") and article["url"] not in seen:
            existing.append(article)
            seen.add(article["url"])
    return existing


def scrape_division(url: str) -> list[dict]:
    soup = fetch(url)
    return parse_articles(soup)


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    out_path = OUTPUT_DIR / "data.json"

    jst = timezone(timedelta(hours=9))
    now = datetime.now(jst).isoformat()

    new_articles = []
    for division, url in TARGETS.items():
        print(f"Scraping {division.upper()}...")
        articles = scrape_division(url)
        print(f"  -> {len(articles)} articles")
        new_articles.extend(articles)
        time.sleep(2)

    existing = load_existing(out_path)
    merged = merge(existing, new_articles)
    merged.sort(key=date_sort_key, reverse=True)

    cutoff = (datetime.now(timezone(timedelta(hours=9))) - timedelta(days=10)).strftime("%Y-%m-%d")
    merged = [a for a in merged if date_sort_key(a) >= cutoff]

    print(f"Total after merge: {len(merged)} articles (+{len(merged) - len(existing)} new)")

    results = {
        "updated_at": now,
        "articles": merged,
    }

    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"Saved to {out_path}")


if __name__ == "__main__":
    main()
