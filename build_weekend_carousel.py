#!/usr/bin/env python3
"""
build_weekend_carousel.py: Saturday and Sunday as one 1080x1350 feed carousel.

Why this exists as its own script
---------------------------------
Two reasons, both load-bearing.

**Saturday cannot carry a post on its own.** It is the emptiest day the roster
has: 29 Aug 2026 was two classes at one studio, below the three-class floor
`build_story_cards.py` refuses to build under. Sunday is the fullest. Posting
them together turns the weakest day into the first act of a strong one instead
of a gap in the rhythm or a card that advertises smallness.

**A carousel is 4:5, and a story is 9:16.** These are laid out separately and
never cropped from each other. Cropping 1080x1920 to 1080x1350 loses 30% of the
height, which is where the line-up rows live. The lesson is already paid for in
`build_real_teachers.py`: "laying out twice costs nothing and loses nothing."

Everything factual: the classes, the portraits, the slugs: is imported from
`build_story_cards.py` rather than reimplemented, so a fix to the pull logic or
the portrait crop reaches both formats. This script owns layout and nothing else.

Why the daily story script was not extended instead
---------------------------------------------------
`build_story_cards.py` runs unattended in GitHub Actions every night. Adding an
aspect-ratio mode to a 780-line script whose fitting constants are all tuned to
1920 risks the daily ritual to save a file. A new format gets a new file.

    python3 build_weekend_carousel.py --saturday 2026-08-29

The Sunday is inferred as the next day. Card count is 5: opener, Saturday,
Sunday morning, Sunday afternoon, and the publication.
"""
import argparse, datetime, json, os, re
from pathlib import Path

import build_story_cards as S   # classes_for, portraits, slugs, esc, fonts

ROOT = Path(__file__).resolve().parent
OUT_ROOT = ROOT / "carousel"

# A feed card has no Instagram chrome eating its top and bottom the way a story
# does, so the padding is even and much tighter than the story's 230/330. The
# usable height still drops from ~1360px to ~1150px, which is why the split
# threshold below is lower than the story's LINEUP_MAX of 8.
LINEUP_MAX = 6

CARD_CSS = S.CARD_CSS.replace(
    "width:1080px;height:1920px;background:var(--paper);color:var(--ink);",
    "width:1080px;height:1350px;background:var(--paper);color:var(--ink);"
).replace(
    "padding:230px 92px 330px;",
    # Bottom padding reserves the absolutely-positioned footer. FIT_JS
    # measures scrollHeight, which an absolute element does not contribute
    # to, so without this a card overflows INTO the wordmark and reports
    # fit=1. Caught on the 30 Aug opener, where Janita Doelken's name sat
    # on top of "Yoga in Melbourne".
    "padding:104px 92px 232px;"
).replace(
    ".foot{position:absolute;left:92px;right:92px;bottom:150px;",
    ".foot{position:absolute;left:92px;right:92px;bottom:96px;"
) + """
/* Feed-only adjustments. The opener headline runs two lines on a 4:5 card where
   it ran one on 9:16, so it comes down; the date/count block is doing the same
   job in less height. */
.date{font-size:82px}
.names{margin-top:44px;padding-top:28px}
.card.lineup .kicker{margin-bottom:18px}
.day-head{font-family:'Fraunces',serif;font-size:64px;line-height:1.04;margin-bottom:6px}
.day-head em{font-style:italic;color:var(--henna)}
.day-sub{font-family:'Spline Sans Mono',monospace;font-size:24px;letter-spacing:.06em;
  color:var(--sage);padding-bottom:20px;border-bottom:2px solid var(--ochre);margin-bottom:6px}
"""


def esc(x):
    return S.esc(x)


def _card(inner, cls=""):
    return f'<div class="card {cls}">{inner}{S._foot()}</div>'


