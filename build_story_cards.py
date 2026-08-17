#!/usr/bin/env python3
"""
build_story_cards.py — render the daily line-up as Instagram story cards.

  data/schedule.json  ──►  story/<date>/frame-NN-*.png   1080x1920, ready to post
                           story/<date>/cards.html       all frames, to eyeball first
                           story/<date>/captions.md      mentions + link per frame

Why this exists
---------------
"Yoga Tomorrow" runs every evening and "Yoga Today" every midday. Twice daily is
fourteen manual card builds a week, and a ritual that depends on a founder's daily
fiddling decays — usually just as it starts working. The schedule data already
exists; this is one more template over it.

Frames
------
    1  opener    the date, the count, every teacher named
    2  line-up   every class, chronological
    3+ teacher   one frame per teacher, her classes only

One frame per teacher at any roster size: a reshare audience enters at *her* frame
regardless of where it sits in the sequence, which is why frame position does not
decay tagged frames. There is no closer — on 15 Aug the closer took 30 views, the
fewest of any frame, because nobody could be tagged on it.

Every frame must carry a link sticker, and every frame that can name someone must
name them. The 15 Aug measurement: tagged frames averaged 123 views, untagged 36 —
3.4x. The opener was the best card and took the fewest views purely because nobody
was mentioned on it. captions.md exists so that never happens again.

Usage
-----
    python3 build_story_cards.py                      # tomorrow, all classes
    python3 build_story_cards.py --mode today         # today, only what is still ahead
    python3 build_story_cards.py --date 2026-08-23    # a specific date
    python3 build_story_cards.py --force              # override the thin-day guard

Cards are a draft, not a publication. Check them against the studios' own
timetables before posting — the pull window cannot see cancellations or covers
booked after the last run.
"""
import json, re, html, os, argparse, datetime, sys
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).parent))
from build_profiles import start_minutes, esc, esc_attr   # one time parser, not two

ROOT = Path(__file__).parent
DATA = ROOT / "data" / "schedule.json"
BASE_CSS = (ROOT / "partials" / "base.css").read_text()
OUTDIR = ROOT / "story"

MELB = ZoneInfo("Australia/Melbourne")
SITE = "https://yogainmelbourne.com.au"
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DAY_FULL = {"Mon": "Monday", "Tue": "Tuesday", "Wed": "Wednesday", "Thu": "Thursday",
            "Fri": "Friday", "Sat": "Saturday", "Sun": "Sunday"}

# A one-class card advertises smallness; a missing story costs nothing. Silence is
# the correct output on a thin day, so a thin day is an error, not a warning.
MIN_CLASSES = 3
# "Yoga Today" lists only what a reader can still get to. Listing a 6am class at
# noon makes the format look inattentive.
TODAY_CUTOFF = "14:00"

# Only the @font-face blocks — the real typefaces, none of the site's layout.
FONT_FACES = "\n".join(re.findall(r"@font-face\{[^}]*\}", BASE_CSS))

