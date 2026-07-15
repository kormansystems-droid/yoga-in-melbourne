#!/usr/bin/env python3
"""
normalizers.py — turn each platform's raw feed into platform-agnostic rows.

A row is exactly what merge.py expects, plus a sub flag:
    {"studio": <studio_id>, "teacher": <raw name as the feed spells it>,
     "day": "Mon", "start": "06:00", "time": "6:00–7:00 AM",
     "class": "Vinyasa Flow", "sub": False}

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


def _row(studio_id, teacher, start, end, cls, sub):
    return {
        "studio": studio_id, "teacher": (teacher or "").strip(),
        "day": DAY_ABBR.get(start.strftime("%A"), start.strftime("%a")),
        "start": start.strftime("%H:%M"),
        "time": _time_range(start, end),
        "class": (cls or "").strip(),
        "sub": bool(sub),
    }


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
        orig = s.get("originalTeacher")
        sub = bool(orig and orig != s.get("teacher"))
        teachers = [s.get("teacher")] + [
            (t.get("name") if isinstance(t, dict) else t) for t in (s.get("additionalTeachers") or [])
        ]
        for tname in [t for t in teachers if t]:
            rows.append(_row(studio_id, tname, st, en, s.get("sessionName", ""), sub))
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
        sub = "bw-session__sub" in staff_raw or "substitute" in staff_raw.lower()
        staff = H.unescape(re.sub(r"<[^>]+>", "", re.sub(r'<span class="bw-session__sub".*?</span>', "", staff_raw, flags=re.S))).strip()
        key = (staff, start.isoformat(), name)
        if key in seen:
            continue
        seen.add(key)
        rows.append(_row(studio_id, staff, start, end, name, sub))
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
            sub = any("sub" in l.lower() for l in leaves)
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
            rows.append(_row(studio_id, teacher, start, end, cls, sub))
    return rows