def build(schedule, sat, sun):
    """Five cards. Order is deliberate: the opener earns the swipe, the two
    line-ups are the product, the last card sells the publication.

    Measured 19 Aug 2026: cards presenting the publication and its people
    converted at 2.5-3% follows per eligible viewer; cards promoting a single
    thing converted at 0-0.5%. Carousel position also decays: 3.46 / 2.75 /
    1.77 across a three-card set: so the schedule goes early, not last."""
    sat_items = S.classes_for(schedule, "Sat", sat)
    sun_items = S.classes_for(schedule, "Sun", sun)
    if not sat_items and not sun_items:
        raise SystemExit(f"No classes across {sat} and {sun}.")

    # Dedup for the line-ups the same way the story frames do: a co-taught class
    # is one row, not one row per teacher.
    def dedup(items):
        # The key MUST carry the suburb. `studio` is the brand, so a key without
        # it collapses (Here) Yoga Malvern into (Here) Yoga Port Melbourne: two
        # different rooms, two different teachers, one of them silently deleted.
        # Caught on the 30 Aug build, where Steph Philip lost both her classes
        # because Emma teaches the same class at the same hour under the same
        # brand in another suburb.
        seen, out = set(), []
        for r in items:
            k = (r["time"], r["class"], r["studio"], r["suburb"])
            if k in seen:
                continue
            seen.add(k)
            out.append(r)
        return out

    sat_rows, sun_rows = dedup(sat_items), dedup(sun_items)
    teachers = []
    for r in sat_items + sun_items:
        if r["teacher"] not in teachers:
            teachers.append(r["teacher"])

    n_classes = len(sat_rows) + len(sun_rows)
    suburbs = {r["suburb"] for r in sat_items + sun_items if r["suburb"]}
    # Count locations, not brands: (Here) Yoga Malvern and (Here) Yoga Port
    # Melbourne are two rooms on two sides of the city. Counting the brand
    # once understates the weekend and is the same mistake, inverted, that
    # produced "Good Vibes and Good Vibes" in the carousel builder.
    studios = {(r["studio"], r["suburb"]) for r in sat_items + sun_items}

    frames = []

    # 1. Opener
    names = "".join(
        f'<li>{S._vignette_html(S.slug_of(t))}<span>{esc(t)}</span></li>'
        for t in teachers)
    span = f"{sat.strftime('%-d')}–{sun.strftime('%-d %B')}"
    frames.append(("01-opener", _card(
        f'<div class="kicker">Weekend Yoga</div>'
        f'<div class="date">Saturday <em>&amp;</em><br>Sunday</div>'
        f'<div class="count">{span} &middot; {n_classes} classes &middot; '
        f'{len(teachers)} teachers &middot; {len(studios)} studios</div>'
        f'<div class="names"><div class="names-lbl">Our teachers</div>'
        f'<ul class="names">{names}</ul></div>')))

    # 2. Saturday. It stays even at two classes, because on this card it is the
    # opening act of a full weekend rather than a day pretending to be full.
    if sat_rows:
        frames.append(("02-saturday", _card(
            f'<div class="kicker">Weekend Yoga &middot; The line-up</div>'
            f'<div class="day-head">Saturday</div>'
            f'<div class="day-sub">{sat.strftime("%-d %B")} &middot; '
            f'{len(sat_rows)} class{"es" if len(sat_rows) != 1 else ""}</div>'
            f'<div class="rows">{S._rows_html(sat_rows, True)}</div>', "lineup")))

    # 3-4. Sunday, split only when it will not fit. The split is by clock, not by
    # halves: a reader scanning for "what can I get to this morning" is served by
    # a morning card, not by rows 1-6 of nine.
    if sun_rows:
        parts = [("Sunday", sun_rows)]
        if len(sun_rows) > LINEUP_MAX:
            am = [r for r in sun_rows if S.hhmm_to_mins(_start24(r["time"])) < 12 * 60]
            pm = [r for r in sun_rows if S.hhmm_to_mins(_start24(r["time"])) >= 12 * 60]
            if am and pm:
                parts = [("Sunday morning", am), ("Sunday afternoon", pm)]
        for i, (label, rows) in enumerate(parts):
            frames.append((f"0{3+i}-{label.lower().replace(' ', '-')}", _card(
                f'<div class="kicker">Weekend Yoga &middot; The line-up</div>'
                f'<div class="day-head">{label}</div>'
                f'<div class="day-sub">{sun.strftime("%-d %B")} &middot; '
                f'{len(rows)} class{"es" if len(rows) != 1 else ""}</div>'
                f'<div class="rows">{S._rows_html(rows, True)}</div>', "lineup")))

    # 5. The publication. Not a repeat of the roster: the last card is the one
    # that has to be worth following. The scope claim is pinned to the TEACHER,
    # not the city: the site does not cover every studio in Melbourne and must
    # never say it does. It also does not say "across the studios we cover" -
    # that phrase is accurate but meaningless to a reader who has never been told
    # what we cover, and it hedges away the confidence the sentence needs.
    # See the long note in build_story_cards.py for the full reasoning.
    frames.append((f"0{len(frames)+1}-yoga-in-melbourne", _card(
        f'<div class="kicker">Yoga in Melbourne</div>'
        f'<div class="closer-lead">One weekend, <em>{len(studios)} studios</em>,<br>'
        f'{len(teachers)} teachers &mdash; in one place.</div>'
        f'<div class="closer-cta">Every class our teachers teach, in one place. '
        f'Profiles, schedules and the podcast at '
        f'<b>yogainmelbourne.com.au</b></div>')))
    return frames, teachers, sat_rows, sun_rows


