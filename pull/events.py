#!/usr/bin/env python3
"""
events.py — workshops, courses and retreats, kept in data/events.json.

Why this is separate from schedule.json
---------------------------------------
A class is a weekly pattern; an event happens once. Collapsing an event into the
weekly grid makes it look like a fixture — Sarah Metzger's 30-minute "200hr Yoga
Training Info Session" on Sunday 23 Aug 2026 rendered on her page as though she
taught every Sunday at 11:15. Events keep their real start and end datetime here
and are never deduped by weekday.

An event may ALSO appear as a class row (Mark's call, 18 Aug 2026): someone
scanning a timetable for Sunday should still see it. The two surfaces answer
different questions, so the same session legitimately shows in both.

Where events come from
----------------------
Studios fall into three groups and each needs a different answer:

  1. Momence feeds (Grass Roots, Kozen, (Here), Good Vibes) publish events in the
     same endpoint as classes, distinguished only by `type`. Fully automatic.
  2. Mindbody studios (Within) publish classes through the booking widget and
     events ONLY as marketing pages. Their timetable widget was checked on
     18 Aug 2026 and returns four class names and nothing else — no API will ever
     surface Flight School. These are scraped from `event_pages` on the studio.
  3. Studios with no live feed (Warrior One, Happy Melon, Inndriya). Manual
     entries, which this module preserves and never overwrites.

The scraper is deliberately loud, not clever. Studio marketing pages are
hand-typed prose in a website builder; the date line WILL change format without
warning. When a configured page yields no event, that is reported as an anomaly
rather than silently shrinking the section — an events page that quietly empties
is exactly the failure this file exists to prevent.
"""
import re, json, datetime

try:
    from zoneinfo import ZoneInfo
    MELB = ZoneInfo("Australia/Melbourne")
except Exception:                                          # pragma: no cover
    MELB = datetime.timezone(datetime.timedelta(hours=10))

# Momence `type` -> the section an event belongs in. These three are exactly the
# homepage's #events / #retreats / #training bands.
KIND = {
    "special-event": "workshop",
    "special-event-new": "workshop",
    "course": "training",
    "retreat": "retreat",
}
# Everything else Momence returns is an ordinary class.
CLASS_TYPES = {"fitness", "course-class"}

MONTHS = {m.lower(): i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], 1)}
MONTHS.update({m[:3].lower(): i for m, i in list(MONTHS.items())})


def _iso(dt):
    return dt.isoformat()


# ---- Momence ---------------------------------------------------------------
def momence_events(payload, studio_id, location=None):
    """Non-class sessions from a Momence host-schedule payload.

    Deduped on title: a four-week course returns one session per week and the
    event is the course, not each meeting. The earliest session wins, so the
    listing shows when it starts."""
    out = {}
    for s in payload:
        if s.get("isCancelled"):
            continue
        kind = KIND.get(s.get("type"))
        if not kind:
            continue
        if location and str(s.get("location", "")).strip() != location:
            continue
        st = datetime.datetime.fromisoformat(s["startsAt"].replace("Z", "+00:00")).astimezone(MELB)
        en = datetime.datetime.fromisoformat(s["endsAt"].replace("Z", "+00:00")).astimezone(MELB)
        title = (s.get("sessionName") or "").strip()
        key = (studio_id, title.lower())
        prev = out.get(key)
        if prev and prev["starts"] <= _iso(st):
            continue
        price = s.get("price")
        if price is None:
            price = s.get("fixedTicketPrice")
        out[key] = {
            "id": f"momence:{s.get('hostId')}:{title.lower()[:40]}",
            "studio": studio_id,
            "kind": kind,
            "title": title,
            "teacher": (s.get("teacher") or "").strip(),
            "starts": _iso(st),
            "ends": _iso(en),
            "price": price,
            "url": s.get("link") or "",
            "source": "momence",
        }
    return list(out.values())


