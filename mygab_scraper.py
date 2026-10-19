#!/usr/bin/env python3
"""MyGab TV companion scraper.

Scans public pages you provide, extracts candidate video/player URLs, and writes
an importable JSON file. It does not download media, bypass logins/paywalls, or
try to defeat site protections. Only domains listed in sources.txt are accepted.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

BLOCKED_HOSTS = {"youtube.com", "www.youtube.com", "youtu.be", "m.youtube.com"}
BLOCKED_CONTENT = re.compile(
    r"underage|under-age|minor|children?|schoolgirl|schoolboy|teen(?:ager)?|"
    r"barely[\s_-]*legal|young[\s_-]*girl",
    re.I,
)
MEDIA_EXT = re.compile(r"\.(?:mp4|webm|ogg|m3u8)(?:$|[?#])", re.I)
VIDEO_PATH = re.compile(r"/(?:embed|player|video|videos|watch)(?:/|$)", re.I)


def read_lines(path: str | None) -> list[str]:
    if not path:
        return []
    p = Path(path)
    if not p.exists():
        raise SystemExit(f"Input file not found: {p}")
    return [line.strip() for line in p.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")]


def host_allowed(url: str, approved: list[str]) -> bool:
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower().rstrip(".")
        if parsed.scheme not in ("http", "https") or not host:
            return False
        if host in BLOCKED_HOSTS or host.endswith(".youtube.com"):
            return False
        if not approved:
            return False
        return any(host == d or host.endswith("." + d) for d in approved)
    except ValueError:
        return False


def flagged(text: str) -> bool:
    return bool(BLOCKED_CONTENT.search(text or ""))


def scan_page(driver, page_url: str, approved: list[str], keywords: list[str]) -> list[dict]:
    driver.get(page_url)
    WebDriverWait(driver, 12).until(
        lambda d: d.execute_script("return document.readyState") in ("interactive", "complete")
    )
    time.sleep(1.5)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    candidates: dict[str, dict] = {}

    def add(raw_url: str | None, title: str, force_player: bool = False) -> None:
        if not raw_url:
            return
        url = urljoin(page_url, raw_url.strip())
        if not host_allowed(url, approved) or flagged(title + " " + url):
            return
        parsed = urlparse(url)
        if not (MEDIA_EXT.search(url) or VIDEO_PATH.search(parsed.path) or force_player):
            return
        if keywords and not any(k.casefold() in (title + " " + url).casefold() for k in keywords):
            return
        candidates[url] = {
            "title": (title.strip() or "Video found by MyGab scraper")[:180],
            "url": url,
            "embed": url,
        }

    for tag in soup.find_all(["video", "source", "iframe"]):
        title = tag.get("title") or tag.get("aria-label") or ""
        add(tag.get("src") or tag.get("data-src"), title, tag.name in ("video", "source", "iframe"))
        for source in tag.find_all("source"):
            add(source.get("src") or source.get("data-src"), title, True)

    for tag in soup.find_all("a", href=True):
        title = tag.get_text(" ", strip=True) or tag.get("title") or ""
        add(tag.get("href"), title)

    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or tag.get_text())
        except (json.JSONDecodeError, TypeError):
            continue
        stack = data if isinstance(data, list) else [data]
        while stack:
            obj = stack.pop()
            if isinstance(obj, dict):
                for key in ("contentUrl", "embedUrl"):
                    value = obj.get(key)
                    if isinstance(value, str):
                        add(value, obj.get("name", "Video from page metadata"), True)
                stack.extend(v for v in obj.values() if isinstance(v, (dict, list)))
            elif isinstance(obj, list):
                stack.extend(obj)

    return list(candidates.values())


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan public pages and export MyGab TV JSON.")
    parser.add_argument("--urls", default="urls.txt", help="text file: one public page URL per line")
    parser.add_argument("--sources", default="sources.txt", help="text file: approved adult-only domains, one per line")
    parser.add_argument("--keywords", default="keywords.txt", help="optional keyword file, one per line")
    parser.add_argument("--output", default="mygab-results.json", help="JSON output path")
    parser.add_argument("--limit", type=int, default=100, help="maximum candidate results")
    args = parser.parse_args()

    approved = [d.lower().replace("https://", "").replace("http://", "").split("/")[0].strip(".")
                for d in read_lines(args.sources)]
    urls = read_lines(args.urls)
    keywords = read_lines(args.keywords)
    if not approved:
        raise SystemExit("No approved domains found. Populate sources.txt with trusted adult-only domains.")
    if not urls:
        raise SystemExit("No page URLs found. Populate urls.txt with public pages to scan.")
    for url in urls:
        if not host_allowed(url, approved):
            raise SystemExit(f"Blocked URL (not an approved domain or YouTube): {url}")

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1440,1000")
    options.add_argument("--log-level=3")
    driver = webdriver.Chrome(options=options)
    results: dict[str, dict] = {}
    try:
        for url in urls:
            print(f"Scanning {url}", flush=True)
            try:
                for item in scan_page(driver, url, approved, keywords):
                    results[item["url"]] = item
                    if len(results) >= max(1, args.limit):
                        break
            except Exception as exc:
                print(f"Skipped {url}: {exc}", file=sys.stderr, flush=True)
            if len(results) >= max(1, args.limit):
                break
    finally:
        driver.quit()

    payload = {
        "source": "MyGab TV companion scraper",
        "items": list(results.values()),
    }
    Path(args.output).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(results)} candidate(s) to {args.output}. Review them before importing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
