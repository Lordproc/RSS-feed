#!/usr/bin/env python3
"""Find a working feed for each website in a list, and say how fresh it is.

For each line: try it as a feed; else read the page for the feed it advertises
(<link rel="alternate">); else try the usual addresses (/feed, /rss, ...).
Prints one line per site: OK with the feed address, item count and newest date, or NONE.
Run on GitHub (see .github/workflows/find-feeds.yml), since many sites block other networks.
"""

import re
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import build  # noqa: E402

COMMON = ["feed", "feed/", "rss", "rss.xml", "feed.xml", "atom.xml", "index.xml", "rss/", "blog/feed", "blog/rss"]
LINK = re.compile(r"<link\b[^>]*>", re.I)


def read_feed(data):
    """(source, items) if data is an RSS or Atom feed, else raise."""
    root = ET.fromstring(data)
    if build.local(root.tag) not in ("rss", "feed", "RDF"):
        raise ValueError("not a feed")
    return build.parse(data)


def advertised(page_url, html):
    found = []
    for tag in LINK.findall(html):
        if re.search(r'type=["\']application/(rss|atom)\+xml', tag, re.I):
            href = re.search(r'href=["\']([^"\']+)', tag, re.I)
            if href:
                found.append(urllib.parse.urljoin(page_url, href.group(1)))
    return found


def find(site):
    tried = []
    try:
        raw = build.fetch(site)
    except Exception as e:
        return f"NONE  {site}  ({type(e).__name__}: {e})"
    try:
        source, items = read_feed(raw)
        candidates = []
        hit = (site, source, items)
    except Exception:
        hit = None
        html = raw.decode("utf-8", "replace")
        base = site if site.endswith("/") else site + "/"
        candidates = advertised(site, html) + [urllib.parse.urljoin(base, c) for c in COMMON]
    for url in candidates:
        if hit:
            break
        if url in tried:
            continue
        tried.append(url)
        try:
            source, items = read_feed(build.fetch(url))
            hit = (url, source, items)
        except Exception:
            pass
    if not hit:
        return f"NONE  {site}  (no feed found; tried {len(tried)})"
    url, source, items = hit
    newest = items[0]["when"].date().isoformat() if items else "no dated items"
    return f"OK    {newest}  {len(items):>2} items  {url}  [{source}]"


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "candidates.txt"
    sites = build.read_feed_list(path)
    with ThreadPoolExecutor(max_workers=8) as pool:
        for line in pool.map(find, sites):
            print(line, flush=True)


if __name__ == "__main__":
    main()