# ---- Studio marketing pages (Within, and anything Squarespace-shaped) ------
# "SAT, 22 August | 1pm - 3pm"   /   "Saturday 22 August, 1pm-3pm"
_DATE_LINE = re.compile(
    r"(?:mon|tue|wed|thu|fri|sat|sun)[a-z]*\.?,?\s+"
    r"(\d{1,2})\s+([a-z]+)"
    r"(?:\s*(?:\||,|\s)\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm))?"
    r"(?:\s*[-–]\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm))?", re.I)
_PRICE = re.compile(r"(?:AUD|\$)\s*([\d,]+(?:\.\d{2})?)", re.I)
_FREE = re.compile(r"complimentary|free (?:community|event|of charge)", re.I)


def page_event(text, studio_id, url, title=None, year=None, kind="workshop"):
    """One event from a studio's own event page. Returns None if the page has no
    parseable date — the caller reports that, it is never swallowed."""
    year = year or datetime.datetime.now(MELB).year
    m = _DATE_LINE.search(text)
    if not m:
        return None
    day, mon = int(m.group(1)), MONTHS.get(m.group(2).lower())
    if not mon:
        return None

    def hhmm(h, mi, ap):
        if not h:
            return None
        h = int(h) % 12 + (12 if (ap or "").lower() == "pm" else 0)
        return h, int(mi or 0)

    start_hm = hhmm(m.group(3), m.group(4), m.group(5) or m.group(8))
    end_hm = hhmm(m.group(6), m.group(7), m.group(8))
    try:
        d0 = datetime.date(year, mon, day)
    except ValueError:
        return None
    # A date already well past is next year's, not this year's.
    if (datetime.datetime.now(MELB).date() - d0).days > 60:
        d0 = datetime.date(year + 1, mon, day)
    st = datetime.datetime.combine(d0, datetime.time(*(start_hm or (0, 0))), tzinfo=MELB)
    en = (datetime.datetime.combine(d0, datetime.time(*end_hm), tzinfo=MELB)
          if end_hm else None)

    price = None
    if _FREE.search(text):
        price = 0
    pm = _PRICE.search(text)
    if pm:
        price = float(pm.group(1).replace(",", ""))
        price = int(price) if price == int(price) else price

    if not title:
        title = (text.strip().splitlines() or [""])[0].strip()[:80]
    return {
        "id": f"page:{url}",
        "studio": studio_id,
        "kind": kind,
        "title": title,
        "teacher": "",
        "starts": _iso(st),
        "ends": _iso(en) if en else "",
        "price": price,
        "url": url,
        "source": "page",
    }


# ---- Index pages that list many events (Warrior One) -----------------------
# page_event() above reads ONE event from a page, which is Within's model: a
# separate URL per workshop. Warrior One publishes the opposite shape — a single
# /workshops/ page listing every event, each as
#
#     SLOW FLOW TO YIN WITH LUCY
#     WED 2 SEPTEMBER 2026 | 10:45 AM – 12:00 PM @ MORNINGTON
#     INVESTMENT: $75
#     <prose>
#
# Pointing page_event() at that would have returned the first event, reported
# success, and silently dropped the other four — which is worse than failing,
# because the anomaly check only fires when a page yields NOTHING. Mark spotted
# the gap on 19 Aug 2026 by finding an event on their site that was not on ours.
# Hence a plural reader, and hence `expect` below.

_LIST_DATE = re.compile(
    r"^(?:mon|tue|wed|thu|fri|sat|sun)[a-z]*\.?\s+"
    r"(\d{1,2})\s+([a-z]+)\s*(\d{4})?"                       # 23 August [2026]
    r"(?:\s*[-–—]\s*(?:(?:mon|tue|wed|thu|fri|sat|sun)[a-z]*\.?\s+)?"
    r"(\d{1,2})\s+([a-z]+)\s*(\d{4})?)?"                     # – 18 September 2026
    r"(?:\s*\|\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)"          # | 10:45 AM
    r"(?:\s*[-–—]\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm))?)?"    # – 12:00 PM
    r"(?:\s*@\s*(.+?))?\s*$", re.I)                           # @ MORNINGTON
