# Feed notes

## Decisions (2026-10-18)

- **Built ahead of time, not in the browser.** Most feeds block a page on another site from reading them (CORS), and the cloud session cannot reach feeds at all. So GitHub fetches them every hour and saves a plain page. The page itself does nothing but show links.
- **Read state is the browser's own visited-link colour.** A tapped title turns grey. No storage, no account. It is per browser, so the phone and the Mac each remember their own.
- **Limits:** the newest 15 items per feed, 150 in total, nothing older than 14 days. Items with no date are dropped rather than guessed at. Times are shown in Europe/Oslo.
- **Failed feeds are named in the footer,** so a dead feed is visible rather than silently missing.
- **Contrast, measured:** light: text 18.88:1, source 5.33:1, read 4.54:1. Dark: text 15.98:1, source 6.71:1, read 4.52:1. All pass 4.5:1.
- **Rows** are at least 37px tall and touch each other, so a tap never lands between two links. `noindex` keeps search engines off it.

## Open

- Pages must be switched on once by hand: repo Settings, Pages, Source: GitHub Actions. Until then the hourly job fails at the deploy step.
- GitHub pauses scheduled jobs in a public repo after 60 days with no commits. Editing `feeds.txt` now and then is enough; otherwise re-enable it in the repo's Actions tab.
- **Feeds (2026-10-19):** the 13 Substack subscriptions from the app, read off screenshots. Not checked from the cloud session (it cannot reach them); the first real build names any that fail in the footer. The Substack Post is listed as `post`, its handle in the app; if it fails, try `on.substack.com/feed`.
- Email newsletters still to come from Gmail. Some only exist as email; those need a feed bridge (for example Kill the Newsletter), or are left out.
- **Public, decided 2026-10-19.** Repo `Lordproc/RSS-feed`, made by hand (a web session cannot create repos). `feeds.txt` and these notes are public.