CARD_CSS = """
:root{
  --paper:#E7D9C0; --paper-deep:#DECDAE; --ink:#2A201A; --ink-soft:#5A4B3E;
  --henna:#9E3B26; --clay:#BC6B3C; --sage:#6F7155; --ochre:#C2974F;
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:#3a3a3a;font-family:'Hanken Grotesk',system-ui,sans-serif}
.card{
  width:1080px;height:1920px;background:var(--paper);color:var(--ink);
  position:relative;overflow:hidden;display:flex;flex-direction:column;
  /* Centre the content as a group between the safe zones: a 3-class day and a
     12-class day both sit balanced instead of hugging the top. */
  justify-content:center;
  /* Instagram's own UI eats roughly the top 220px and bottom 250px of a story,
     so nothing that must be read lives there. */
  padding:230px 92px 330px;
  --k:1;
}
.card + .card{margin-top:40px}
.kicker{
  font-family:'Spline Sans Mono',monospace;font-size:26px;letter-spacing:.20em;
  text-transform:uppercase;color:var(--henna);margin-bottom:26px;
}
.date{font-family:'Fraunces',serif;font-weight:400;font-size:96px;line-height:1.02;margin-bottom:18px}
.date em{font-style:italic;color:var(--henna)}
.count{
  font-family:'Spline Sans Mono',monospace;font-size:27px;letter-spacing:.06em;
  color:var(--sage);padding-top:22px;border-top:2px solid var(--ochre);
}
.names{margin-top:74px;padding-top:40px}
.names-lbl{
  font-family:'Spline Sans Mono',monospace;font-size:23px;letter-spacing:.14em;
  text-transform:uppercase;color:var(--sage);margin-bottom:22px;
}
.names li{font-family:'Fraunces',serif;line-height:1.30;list-style:none}

/* Row metrics scale off --k, which fit() lowers until the frame fits. The roster
   is meant to grow, so a fixed set of density breakpoints would quietly start
   clipping classes off the bottom of the card on the day it outgrew them. */
.rows{display:flex;flex-direction:column;gap:0;margin-top:14px}
.row{padding:calc(26px * var(--k)) 0;border-bottom:1.5px solid rgba(42,32,26,.16);display:grid;
     grid-template-columns:calc(238px * var(--k)) 1fr;column-gap:calc(30px * var(--k));
     align-items:baseline}
.row:last-child{border-bottom:none}
.row .t{font-family:'Spline Sans Mono',monospace;font-size:calc(30px * var(--k));
        color:var(--henna);white-space:nowrap}
.row .c{font-family:'Fraunces',serif;font-size:calc(42px * var(--k));line-height:1.18}
.row .w{font-family:'Hanken Grotesk',sans-serif;font-size:calc(27px * var(--k));
        color:var(--ink-soft);margin-top:calc(9px * var(--k))}
.row .w b{font-weight:600;color:var(--ink)}
.sub{font-style:italic;color:var(--sage)}
.names li{font-size:calc(58px * var(--k))}

.teacher-name{font-family:'Fraunces',serif;font-size:104px;line-height:1.02;margin-bottom:14px}
.teacher-sub{font-family:'Hanken Grotesk',sans-serif;font-size:32px;color:var(--ink-soft);
             padding-bottom:30px;border-bottom:2px solid var(--ochre)}

.foot{position:absolute;left:92px;right:92px;bottom:150px;
      display:flex;justify-content:space-between;align-items:flex-end;
      padding-top:26px;border-top:1.5px solid rgba(42,32,26,.22)}
.mark{font-family:'Fraunces',serif;font-size:40px;line-height:1}
.mark em{font-style:italic;color:var(--henna)}
.url{font-family:'Spline Sans Mono',monospace;font-size:23px;letter-spacing:.05em;color:var(--sage)}
"""

# Shrink each card's rows until it fits inside the frame. Runs in the page, so the
# HTML preview and the PNGs are always the same thing. A card that cannot fit even
# at the floor sets data-overflow, which the build then refuses to ship silently.
FIT_JS = """
(() => {
  const FLOOR = 0.62, STEP = 0.02;
  for (const card of document.querySelectorAll('.card')) {
    let k = 1;
    card.style.setProperty('--k', k);
    while (card.scrollHeight > card.clientHeight && k > FLOOR) {
      k = Math.round((k - STEP) * 100) / 100;
      card.style.setProperty('--k', k);
    }
    card.dataset.k = k;
    if (card.scrollHeight > card.clientHeight) card.dataset.overflow = '1';
  }
})();
"""