_INVEST = re.compile(r"(?:investment|price|cost)\s*:?(.*)", re.I)

# Warrior One sets its headings in caps as a design choice. "YIN, POETRY & CELLO
# WITH FRANKS" is styling, not how the words are written, and shouting it back on
# our page would be reproducing their CSS rather than their information.
_SMALL = {"a", "an", "and", "as", "at", "but", "by", "for", "from", "in", "into",
          "nor", "of", "on", "or", "the", "to", "with", "via"}
ACRONYMS = {"IKSRE", "YTT", "YIM"}          # extend by hand; guessing gets it wrong


def title_case(s):
    """Caps heading -> sentence-shaped title. Left alone if it is not all caps,
    because a studio that already writes its titles properly knows better."""
    if not s or s != s.upper():
        return s
    out, words = [], s.split()
    for i, w in enumerate(words):
        if w.strip(",.:;!?—-") in ACRONYMS:
            out.append(w)
        elif (w.lower().strip(",.:;!?—-") in _SMALL and 0 < i < len(words) - 1
              # A small word is only small mid-clause. After a dash or colon it
              # opens a subtitle: "Spring Resonance — A Spring Sound Journey".
              and not (words[i - 1][-1:] in "—–-:" or words[i - 1] in "—–")):
            out.append(w.lower())
        else:
            # "21-DAY" -> "21-Day", "SOUND" -> "Sound"
            out.append("-".join(p[:1].upper() + p[1:].lower() for p in w.split("-")))
    return " ".join(out)


def page_events(text, studio_id, url, year=None, kind="workshop",
                locations=None, expect=None):
    """Every event on a studio's index page.

    `locations` maps the "@ SUBURB" suffix to a studio id, because one Warrior
    One page covers Brighton, Mordialloc and Mornington. Without it every event
    would be filed under whichever studio happened to hold the config.

    `expect` is how many events this page yielded last time. Returning fewer is
    reported by the caller as an anomaly — a studio quietly restyling its page is
    the failure mode that loses events without anyone noticing."""
    year = year or datetime.datetime.now(MELB).year
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    out, problems = [], []

    for i, line in enumerate(lines):
        m = _LIST_DATE.match(line)
        if not m or i == 0:
            continue
        (d1, mon1, y1, d2, mon2, y2, sh, sm, sap, eh, em, eap, where_raw) = m.groups()
        m1, m2 = MONTHS.get((mon1 or "").lower()), MONTHS.get((mon2 or "").lower())
        if not m1:
            continue
        # "SAT 29 AUGUST – FRI 18 SEPTEMBER 2026": only the end carries the year.
        yr = int(y1 or y2 or year)
        try:
            d_start = datetime.date(yr, m1, int(d1))
        except ValueError:
            problems.append(f"{url}: unreadable date {line!r}")
            continue
        d_end = None
        if d2 and m2:
            try:
                d_end = datetime.date(int(y2 or yr), m2, int(d2))
            except ValueError:
                d_end = None

        def hm(h, mi, ap):
            if not h:
                return None
            return (int(h) % 12 + (12 if (ap or "").lower() == "pm" else 0), int(mi or 0))

        st_hm, en_hm = hm(sh, sm, sap), hm(eh, em, eap)
        st = datetime.datetime.combine(d_start, datetime.time(*(st_hm or (0, 0))), tzinfo=MELB)
        en = datetime.datetime.combine(d_end or d_start,
                                       datetime.time(*(en_hm or (23, 59))), tzinfo=MELB)

        title = lines[i - 1].strip()
        # An all-caps heading is theirs; sentence case means we grabbed prose.
        if len(title) > 90 or title.endswith("."):
            problems.append(f"{url}: no heading above {line!r}")
            continue

        price, where = None, (where_raw or "").strip()
        for nxt in lines[i + 1:i + 3]:
            if _LIST_DATE.match(nxt):
                break
            inv = _INVEST.match(nxt)
            if inv:
                body = inv.group(1)
                if _FREE.search(body) or re.search(r"complimentary", body, re.I):
                    pm = _PRICE.search(body)
                    # "COMPLIMENTARY FOR TRIBE MEMBERS | $225 FOR NON-MEMBERS" —
                    # the number a non-member actually pays is the honest one.
                    price = float(pm.group(1).replace(",", "")) if pm else 0
                else:
                    pm = _PRICE.search(body)
                    if pm:
                        price = float(pm.group(1).replace(",", ""))
                if price is not None and price == int(price):
                    price = int(price)
                break

        sid = studio_id
        if locations and where:
            sid = locations.get(where.upper(), studio_id)

        out.append({
            "id": f"page:{url}#{re.sub(r'[^a-z0-9]+', '-', title.lower())[:44]}",
            "studio": sid,
            "kind": kind,
            "title": title_case(title),
            "teacher": "",
            "starts": _iso(st),
            "ends": _iso(en),
            "price": price,
            "url": url,
            "source": "page",
        })

    if expect and len(out) < expect:
        problems.append(
            f"{url}: found {len(out)} event(s), expected at least {expect} — "
            f"the studio has probably restyled the page. Events may be missing.")
    return out, problems