def _start24(t):
    """'3:45–5:00 PM' -> '15:45', so morning/afternoon splits on real time."""
    m = re.match(r"\s*(\d{1,2}):?(\d{2})?", t)
    hh, mm = int(m.group(1)), int(m.group(2) or 0)
    ap = re.search(r"(AM|PM)", t, re.I)
    ap = ap.group(1).upper() if ap else None
    if ap == "PM" and hh != 12:
        hh += 12
    if ap == "AM" and hh == 12:
        hh = 0
    return f"{hh:02d}:{mm:02d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--saturday", required=True, help="YYYY-MM-DD")
    ap.add_argument("--dir", default=None)
    ap.add_argument("--no-png", action="store_true")
    a = ap.parse_args()

    sat = datetime.date.fromisoformat(a.saturday)
    if sat.weekday() != 5:
        raise SystemExit(f"{sat} is a {S.DAY_FULL[S.DAYS[sat.weekday()]]}, not a Saturday.")
    sun = sat + datetime.timedelta(days=1)

    schedule = json.loads(S.DATA.read_text())
    frames, teachers, sat_rows, sun_rows = build(schedule, sat, sun)

    out = ROOT / (a.dir or f"carousel/weekend-{sat.isoformat()}")
    out.mkdir(parents=True, exist_ok=True)
    for f in out.glob("card-*.png"):
        f.unlink()

    doc = (f"<!doctype html><html lang='en-AU'><head><meta charset='utf-8'>"
           f"<title>Weekend Yoga {sat} – {sun}</title>"
           f"<style>{S.FONT_FACES}{CARD_CSS}</style></head><body>"
           + "\n".join(h for _, h in frames) + "</body></html>")
    (out / "cards.html").write_text(doc, encoding="utf-8")
    print(f"Weekend {sat} – {sun}: {len(sat_rows)} Sat + {len(sun_rows)} Sun classes, "
          f"{len(teachers)} teachers, {len(frames)} cards -> {out.relative_to(ROOT)}/")
    if a.no_png:
        return

    from playwright.sync_api import sync_playwright
    exe = os.environ.get("CHROMIUM_EXECUTABLE")
    with sync_playwright() as p:
        b = p.chromium.launch(**({"executable_path": exe} if exe else {}))
        pg = b.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=1)
        pg.goto((out / "cards.html").as_uri())
        pg.wait_for_timeout(900)
        pg.evaluate(S.FIT_JS)
        over = pg.eval_on_selector_all(
            ".card", "els => els.map(e => [e.dataset.k, e.dataset.overflow || ''])")
        for i, (name, _) in enumerate(frames):
            f = out / f"card-{name}.png"
            pg.locator(".card").nth(i).screenshot(path=str(f))
            k, ov = over[i]
            print(f"  {f.name}  fit={k}{'  OVERFLOW' if ov else ''}")
        b.close()
    if any(ov for _, ov in over):
        raise SystemExit("A card overflowed even at the fit floor: do not post this set.")


if __name__ == "__main__":
    main()
