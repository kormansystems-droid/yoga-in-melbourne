#!/usr/bin/env python3
"""
normalizers.py — turn each platform's raw feed into platform-agnostic rows.

A row is exactly what merge.py expects:
    {"studio": <studio_id>, "teacher": <raw name as the feed spells it>,
     "date": "2026-08-19", "day": "Mon", "start": "06:00",
     "time": "6:00–7:00 AM", "class": "Vinyasa Flow"}

`date` is the single fact that matters: on this date, at this studio, at this
time, this is the teacher. Rosters churn constantly — teachers travel, cover for
each other, hand slots over — so nobody "owns" a slot and no feed field says who
does. Momence's `originalTeacher` only records that an assignment was edited; it
is bookkeeping, not a fact about the world, and it is deliberately not read.

A row carries no `date` only when its feed genuinely has none: Inndriya publishes
a weekly grid with no dates in it at all. Undated rows still render on a profile
as a weekly timetable, but nothing downstream may use them to claim a class runs
on a given day — see build_story_cards.classes_for.

Two platforms are solved and validated against real captured data:
  - Momence  (Grass Roots host 34431, Here Yoga host 40780): clean JSON API.
  - Mindbody healcode widget (Within): schedule rendered as bw-session HTML.
Happy Melon (Mindbody branded-web "Schedules V2") is pending its own endpoint.
"""
import re, datetime, html as H

try:
    from zoneinfo import ZoneInfo
    MELB = ZoneInfo("Australia/Melbourne")          # DST-safe
except Exception:
    MELB = datetime.timezone(datetime.timedelta(hours=10))  # AEST fallback

DAY_ABBR = {"Monday": "Mon", "Tuesday": "Tue", "Wednesday": "Wed", "Thursday": "Thu",
            "Friday": "Fri", "Saturday": "Sat", "Sunday": "Sun"}


def _time_range(start, end):
    s = start.strftime("%-I:%M")
    e = end.strftime("%-I:%M %p") if end else ""
    return f"{s}\u2013{e}".strip("\u2013")


def _row(studio_id, teacher, start, end, cls, url=None, dated=True):
    """`dated=False` for a feed that publishes a weekly grid rather than sessions
    (Inndriya): `start` is then a synthetic next-occurrence stamp used only to
    format day/time, so emitting it as a date would be inventing a fact.

    `url` is optional and deep-links to that specific session's booking page.
    Where a feed exposes one, the profile links the class row straight at it;
    where it does not, the row falls back to the studio's booking page. Adding it
    to a normalizer is the whole change — merge and the templates already carry
    it through."""
    row = {
        "studio": studio_id, "teacher": (teacher or "").strip(),
        "day": DAY_ABBR.get(start.strftime("%A"), start.strftime("%a")),
        "start": start.strftime("%H:%M"),
        "time": _time_range(start, end),
        "class": (cls or "").strip(),
    }
    if dated:
        row["date"] = start.date().isoformat()
    if url:
        row["url"] = str(url).strip()
    return row


# ---- Momence ---------------------------------------------------------------
def momence_rows(payload, studio_id, location=None):
    """payload = list of Momence session dicts (UTC times).
    If `location` is given, keep only sessions at that venue — a single Momence
    host can serve multiple locations (e.g. Here Yoga Malvern + Port Melbourne)."""
    rows = []
    for s in payload:
        if s.get("isCancelled"):
            continue
        if location and str(s.get("location", "")).strip() != location:
            continue
        st = datetime.datetime.fromisoformat(s["startsAt"].replace("Z", "+00:00")).astimezone(MELB)
        en = datetime.datetime.fromisoformat(s["endsAt"].replace("Z", "+00:00")).astimezone(MELB)
        teachers = [s.get("teacher")] + [
            (t.get("name") if isinstance(t, dict) else t) for t in (s.get("additionalTeachers") or [])
        ]
        for tname in [t for t in teachers if t]:
            rows.append(_row(studio_id, tname, st, en, s.get("sessionName", "")))
    return rows