# ---- Registry --------------------------------------------------------------
def merge_events(existing, fresh, covered_sources, today=None):
    """Fold freshly-pulled events into the registry.

    `covered_sources` is the set of sources that ran successfully this pass
    ("momence", "page"). Anything from a source that did NOT run is kept exactly
    as it was — the same partial-failure rule merge.py uses for classes, so a
    Momence outage can never wipe the events section.

    Manual entries (source "manual") are never touched by any pull. Past events
    are dropped once they are a day behind, so the registry does not grow
    without bound."""
    today = today or datetime.datetime.now(MELB).date()
    cutoff = (today - datetime.timedelta(days=1)).isoformat()

    kept = [e for e in existing
            if e.get("source") == "manual" or e.get("source") not in covered_sources]
    by_id = {e["id"]: e for e in kept}

    # A hand-written card may name the scraped ids it stands in for. Warrior One's
    # "Yin, Poetry & Cello" card has a caption and blurb someone wrote; the same
    # event scraped off their index page is thinner. Without this the two would sit
    # side by side, which is exactly the duplication that got Mark's attention on
    # 19 Aug (the same Sri Lanka retreat via two different URLs).
    superseded = {sid for e in kept for sid in (e.get("supersedes") or [])}

    for e in fresh:
        if e["id"] in superseded:
            continue
        prior = by_id.get(e["id"])
        if prior and prior.get("source") == "manual":
            continue                       # a human overrode this one; leave it
        by_id[e["id"]] = e

    # Expiry precedence must match build_events.expiry() exactly: `until` first,
    # because that is the only date a hand-written card carries. Reading `ends` or
    # `starts` alone made every manual card look undated and therefore expired —
    # a single --publish would have deleted all fifteen of them. Found 19 Aug 2026
    # by an assertion, not by anything going wrong in production, which is luck.
    # An entry with no date at all is evergreen (Warrior One's 200-hour training)
    # and is never dropped.
    out = [e for e in by_id.values()
           if (e.get("until") or e.get("ends") or e.get("starts") or "9999") >= cutoff]
    out.sort(key=lambda e: (e.get("starts", ""), e.get("studio", ""), e.get("title", "")))
    return out


def load(path):
    try:
        return json.loads(open(path, encoding="utf-8").read()).get("events", [])
    except (FileNotFoundError, ValueError):
        return []


def save(path, events):
    open(path, "w", encoding="utf-8").write(
        json.dumps({"events": events}, indent=2, ensure_ascii=False) + "\n")
