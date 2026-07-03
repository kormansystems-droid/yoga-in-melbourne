# Feed recon notes — 2026-07-04 (crack session)

Reference for the next build session. Goal: go from 3/5 studios automated to 5/5.

## Within (South Yarra) — CRACKED, ready to swap
- Current: pulled daily via Playwright (healcode page render), 35 rows. Works.
- Found: direct plain-HTTP endpoint, NO browser needed, NO Cloudflare:
  `GET https://widgets.mindbodyonline.com/widgets/schedules/188058/load_markup?options[start_date]=YYYY-MM-DD`
- Returns JSON `{"class_sessions": "<escaped HTML>"}` with the full week's
  bw-session markup (same shapes the existing healcode parser reads:
  hc_starttime / hc_endtime datetimes incl. AEST offset, bw-session__name,
  bw-session__staff, substitute flag, location).
- Widget identity: healcode widget id `f4188058a479`, bw-widget id `188058`,
  data-mbo-site-id `5729638`, cart site `111435`.
- Verified 2026-07-04: 254KB response, 35 staff blocks = matches live pull.
- NEXT: swap healcode_fetch() in pull/pull.py from Playwright to this GET
  (keep Playwright as fallback), test parser against real response, commit.
  This removes the browser dependency from the daily run entirely IF
  Warrior One/Happy Melon also go direct (below).

## Warrior One (Brighton/Mordialloc/Mornington) — REACHABLE, needs a build
- The schedule on warrioroneyoga.com.au/<location>/ is a go.mindbody V2
  branded_web embed in an iframe:
  `https://go.mindbodyonline.com/book/widgets/schedules/view/751447bfa/schedule`
  (that widget slug covers Brighton; other locations likely have their own
  slugs or a location filter — confirm on /mordialloc/ and /mornington/ pages).
- KEY FINDING: go.mindbodyonline.com loaded with NO Cloudflare challenge in a
  real browser. The blocked path was only the classic scheduler on
  clients.mindbodyonline.com (studioid=211566). So Warrior One is NOT
  un-scrapable — the earlier "manual forever" conclusion is superseded.
- Data loads via POST to the same URL (Next.js server action / client render;
  no __NEXT_DATA__ in HTML). Site id `11017` (branded_web), healcode site
  `211566` (classic, pricing links only on the page).
- UNKNOWNS to test next session:
  1. Does a headless GitHub-Actions runner (datacenter IP) also clear
     go.mindbodyonline.com, or does it challenge there? (Playwright recon
     against the embed URL directly.)
  2. Can the POST be replayed as plain HTTP (inspect payload in DevTools),
     or is headless render the path?
- Staff photos load from clients-content.mindbodyonline.com/studios/warrioroneyogaau/

## Happy Melon (Armadale) — same platform as Warrior One
- branded_web V2, mindbody site id `10796` (from June recon; LaunchDarkly
  context also showed mindbodyStudioId `137396`).
- Whatever solves Warrior One (embed render or POST replay) should port
  directly — find its embed slug on happymelon.com.au/timetable/ the same
  way (iframe src on the page).

## Momence (Grass Roots 34431, Here Yoga 40780) — done, in production
- Plain JSON, 7-day window, paginated. No action needed.

## Plan for next session (one focused pass)
1. Swap Within to load_markup GET (quick, low risk).
2. Recon go.mindbody embed from GitHub Actions headless (does it clear?).
3. If yes: parse rendered embed (or replayed POST) for Warrior One; port to
   Happy Melon; register feeds in schedule.json; flip both from manual.
4. Result: 5/5 studios unattended; Playwright possibly removed from the
   daily run altogether.
