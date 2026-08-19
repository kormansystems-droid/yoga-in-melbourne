#!/usr/bin/env python3
"""
build_events.py — render data/events.json into the three homepage bands.

Why this exists
---------------
Until 19 Aug 2026 the Events & Workshops, Retreats and Teacher Training cards
were hand-typed into index.html. A one-line script at the foot of the page hides
any card whose `data-until` has passed, so the sections could only ever shrink:
Events shipped with seven cards and was down to three by 19 Aug with nothing
refilling it. Discovery (pull/pull_events.py) had been built by then, but its
output went nowhere — no code read events.json. This is the missing end of the
pipe.

The gate is unchanged
---------------------
This script renders whatever is already in data/events.json. It does not fetch,
and it cannot publish: getting an event INTO events.json still requires Mark to
read a proposal and someone to run pull_events.py --publish. Rendering is
downstream of his yes, never a way around it.

Manual and automatic entries coexist
------------------------------------
A retreat card carries a photograph, an alt line and a region caption that no
studio feed will ever provide, and some cards are deliberately evergreen (Warrior
One's 200-hour training has no end date). Those live as `source: "manual"` with
their fields written out verbatim and are never overwritten by a pull. Feed
entries carry only what a feed knows — title, teacher, date, price, link — and
this file composes their caption line from those.

Order of preference for the caption line:
  1. `cat`      — an explicit, hand-written caption. Always wins.
  2. composed   — "Sat 22 Aug · Within, South Yarra · $50" from the structured
                  fields, for anything a feed discovered.
"""
import json, html, datetime, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EVENTS = ROOT / "data" / "events.json"
SCHED = ROOT / "data" / "schedule.json"
INDEX = ROOT / "index.html"

try:
    from zoneinfo import ZoneInfo
    MELB = ZoneInfo("Australia/Melbourne")
except Exception:                                          # pragma: no cover
    MELB = datetime.timezone(datetime.timedelta(hours=10))

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

BANDS = [("events", "workshop"), ("retreats", "retreat"), ("training", "training")]


def esc(s):
    return html.escape(str(s or ""), quote=True)


def studios():
    try:
        return json.loads(SCHED.read_text(encoding="utf-8"))["studios"]
    except Exception:                                      # pragma: no cover
        return {}


def expiry(e):
    """The date this card should stop showing. None means evergreen."""
    for k in ("until", "ends", "starts"):
        v = e.get(k)
        if v:
            return v[:10]
    return None


def compose_cat(e, sts):
    """Caption for a feed-discovered event: when · where · how much."""
    bits = []
    st = e.get("starts")
    if st:
        try:
            d = datetime.datetime.fromisoformat(st)
            bits.append(f"{DAYS[d.weekday()]} {d.day} {MONS[d.month - 1]}")
        except ValueError:
            pass
    meta = sts.get(e.get("studio") or "", {})
    where = ", ".join(x for x in (meta.get("name"), meta.get("location")) if x)
    if where:
        bits.append(where)
    if e.get("teacher"):
        bits.append(e["teacher"])
    p = e.get("price")
    if p == 0:
        bits.append("Free")
    elif p:
        bits.append(f"${p:g}")
    return " · ".join(bits)


def strip_card(e, sts, indent="      "):
    cat = e.get("cat") or compose_cat(e, sts)
    ext = ' target="_blank" rel="noopener"' if e.get("external", True) and \
        (e.get("url") or "").startswith("http") else ""
    until = f' data-until="{esc(expiry(e))}"' if expiry(e) else ""
    blurb = e.get("blurb")
    if not blurb:
        meta = sts.get(e.get("studio") or "", {})
        blurb = meta.get("name", "")
    i, j = indent, indent + "  "
    return (f'{i}<a class="strip-card"{until} href="{esc(e.get("url"))}"{ext}>\n'
            f'{j}<div class="cat">{esc(cat)}</div>\n'
            f'{j}<h3>{esc(e.get("title"))}</h3>\n'
            f'{j}<p>{esc(blurb)}</p>\n'
            f'{i}</a>')


def band_card(e):
    """The big photographic card at the head of the Retreats section."""
    until = f' data-until="{esc(expiry(e))}"' if expiry(e) else ""
    ext = ' target="_blank" rel="noopener"' if (e.get("url") or "").startswith("http") else ""
    return (f'<a class="jb-card" href="{esc(e.get("url"))}"{ext}{until}>'
            f'<img src="{esc(e["image"])}" alt="{esc(e.get("alt"))}">'
            f'<div class="jb-scrim"></div>'
            f'<div class="jb-cap"><span class="cat">{esc(e.get("region"))}</span>'
            f'<h3>{esc(e.get("band_title") or e.get("title"))}</h3></div></a>')


def render(kind, evs, sts):
    out = []
    if kind == "retreat":
        band = [e for e in evs if e.get("image")]
        if band:
            out.append('    <div class="retreat-band">')
            out += ["      " + band_card(e) for e in band]
            out.append('    </div>')
    out.append('    <div class="strip">')
    out += [strip_card(e, sts) for e in evs]
    out.append('    </div>')
    return "\n".join(out)


def main(check=False):
    sts = studios()
    try:
        evs = json.loads(EVENTS.read_text(encoding="utf-8"))["events"]
    except FileNotFoundError:
        print(f"! {EVENTS.relative_to(ROOT)} does not exist — nothing to render.")
        return 1

    today = datetime.datetime.now(MELB).date().isoformat()
    live = [e for e in evs if (expiry(e) or "9999") >= today]
    dropped = len(evs) - len(live)

    src = INDEX.read_text(encoding="utf-8")
    out = src
    empty = []
    for sid, kind in BANDS:
        mine = sorted((e for e in live if e.get("kind") == kind),
                      key=lambda e: (e.get("starts") or e.get("until") or "9999", e.get("title", "")))
        if not mine:
            # A band that renders empty is the failure this pipeline exists to
            # prevent. Leave the existing markup alone and shout about it.
            empty.append(sid)
            print(f"! {sid}: nothing live — leaving the existing markup untouched")
            continue
        block = f"<!-- EVENTS:{kind} -->\n{render(kind, mine, sts)}\n    <!-- /EVENTS:{kind} -->"
        pat = re.compile(r"<!-- EVENTS:%s -->[\s\S]*?<!-- /EVENTS:%s -->" % (kind, kind))
        if not pat.search(out):
            print(f"! no <!-- EVENTS:{kind} --> markers in index.html", file=sys.stderr)
            return 2
        out = pat.sub(lambda _m: block, out, count=1)
        print(f"  {sid:9} {len(mine)} card(s)")

    print(f"\n{len(live)} live, {dropped} past dropped"
          + (f", EMPTY BANDS: {', '.join(empty)}" if empty else ""))

    if check:
        if out != src:
            print("index.html would change")
            return 1
        print("index.html unchanged")
        return 0
    if out != src:
        INDEX.write_text(out, encoding="utf-8")
        print(f"wrote {INDEX.name}")
    else:
        print("index.html already current")
    return 0


if __name__ == "__main__":
    sys.exit(main(check="--check" in sys.argv))