def slug_of(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def story_link(path, campaign):
    """Link-sticker target. Convention from the 15 Aug audit: reel/story links
    carry utm_medium and a campaign slug, so this traffic separates cleanly from
    the bio link in GA."""
    return f"{SITE}{path}?utm_source=instagram&utm_medium=story&utm_campaign={campaign}"


def classes_for(schedule, day, cutoff=None):
    """Every class on `day`, one entry per teacher, earliest first.

    A class co-taught or covered appears once per teacher because each teacher's
    own frame has to show it. The line-up frame dedups on (time, class, studio)."""
    studios = schedule["studios"]
    out = []
    for teacher, rec in schedule.get("teachers", {}).items():
        for c in rec.get("classes", []):
            if c.get("day") != day:
                continue
            mins = start_minutes(c["time"])
            if cutoff is not None and mins < cutoff:
                continue
            meta = studios.get(c["studio"], {})
            out.append({
                "teacher": teacher, "mins": mins, "time": c["time"], "class": c["class"],
                "studio": meta.get("name", c["studio"]), "suburb": meta.get("location", ""),
                "sub": bool(c.get("sub")),
            })
    return sorted(out, key=lambda r: (r["mins"], r["teacher"]))


def hhmm_to_mins(s):
    h, m = s.split(":")
    return int(h) * 60 + int(m)


def _rows_html(items, show_teacher):
    out = []
    for r in items:
        bits = [f'<b>{esc(r["studio"])}</b>']
        if r["suburb"]:
            bits.append(esc(r["suburb"]))
        if show_teacher:
            bits.insert(0, f'<b>{esc(r["teacher"])}</b>')
        sub = ' <span class="sub">· covering</span>' if r["sub"] else ""
        out.append(
            f'<div class="row"><div class="t">{esc(r["time"])}</div>'
            f'<div><div class="c">{esc(r["class"])}{sub}</div>'
            f'<div class="w">{" · ".join(bits)}</div></div></div>')
    return "\n".join(out)


def _foot():
    return ('<div class="foot"><div class="mark">Yoga <em>in</em> Melbourne</div>'
            '<div class="url">yogainmelbourne.com.au</div></div>')


def build_frames(schedule, day, date, items, mode):
    """-> list of {name, html, link, mentions, note}. One frame per teacher, always."""
    kicker = "Yoga Today" if mode == "today" else "Yoga Tomorrow"
    campaign = "daily-lineup-today" if mode == "today" else "daily-lineup"
    day_full = DAY_FULL[day]
    date_str = date.strftime("%-d %B")

    by_teacher = {}
    for r in items:
        by_teacher.setdefault(r["teacher"], []).append(r)
    teachers = sorted(by_teacher, key=lambda t: min(r["mins"] for r in by_teacher[t]))

    # the line-up frame shows each class once, however many teachers are on it
    seen, uniq = set(), []
    for r in items:
        key = (r["time"], r["class"], r["studio"])
        if key not in seen:
            seen.add(key)
            uniq.append(r)
    studios = {r["studio"] for r in items}
    suburbs = {r["suburb"] for r in items if r["suburb"]}

    def plural(n, word):
        if n == 1:
            return f"{n} {word}"
        return f"{n} {word + 'es' if word.endswith(('s', 'sh', 'ch', 'x')) else word + 's'}"

    frames = []

    # 1 — opener. Names every teacher, because this frame has to be taggable.
    lead = "Still to come today" if mode == "today" else "Tomorrow"
    frames.append({
        "name": "opener",
        "link": story_link("/", campaign),
        "mentions": list(teachers),
        "note": "Tag EVERY teacher on this frame. On 15 Aug this was the best card "
                "and took the fewest views (37) because nobody was mentioned on it.",
        "html": f'<div class="card"><div class="kicker">{esc(kicker)}</div>'
                f'<div class="date">{esc(day_full)}<br><em>{esc(date_str)}</em></div>'
                f'<div class="count">{esc(lead)} · '
                f'{plural(len(uniq), "class")} · {plural(len(teachers), "teacher")} · '
                f'{plural(len(studios), "studio")} · {plural(len(suburbs), "suburb")}</div>'
                f'<div class="names"><div class="names-lbl">Our teachers</div><ul>'
                + "".join(f"<li>{esc(t)}</li>" for t in teachers)
                + f'</ul></div>{_foot()}</div>',
    })

    # 2 — the full line-up
    frames.append({
        "name": "lineup",
        "link": story_link("/", campaign),
        "mentions": list(teachers),
        "note": "Tag every teacher and every studio shown.",
        "html": f'<div class="card"><div class="kicker">{esc(kicker)} · the line-up</div>'
                f'<div class="date">{esc(day_full)}</div>'
                f'<div class="rows">{_rows_html(uniq, show_teacher=True)}</div>{_foot()}</div>',
    })

    # 3+ — one per teacher
    for t in teachers:
        rows = by_teacher[t]
        slug = slug_of(t)
        where = ", ".join(sorted({r["suburb"] for r in rows if r["suburb"]}))
        frames.append({
            "name": slug,
            "link": story_link(f"/{slug}.html", campaign),
            "mentions": [t],
            "note": f"Mention {t} on this frame only — the frame she reshares is then "
                    f"entirely about her. Link sticker goes to her page, not the homepage.",
            "html": f'<div class="card"><div class="kicker">{esc(kicker)} · {esc(day_full)}</div>'
                    f'<div class="teacher-name">{esc(t)}</div>'
                    f'<div class="teacher-sub">{esc(where)}</div>'
                    f'<div class="rows">{_rows_html(rows, show_teacher=False)}</div>{_foot()}</div>',
        })
    return frames


def write_captions(path, frames, day, date, mode, items):
    kicker = "Yoga Today" if mode == "today" else "Yoga Tomorrow"
    when = "around midday" if mode == "today" else "in the evening, around 7pm"
    L = [f"# {kicker} — {DAY_FULL[day]} {date.strftime('%-d %B %Y')}",
         "",
         f"{len(frames)} frames. Post them as one run, {when} — and at the *same* hour "
         "every day, so yesterday's frames expire as these go up.",
         "",
         "**Before posting:** check these against the studios' own timetables. The pull "
         "window cannot see a cancellation or a cover booked since the last run.",
         "",
         "**Every frame takes a link sticker. Every frame that can name someone names them.**",
         "",
         "| # | Frame | Mention | Link sticker |",
         "|---|---|---|---|"]
    for i, f in enumerate(frames, 1):
        m = ", ".join(f["mentions"]) or "—"
        L.append(f'| {i} | `{f["name"]}` | {m} | `{f["link"]}` |')
    L += ["", "## Frame notes", ""]
    for i, f in enumerate(frames, 1):
        L.append(f'**{i}. {f["name"]}** — {f["note"]}')
        L.append("")
    L += ["## After posting", "",
          "- Stories are one rolling 24h sequence, so post ~24h apart and let yesterday's "
          "frames expire on their own. **Never delete frames to make room** — deleting "
          "destroys their insights permanently.",
          "- Screenshot Insights at ~20h, before expiry, and log views per frame in the "
          "rotation ledger. Tagged vs untagged is the number worth watching.",
          "- Judge this on taps, exits, link taps and reshares. Not likes — story likes "
          "are ~0 and always will be.",
          "- When a teacher reshares: react warmly, one line, and do not re-reshare an "
          "echo. The point is that replying opens a DM thread.",
          ""]
    path.write_text("\n".join(L))


def main():
    ap = argparse.ArgumentParser(description="Render the daily line-up as story cards.")
    ap.add_argument("--mode", choices=["tomorrow", "today"], default="tomorrow")
    ap.add_argument("--date", help="YYYY-MM-DD; default is tomorrow (or today in --mode today)")
    ap.add_argument("--cutoff", default=TODAY_CUTOFF,
                    help=f"--mode today: hide classes starting before this (default {TODAY_CUTOFF})")
    ap.add_argument("--force", action="store_true", help="build even on a thin day")
    ap.add_argument("--no-png", action="store_true", help="write the HTML preview only")
    a = ap.parse_args()

    schedule = json.loads(DATA.read_text())
    now = datetime.datetime.now(MELB)
    if a.date:
        date = datetime.date.fromisoformat(a.date)
    else:
        date = now.date() + (datetime.timedelta(days=0) if a.mode == "today"
                             else datetime.timedelta(days=1))
    day = DAYS[date.weekday()]
    cutoff = hhmm_to_mins(a.cutoff) if a.mode == "today" else None

    items = classes_for(schedule, day, cutoff)
    n_teachers = len({r["teacher"] for r in items})
    if len(items) < MIN_CLASSES and not a.force:
        raise SystemExit(
            f"{DAY_FULL[day]} {date}: {len(items)} class(es), below the {MIN_CLASSES}-class "
            f"threshold — not building.\nSilence costs nothing in stories; a one-class card "
            f"advertises smallness. Use --force to override.")
    if not items:
        raise SystemExit(f"{DAY_FULL[day]} {date}: no classes at all.")
    if a.mode == "today" and n_teachers < 5:
        print(f"⚠ Yoga Today is a five-teacher format and the roster shows {n_teachers}. "
              "It is the commercially valuable one — availability, not aspiration — but it "
              "needs the density to never look thin.")

    out = OUTDIR / f"{date.isoformat()}-{a.mode}"
    out.mkdir(parents=True, exist_ok=True)
    frames = build_frames(schedule, day, date, items, a.mode)

    doc = (f"<!doctype html><html lang=\"en-AU\"><head><meta charset=\"utf-8\">"
           f"<title>{esc_attr(a.mode)} {date.isoformat()}</title>"
           f"<style>{FONT_FACES}{CARD_CSS}</style></head><body>"
           + "\n".join(f["html"] for f in frames)
           + f"<script>{FIT_JS}</script></body></html>")
    (out / "cards.html").write_text(doc)
    write_captions(out / "captions.md", frames, day, date, a.mode, items)

    print(f"{DAY_FULL[day]} {date} — {len(items)} classes, {n_teachers} teachers, "
          f"{len(frames)} frames -> {out.relative_to(ROOT)}/")

    if a.no_png:
        return
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit("cards.html and captions.md written. Install playwright for PNGs: "
                         "pip install playwright")
    # Set CHROMIUM_EXECUTABLE where a Chromium is already on disk and playwright's
    # own build number does not match it (any preinstalled-browser environment).
    exe = os.environ.get("CHROMIUM_EXECUTABLE")
    with sync_playwright() as p:
        b = p.chromium.launch(**({"executable_path": exe} if exe else {}))
        pg = b.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=1)
        pg.goto((out / "cards.html").as_uri())
        pg.wait_for_timeout(600)   # let the embedded webfonts paint
        pg.evaluate(FIT_JS)        # re-fit now the real metrics are known
        scales = pg.evaluate(
            "() => [...document.querySelectorAll('.card')]"
            ".map(c => ({k: c.dataset.k, over: !!c.dataset.overflow}))")
        for i, f in enumerate(frames):
            name = f"frame-{i+1:02d}-{f['name']}.png"
            pg.locator(".card").nth(i).screenshot(path=str(out / name))
            s = scales[i]
            note = "" if s["k"] == "1" else f"   (fitted to {s['k']})"
            print(f"  {name}{note}")
        b.close()

    over = [f["name"] for f, s in zip(frames, scales) if s["over"]]
    if over:
        raise SystemExit(
            f"\n⚠ {', '.join(over)} still overflow at the smallest size. The PNGs are "
            "written but a class is cut off the bottom — split the line-up across two "
            "frames rather than posting these.")


if __name__ == "__main__":
    main()