# ---- Mindbody Public API (v6 GetClasses) -----------------------------------
def mindbody_rows(payload, studio_id, location=None):
    """payload = list of Mindbody v6 Class dicts (from GetClasses).
    StartDateTime/EndDateTime are the site's LOCAL time (no offset) — for a
    Melbourne studio that's already Melbourne, so we just localise it. If
    `location` is given, keep only that venue (a Mindbody site can host several,
    e.g. Warrior One Brighton / Mordialloc / Mornington)."""
    rows = []
    for c in payload:
        if c.get("IsCanceled"):
            continue
        if location and str((c.get("Location") or {}).get("Name", "")).strip() != location:
            continue
        staff = c.get("Staff") or {}
        tname = (staff.get("Name")
                 or (staff.get("FirstName", "") + " " + staff.get("LastName", "")).strip())
        if not tname or not c.get("StartDateTime"):
            continue
        st = datetime.datetime.fromisoformat(c["StartDateTime"]).replace(tzinfo=MELB)
        en = datetime.datetime.fromisoformat(c["EndDateTime"]).replace(tzinfo=MELB)
        cname = (c.get("ClassDescription") or {}).get("Name", "")
        rows.append(_row(studio_id, tname, st, en, cname))
    return rows


# ---- Mindbody healcode -----------------------------------------------------
def healcode_rows(html, studio_id):
    """html = rendered DOM containing bw-session blocks (datetime attrs are local)."""
    rows = []
    seen = set()
    for m in re.finditer(r'class="bw-session\b.*?(?=class="bw-session\b|class="bw-widget__day"|\Z)', html, re.S):
        blk = m.group(0)
        dt = re.search(r'hc_starttime"\s+datetime="([0-9T:\-]+)"', blk)
        et = re.search(r'hc_endtime"\s+datetime="([0-9T:\-]+)"', blk)
        nm = re.search(r'bw-session__name">(.*?)</div>', blk, re.S)
        sf = re.search(r'bw-session__staff"[^>]*>(.*?)</div>', blk, re.S)
        if not (dt and sf):
            continue
        start = datetime.datetime.fromisoformat(dt.group(1))
        end = datetime.datetime.fromisoformat(et.group(1)) if et else None
        name = ""
        if nm:
            n = re.sub(r'<span class="bw-session__type"[^>]*>.*?</span>', "", nm.group(1), flags=re.S)
            name = H.unescape(re.sub(r"<[^>]+>", "", n)).strip()
        staff_raw = sf.group(1)
        staff = H.unescape(re.sub(r"<[^>]+>", "", re.sub(r'<span class="bw-session__sub".*?</span>', "", staff_raw, flags=re.S))).strip()
        key = (staff, start.isoformat(), name)
        if key in seen:
            continue
        seen.add(key)
        rows.append(_row(studio_id, staff, start, end, name))
    return rows


# ---- go.mindbody branded-web V2 (Warrior One) ------------------------------
_GMB_NOISE = {"show details", "book my mat", "book", "waitlist", "sign up",
              "join waitlist", "add to calendar", "full", "cancelled", "sold out"}
_GMB_MONTHS = {m: i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}

def gomindbody_rows(days, studio_id):
    """days = [{'date': 'Tuesday, Jul 7', 'cards': [[leaf, leaf, ...], ...]}, ...]
    from the rendered V2 widget. Each card's leaves are the ordered text nodes:
    time, duration, class, teacher, (Show Details), location, (Book). Times are
    already Melbourne-local (widget: 'displayed in the location's timezone')."""
    now = datetime.datetime.now(MELB)
    rows, seen = [], set()
    for day in days or []:
        dm = re.search(r"([A-Z][a-z]{2})[a-z]*\s+(\d{1,2})", day.get("date", ""))  # 'Jul 7'
        if not dm:
            continue
        mon = _GMB_MONTHS.get(dm.group(1))
        if not mon:
            continue
        dnum = int(dm.group(2))
        try:
            date0 = datetime.date(now.year, mon, dnum)
        except ValueError:
            continue
        if (now.date() - date0).days > 30:          # Dec -> Jan rollover
            try:
                date0 = datetime.date(now.year + 1, mon, dnum)
            except ValueError:
                continue
        for leaves in day.get("cards", []):
            leaves = [H.unescape(str(x)).strip() for x in leaves if str(x).strip()]
            time_s = next((l for l in leaves if re.match(r"^\d{1,2}:\d{2}\s?[AP]M$", l, re.I)), None)
            if not time_s:
                continue
            dur_s = next((l for l in leaves if re.match(r"^\d+\s*min$", l, re.I)), None)
            loc_s = next((l for l in leaves if re.search(r"warrior one|studio", l, re.I)), "")
            # meaningful content leaves, in order: [class, teacher]
            core = [l for l in leaves
                    if l not in (time_s, dur_s, loc_s)
                    and l.lower() not in _GMB_NOISE
                    and not re.match(r"^\d+\s*min$", l, re.I)
                    and not re.match(r"^\d{1,2}:\d{2}\s?[AP]M$", l, re.I)]
            cls = core[0] if len(core) >= 1 else ""
            teacher = core[1] if len(core) >= 2 else ""
            try:
                t = datetime.datetime.strptime(time_s.upper().replace(" ", ""), "%I:%M%p").time()
            except ValueError:
                continue
            start = datetime.datetime.combine(date0, t)
            mins = int(re.match(r"(\d+)", dur_s).group(1)) if dur_s else 60
            end = start + datetime.timedelta(minutes=mins)
            key = (teacher, start.isoformat(), cls)
            if key in seen:
                continue
            seen.add(key)
            rows.append(_row(studio_id, teacher, start, end, cls))
    return rows


