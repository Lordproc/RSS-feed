# Feed notes

## Decisions (2026-10-18)

- **Built ahead of time, not in the browser.** Most feeds block a page on another site from reading them (CORS), and the cloud session cannot reach feeds at all. So GitHub fetches them every hour and saves a plain page. The page itself does nothing but show links.
- **Read state is the browser's own visited-link colour.** A tapped title turns grey. No storage, no account. It is per browser, so the phone and the Mac each remember their own.
- **Limits:** the newest 15 items per feed, 150 in total, nothing older than 14 days. Items with no date are dropped rather than guessed at. Times are shown in Europe/Oslo.
- **Failed feeds are named in the footer,** so a dead feed is visible rather than silently missing.
- **Contrast, measured:** light: text 18.88:1, source 5.33:1, read 4.54:1. Dark: text 15.98:1, source 6.71:1, read 4.52:1. All pass 4.5:1.
- **Rows** are at least 37px tall and touch each other, so a tap never lands between two links. `noindex` keeps search engines off it.

- **Saveable as a phone app (2026-10-19).** A manifest and icon in `static/` (copied next to the page on build) let it be added to the home screen and open full screen. Works offline since 2026-10-19 (asked for): `static/sw.js` plus one line on the page registers a service worker that always tries the network first and falls back to the last page it saved. That is the only JavaScript. Articles themselves still need a connection. The "Updated" time in the footer links back to the page, since a home-screen app on iPhone has no pull to refresh. Icon: three light list rows on near-black, drawn once with a small script, inside Android's safe zone.

## Open

- Pages must be switched on once by hand: repo Settings, Pages, Source: GitHub Actions. Until then the hourly job fails at the deploy step. Still off on 2026-10-19 (first run failed with "Get Pages site failed"; the page shows GitHub's 404), and runs 2 to 6 sat queued without starting.
- GitHub pauses scheduled jobs in a public repo after 60 days with no commits. Editing `feeds.txt` now and then is enough; otherwise re-enable it in the repo's Actions tab.
- **Feeds (2026-10-19):** the 13 Substack subscriptions from the app, read off screenshots. Not checked from the cloud session (it cannot reach them); the first real build names any that fail in the footer. The Substack Post is listed as `post`, its handle in the app; if it fails, try `on.substack.com/feed`.
- **Email newsletters (2026-10-19):** 12 added to `feeds.txt` from the last 12 months of Gmail, addresses worked out from the sender, not checked. Least certain: the three sent by Substack itself (`the-weekender`, `unstacked`, `someone-on-film`) and UX Magazine; the footer will say if they fail. Shops, receipts, product updates, job alerts and organisation news (Are.na, Rafto, APA, World Happiness Report, Artefact) were left out.
- **Email only, not in the feed** (no feed found; would need a bridge such as Kill the Newsletter, or stay in email): Dive Club (beehiiv), TLDR Design, Built for Mars (UX Bites), roadmap.sh, Design Spells, Growth.design, oio news. Also COS and KA-YO (shops, asked for 2026-10-19): shops publish no feed, so they need the same bridge.
- **World Happiness Report** added 2026-10-19 at a guessed address (`/feed/`); the footer will say if it is wrong.
- **Unsubscribing** from the newsletters now in the feed cannot be done from the cloud session: the unsubscribe links are web links (Substack has no email option) and the session has no web access. Done by hand in Gmail or in Substack's settings.
- **Public, decided 2026-10-19.** Repo `Lordproc/RSS-feed`, made by hand (a web session cannot create repos). `feeds.txt` and these notes are public.

## Substack relay (2026-10-19)

- Substack answers 403 to every request from GitHub's servers, even with a Safari User-Agent; other feeds load fine from the same run. It blocks by network, not by name tag.
- Fix chosen by the owner: a Cloudflare Worker (`worker/relay.js`) fetches Substack feeds from Cloudflare's network. `build.py` sends only `*.substack.com` through it, via the `RELAY` setting. The relay refuses anything that is not an https Substack `/feed` address, so it cannot be used as an open proxy, and keeps each feed for 15 minutes.
- Not yet known whether Substack lets Cloudflare's network in. The first build after `RELAY` is set answers it. If it also gets 403, the remaining route is building from the Mac.

## Explore page (2026-10-19)

- Asked for: topics I should keep up with or be exposed to, from my goals, and feeds for them, as a parallel thing to my own subscriptions. Built as a second page so busy news sites do not bury the writers I chose.
- Topics, from my profile and job radar: product and UX design; product practice (my gap is in-house product work); tech industry; AI from builders (8 of the August job ads asked for AI skills); service design and public sector (my favourite field, and where the Norwegian design jobs are); behaviour change and attention (my lens, and Days); accessibility; interaction and front-end craft; visual design and type; mobile platforms; Norway.
- 61 sites checked from GitHub in two passes; 37 had working feeds. No feed found (worth another route later): Kode24, Shifter, Computerworld, Digdir, Designsystemet, Grafill, DOGA, Uutilsynet, Datatilsynet, Forbrukertilsynet, Netlife, Knowit, Itera, Eye on Design, Mind the Product, The Decision Lab, Emil Kowalski, Service Design Network, Design Council, Public Digital.
- Six Substacks in `explore.txt` (Lenny, John Cutler, Ethan Mollick, Pragmatic Engineer, After Babel, Center for Humane Technology) use guessed addresses and wait on the relay.

## Newsletters by email (2026-10-19)

- Of the email-only newsletters, only TLDR Design also has a web feed (added to `feeds.txt`). Dive Club, Built for Mars, roadmap.sh, Design Spells, Growth.design and oio have none; COS and KA-YO are shops with none.
- Route chosen: one Kill the Newsletter inbox (an email address that turns whatever it receives into a feed) and a Gmail filter that forwards only those senders to it. Existing subscriptions stay as they are, and a new newsletter joins by adding it to the filter. `build.py` names each bridged post by its sender (`BRIDGE_HOSTS`), so one inbox still shows "Dive Club", "Growth.design" and so on.
- Bridge inbox created 2026-10-19: `eqe8zerk6b4k5zqr34wz1lifm3fdzds4d02h2guu@kill-the-newsletter.com`, feed in `feeds.txt`. Next: Gmail forwarding address (its confirmation code arrives as a post on Mine), then the filter.
- Gmail must never forward all mail: forwarding stays off in Gmail's Forwarding settings, and only the filter forwards.
- The bridge's feed address sits in this public repo, so anyone who finds it can read those newsletters, including their personal unsubscribe links. Accepted: they are mass mailings.
