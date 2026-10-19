#!/usr/bin/env python3
"""Fetch the feeds in feeds.txt and write one static page to site/index.html.

Standard library only, so it runs anywhere Python 3.11+ does, with nothing to install.
Reads RSS 2.0, RSS 1.0 (RDF) and Atom.
"""

import argparse
import html
import re
import shutil
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("Europe/Oslo")
except Exception:
    TZ = timezone.utc

HERE = Path(__file__).parent
PER_FEED = 15      # newest items kept from each feed, so one busy feed cannot bury the rest
MAX_ITEMS = 150    # items on the page in total
# Substack refuses requests from GitHub's servers (403), whatever they claim to be. Its feeds go
# through a small relay on Cloudflare instead (worker/relay.js). Empty means fetch directly.
RELAY = "https://rss-relay.lordproctor.workers.dev/"
RELAYED_HOSTS = ("substack.com",)
# Email-to-feed services: one inbox can hold many newsletters.
BRIDGE_HOSTS = ("kill-the-newsletter.com",)
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15"


def read_feed_list(path):
    urls = []
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            urls.append(line)
    return urls


def fetch(url):
    if "://" not in url:
        return (HERE / url).read_bytes()
    host = urllib.parse.urlsplit(url).hostname or ""
    if RELAY and any(host == h or host.endswith("." + h) for h in RELAYED_HOSTS):
        url = RELAY + "?url=" + urllib.parse.quote(url, safe="")
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/rss+xml, application/atom+xml, application/xml;q=0.9, */*;q=0.8",
    })
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()


def local(tag):
    """Tag name without its XML namespace: '{http://www.w3.org/2005/Atom}entry' -> 'entry'."""
    return tag.rsplit("}", 1)[-1]


def child(el, *names):
    for c in el:
        if local(c.tag) in names:
            return c
    return None


def text(el, *names):
    c = child(el, *names)
    return (c.text or "").strip() if c is not None else ""


def parse_date(s):
    if not s:
        return None
    try:
        d = parsedate_to_datetime(s)
    except (TypeError, ValueError):
        try:
            d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d


def clean(s):
    """Feed titles often carry entities or stray tags. Leave plain text."""
    s = html.unescape(re.sub(r"<[^>]+>", "", html.unescape(s)))
    return re.sub(r"\s+", " ", s).strip()


def atom_link(entry):
    for c in entry:
        if local(c.tag) == "link" and c.get("rel", "alternate") == "alternate":
            return c.get("href", "")
    return ""


def author(entry):
    """Atom author name, without an email address: 'Dive Club <hi@dive.club>' -> 'Dive Club'."""
    a = child(entry, "author")
    name = text(a, "name") if a is not None else ""
    return re.sub(r"\s*<[^>]*>\s*$", "", name).strip().strip('"')


def parse(data, per_feed=PER_FEED):
    root = ET.fromstring(data)
    kind = local(root.tag)
    if kind == "feed":
        source = text(root, "title")
        entries = [e for e in root if local(e.tag) == "entry"]
        items = [(text(e, "title"), atom_link(e), text(e, "published", "updated"), author(e))
                 for e in entries]
    else:
        channel = child(root, "channel")
        source = text(channel, "title") if channel is not None else ""
        # RSS 2.0 keeps items inside the channel; RSS 1.0 keeps them beside it.
        pool = list(channel) if kind == "rss" else list(root)
        entries = [e for e in pool if local(e.tag) == "item"]
        items = [(text(e, "title"), text(e, "link"), text(e, "pubDate", "date"), "") for e in entries]

    out = []
    for title, link, date, by in items:
        when = parse_date(date)
        if link and when:
            out.append({"title": clean(title) or link, "link": link, "when": when, "by": clean(by)})
    out.sort(key=lambda i: i["when"], reverse=True)
    return clean(source), out[:per_feed]


def load(url, per_feed=PER_FEED):
    try:
        source, items = parse(fetch(url), per_feed)
        # A newsletter bridge gathers many senders in one feed, so name each post by its sender.
        bridge = any(h in url for h in BRIDGE_HOSTS)
        for i in items:
            i["source"] = (bridge and i["by"]) or source or url
        return url, items, None
    except Exception as e:
        return url, [], f"{type(e).__name__}: {e}"


def day_label(d, today):
    if d == today:
        return "Today"
    if d == today - timedelta(days=1):
        return "Yesterday"
    return f"{d:%a} {d.day} {d:%b}"


# The two pages: my own subscriptions, and a wider list chosen to keep me up to date.
PAGES = [("index.html", "Mine", "./"), ("explore.html", "Explore", "explore.html")]


def nav(current):
    links = []
    for file, label, href in PAGES:
        mark = ' aria-current="page"' if file == current else ""
        links.append(f'<a href="{href}"{mark}>{label}</a>')
    return '<nav aria-label="Pages">' + " ".join(links) + "</nav>"


def render(items, failed, now, page="index.html"):
    today = now.date()
    rows, current = [], None
    for i in items:
        d = i["when"].astimezone(TZ).date()
        if d != current:
            if current is not None:
                rows.append("</ul>")
            rows.append(f"<h2>{day_label(d, today)}</h2>\n<ul>")
            current = d
        rows.append(
            f'<li><a href="{html.escape(i["link"])}"><span class="t">{html.escape(i["title"])}</span>'
            f' <span class="s">{html.escape(i["source"])}</span></a></li>'
        )
    if current is not None:
        rows.append("</ul>")
    if not items:
        rows.append("<p>Nothing new.</p>")

    # A link back to the page, because a saved home-screen app on iPhone has no pull to refresh.
    here = "./" if page == "index.html" else page
    foot = f'<a href="{here}">Updated {now.day} {now:%b %H:%M}</a>'
    if failed:
        names = ", ".join(html.escape(u) for u in failed)
        foot += f'<br>Could not read {len(failed)}: {names}'

    return (TEMPLATE.replace("{{nav}}", nav(page)).replace("{{rows}}", "\n".join(rows))
            .replace("{{foot}}", foot))


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<meta name="robots" content="noindex">
<title>Feed</title>
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="icon-180.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Feed">
<meta name="theme-color" content="#ffffff" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#111111" media="(prefers-color-scheme: dark)">
<style>
:root { --bg: #fff; --fg: #111; --muted: #6b6b6b; --read: #767676; }
@media (prefers-color-scheme: dark) {
  :root { --bg: #111; --fg: #ececec; --muted: #9a9a9a; --read: #7c7c7c; }
}
* { margin: 0; padding: 0; }
body { background: var(--bg); color: var(--fg); font: 17px/1.4 system-ui, sans-serif;
  max-width: 38rem; margin: 0 auto; padding: 2.5rem 1rem 4rem; }
h2 { font-size: 0.8rem; font-weight: 500; color: var(--muted); margin: 2rem 0 0.25rem; }
h2:first-child { margin-top: 0; }
ul { list-style: none; }
a { display: block; padding: 0.4rem 0; color: var(--fg); text-decoration: none; }
a:visited { color: var(--read); }
a:hover .t { text-decoration: underline; text-decoration-thickness: 1px; text-underline-offset: 3px; }
a:focus-visible { outline: 2px solid currentColor; outline-offset: 2px; }
.s { color: var(--muted); font-size: 0.8rem; white-space: nowrap; }
nav { display: flex; gap: 1.25rem; margin-bottom: 2rem; font-size: 0.8rem; }
nav a, nav a:visited { display: inline-block; padding: 0.6rem 0; color: var(--muted); }
nav a[aria-current] { color: var(--fg); font-weight: 600; }
footer { margin-top: 3rem; font-size: 0.8rem; color: var(--muted); }
footer a { display: inline; color: inherit; }
</style>
</head>
<body>
{{nav}}
<main>
{{rows}}
</main>
<footer>{{foot}}</footer>
<script>if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js");</script>
</body>
</html>
"""


def build_page(feeds, out, page, days, per_feed, max_items):
    urls = read_feed_list(feeds)
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda u: load(u, per_feed), urls))

    now = datetime.now(TZ)
    cutoff = now - timedelta(days=days)
    seen, items, failed = set(), [], []
    for url, got, err in results:
        if err:
            failed.append(url)
            print(f"failed  {url}  {err}", file=sys.stderr)
        for i in got:
            if i["link"] not in seen and cutoff <= i["when"] <= now + timedelta(hours=1):
                seen.add(i["link"])
                items.append(i)
    items.sort(key=lambda i: i["when"], reverse=True)
    items = items[:max_items]

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(items, failed, now, page))
    print(f"{len(items)} items from {len(urls) - len(failed)} of {len(urls)} feeds -> {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--feeds", default=HERE / "feeds.txt")
    ap.add_argument("--explore", default=HERE / "explore.txt")
    ap.add_argument("--out", default=HERE / "site" / "index.html")
    ap.add_argument("--days", type=int, default=14, help="leave out items older than this")
    args = ap.parse_args()

    out = Path(args.out)
    build_page(args.feeds, out, "index.html", args.days, PER_FEED, MAX_ITEMS)
    # Explore holds busy news sites, so fewer per feed: one site's day cannot fill the page.
    explore = Path(args.explore)
    if explore.exists():
        build_page(explore, out.parent / "explore.html", "explore.html", args.days, 5, 200)
    # App icon, manifest and offline copy, so the page can be saved to a phone's home screen.
    shutil.copytree(HERE / "static", out.parent, dirs_exist_ok=True)


if __name__ == "__main__":
    main()
