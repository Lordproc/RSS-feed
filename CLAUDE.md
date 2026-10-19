# Feed

My personal, hyper-minimal RSS reader: one page, newest first, grouped by day. Title and source, nothing else. No accounts, no unread counts, and no JavaScript except the small offline helper (`static/sw.js`) that lets the saved phone app open without a connection.

- **Kit's role:** engineering project. Kit's design rules apply to the page's look and copy only. Keep it minimal: every addition has to earn its place against "one list of links".
- **Stack:** `build.py` (Python 3.11+, standard library only) reads `feeds.txt`, fetches every feed, and writes one static page to `site/index.html`. Styles live inline in the template at the bottom of `build.py`.
- **Repo:** `Lordproc/RSS-feed`, public. In Kit it sits at `projects/RSS-feed/` (gitignored there).
- **Hosting:** `.github/workflows/build.yml` rebuilds hourly and on every push to `main`, and publishes with GitHub Pages at https://lordproc.github.io/RSS-feed/. **Pushing `main` publishes.**
- **Run locally:** `./run`, then open http://localhost:8000.
- **Test:** `python3 build.py --feeds test/feeds.txt --out test/out/index.html --days 100000`. Should print `6 items from 3 of 5 feeds` (one RSS 2.0, one Atom, one RSS 1.0 fixture, plus two feeds that fail on purpose).
- **Add or remove a feed:** edit `feeds.txt`, one address per line.
