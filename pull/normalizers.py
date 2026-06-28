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
def momence_rows(payload, studio_id):
    """payload = list of Momence session dicts (UTC times)."""
    rows = []
    for s in payload:
        if s.get("isCancelled"):
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