# ---- Squarespace plain-HTML weekly timetable (Inndriya) --------------------
_SQS_DAY = {"MONDAY": 0, "TUESDAY": 1, "WEDNESDAY": 2, "THURSDAY": 3,
            "FRIDAY": 4, "SATURDAY": 5, "SUNDAY": 6}
_SQS_SMALL = {"to", "the", "and", "of", "with", "for", "a", "in"}

def _sqs_title(s):
    out = []
    for i, w in enumerate(s.strip().split()):
        lw = w.lower()
        out.append(lw if (i and lw in _SQS_SMALL) else (w[:1].upper() + w[1:].lower()))
    return " ".join(out)

_SQS_LINE = re.compile(
    r"^\s*(\d{1,2})(?:[.:](\d{2}))?\s*([AP]M)?\s*[-\u2013]\s*"
    r"(\d{1,2})(?:[.:](\d{2}))?\s*([AP]M)\s+(.+?)\s*,\s*([^,]+?)\s*$", re.I)

def squarespace_rows(page_html, studio_id):
    """page_html = raw Squarespace page HTML. The weekly timetable is plain text
    in <p> blocks: a MONDAY..SUNDAY header, then lines like
    '9.30-10.30AM SLOW FLOW, Sary Davis' / '6-7AM FLOW, Phil Kayumba' /
    '11.15AM - 12.30PM YIN + YOGA NIDRA, Jori Sandler'.
    The grid is weekly (no dates), so each row is stamped on the NEXT occurrence
    of its weekday purely to drive day/start/time formatting. A non-class,
    non-header line CLEARS the day context, so the dated one-off events and
    pricing copy lower on the page are never swallowed as classes."""
    text = re.sub(r"(?i)<\s*br[^>]*>", "\n", page_html)
    text = re.sub(r"(?i)</\s*(p|div|h[1-6])\s*>", "\n", text)
    text = H.unescape(re.sub(r"<[^>]+>", "", text))
    today = datetime.datetime.now(MELB).date()
    rows, day_idx, seen = [], None, set()
    for line in text.splitlines():
        line = line.replace("\u00a0", " ").strip()
        if not line:
            continue
        up = line.upper().rstrip(":")
        if up in _SQS_DAY:
            day_idx = _SQS_DAY[up]
            continue
        m = _SQS_LINE.match(line)
        if not m:
            day_idx = None          # left the timetable block
            continue
        if day_idx is None:
            continue                # a dated event line, not the weekly grid
        h1, m1, ap1, h2, m2, ap2, cls, teacher = m.groups()
        ap1, ap2 = (ap1 or "").upper(), ap2.upper()
        eh = int(h2) % 12 + (12 if ap2 == "PM" else 0)
        if ap1:
            sh = int(h1) % 12 + (12 if ap1 == "PM" else 0)
        else:
            sh = int(h1) % 12 + (12 if ap2 == "PM" else 0)
            if sh > eh:             # '11-12.30PM' style morning start
                sh -= 12
        date0 = today + datetime.timedelta(days=(day_idx - today.weekday()) % 7)
        start = datetime.datetime.combine(date0, datetime.time(sh, int(m1 or 0)), tzinfo=MELB)
        end = datetime.datetime.combine(date0, datetime.time(eh, int(m2 or 0)), tzinfo=MELB)
        key = (teacher.strip(), start.isoformat(), cls)
        if key in seen:
            continue
        seen.add(key)
        rows.append(_row(studio_id, teacher, start, end, _sqs_title(cls), dated=False))
    return rows
