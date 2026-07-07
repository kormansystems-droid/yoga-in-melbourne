#!/usr/bin/env python3
"""
pull.py — PRODUCTION: refresh every teacher's timetable from the studio feeds.

How each studio is pulled is declared in data/schedule.json, in a "feed" block
on each studio — never in this file:
    {"type": "momence",  "host": 34431}                  -> clean JSON API
    {"type": "healcode", "page": "https://.../timetable"} -> rendered widget
    {"type": "manual", ...}                               -> skipped, left as-is

For every studio it can read, it fetches the live schedule, normalizes it
(pull/normalizers.py), and merge.py folds the result into schedule.json —
alias-matched, substitute-flagged, with partial-failure safety (a feed that
fails or is "manual" leaves that studio's existing classes untouched). Then it
rebuilds the profile pages. The workflow opens a Pull Request, so nothing goes
live until a human reviews and merges.

Adding a studio to the automation = one registry entry with a feed block.
Belongs in the REAL site repo (with build_profiles.py, templates/, data/, *.html).
"""
import json, sys, datetime, subprocess
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
import normalizers as N
import merge as M

ROOT = Path(__file__).resolve().parent.parent
SCHED = ROOT / "data" / "schedule.json"
ANOM = Path(__file__).resolve().parent / "_anomalies.md"
STATE = Path(__file__).resolve().parent / "_feed_state.json"
DARK_ESCALATE = 3  # consecutive failed runs before a feed is called "likely broken", not a blip
FORWARD_DAYS = 7   # Momence: pull a rolling week — covers every weekly slot once, keeps fetches light
SESSION_TYPES = ["course-class", "fitness", "retreat", "special-event", "special-event-new"]
UA = {"User-Agent": "Mozilla/5.0 (compatible; YIM-timetable/1.0)"}

# Mindbody bw-widget ids for the direct load_markup endpoint (no browser needed).
# studio_id -> widget id. A feed may also carry its own "widget" to override this.
HEALCODE_WIDGETS = {"within-south-yarra": "188058"}


def write_anomalies(failed, missing, unknown_studios, recovered):
    """Write a human-readable anomaly report for the workflow to raise as an issue.
    Anomalies never block publishing — clean studios still go live; this is a heads-up.
    `failed`  = list of (sid, err, dark_runs, since); escalates at DARK_ESCALATE+ runs.
    `missing` = registered teachers who had classes last run but zero this run at a
                covered studio (a real disappearance — NOT the ~150 non-profiled teachers
                in the feeds, which are normal and never flagged)."""
    lines = []
    escalated = [f for f in failed if f[2] >= DARK_ESCALATE]
    blips = [f for f in failed if f[2] < DARK_ESCALATE]
    if escalated:
        lines.append(f"**🔴 Feeds DOWN {DARK_ESCALATE}+ runs — likely broken, not a blip. "
                     "Fix the scrape, switch the studio to `manual`, or move it to the official API:**")
        for sid, err, runs, since in escalated:
            lines.append(f"- `{sid}` — down **{runs} runs** since {since}. Last error: {err}")
    if blips:
        lines.append("")
        lines.append("**🟡 Feed down this run** — kept last-good data; only a concern if it repeats:")
        for sid, err, runs, since in blips:
            lines.append(f"- `{sid}` — {err}  _(run {runs} of the streak)_")
    if recovered:
        lines.append("")
        lines.append("**🟢 Recovered** — pulling cleanly again:")
        for sid, since in recovered:
            lines.append(f"- `{sid}` — was down since {since}")
    if missing:
        lines.append("")
        lines.append("**Profiled teacher dropped from the feed** — had classes last run, zero this "
                     "run at a studio that pulled cleanly. Likely their name changed in the studio's "
                     "system (update the alias in `schedule.json`) or they stopped teaching there:")
        for name in missing:
            lines.append(f"- {name}")
    if unknown_studios:
        lines.append("")
        lines.append("**Rows for unknown studio ids** — add them to the studios registry:")
        for sid, count in sorted(unknown_studios.items()):
            lines.append(f"- `{sid}` — {count} row(s)")
    if lines:
        header = ("The automated timetable pull flagged items needing a look. Schedules that "
                  "pulled cleanly were published as normal; nothing below blocked them.\n\n")
        ANOM.write_text(header + "\n".join(lines) + "\n")
        print(f"\n⚠ anomalies written to {ANOM.name} — the workflow will raise/append a GitHub issue.")
    else:
        print("\n✓ clean run — no anomalies.")


def momence_fetch(host):
    base = f"https://readonly-api.momence.com/host-plugins/host/{host}/host-schedule/sessions"
    nowdt = datetime.datetime.now(datetime.timezone.utc)
    fmt = "%Y-%m-%dT%H:%M:%S.000Z"
    frm = nowdt.strftime(fmt)
    to = (nowdt + datetime.timedelta(days=FORWARD_DAYS)).strftime(fmt)
    payload, page = [], 0
    while True:
        q = [("sessionTypes[]", t) for t in SESSION_TYPES] + \
            [("fromDate", frm), ("toDate", to), ("pageSize", "50"), ("page", str(page)), ("timeZone", "UTC")]
        req = Request(base + "?" + urlencode(q), headers=UA)
        d = json.loads(urlopen(req, timeout=30).read().decode("utf-8"))
        payload += d.get("payload", [])
        total = d.get("pagination", {}).get("totalCount", len(payload))
        page += 1
        if page * 50 >= total or page > 40:
            break
    return payload


def healcode_fetch(feed, sid):
    """Direct load_markup GET — no browser. Returns the week's bw-session HTML.
    feed = {"type":"healcode","widget":"188058", ...}. The bw-widget returns 7 days
    from start_date; datetimes in the markup are already Melbourne-local."""
    wid = feed.get("widget") or HEALCODE_WIDGETS.get(sid)
    if not wid:
        raise RuntimeError(f"no healcode widget id for '{sid}'")
    start = datetime.datetime.now(ZoneInfo("Australia/Melbourne")).strftime("%Y-%m-%d")
    url = (f"https://widgets.mindbodyonline.com/widgets/schedules/{wid}"
           f"/load_markup?options[start_date]={start}")
    raw = urlopen(Request(url, headers=UA), timeout=45).read().decode("utf-8")
    try:
        data = json.loads(raw)
        return data.get("class_sessions") or data.get("contents") or raw
    except (ValueError, AttributeError):
        return raw  # response was already raw markup


def main():
    if ANOM.exists():
        ANOM.unlink()  # start clean; only present if this run finds something
    schedule = json.loads(SCHED.read_text())
    rows, covered, failed = [], [], []

    for sid, meta in schedule["studios"].items():
        feed = meta.get("feed", {})
        ftype = feed.get("type")
        if ftype not in ("momence", "healcode"):
            continue  # manual / unconfigured — left untouched, not expected to auto-pull
        try:
            if ftype == "momence":
                r = N.momence_rows(momence_fetch(feed["host"]), sid)
            else:  # healcode
                r = N.healcode_rows(healcode_fetch(feed, sid), sid)
            if not r:
                # A feed that responds but yields nothing is a FAILURE, never
                # "this studio now has no classes" — otherwise a block, challenge,
                # or markup change would silently WIPE a real schedule.
                raise RuntimeError("feed returned 0 sessions (block or markup change?)")
            rows += r
            covered.append(sid)
            print(f"  {sid}: {len(r)} rows [{ftype}]")
        except Exception as e:
            failed.append((sid, str(e)))
            print(f"  {sid}: FAILED — {e}  (kept last-good)")

    # ---- feed-failure streak tracking (dark-day escalation) ----
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    today = datetime.date.today().isoformat()
    new_state, recovered = {}, []
    for sid, _err in failed:
        prev = state.get(sid, {})
        new_state[sid] = {"dark_runs": prev.get("dark_runs", 0) + 1,
                          "since": prev.get("since", today)}
    for sid in covered:
        if sid in state:                       # was failing, pulled cleanly now
            recovered.append((sid, state[sid].get("since", "?")))
    STATE.write_text(json.dumps(new_state, indent=2) + "\n")
    failed_detail = [(sid, err, new_state[sid]["dark_runs"], new_state[sid]["since"])
                     for sid, err in failed]

    if not covered:
        print("No studios pulled successfully; leaving schedule.json untouched.")
        write_anomalies(failed_detail, [], {}, recovered)
        return

    # count each profiled teacher's classes AT COVERED STUDIOS, before the merge overwrites
    covset = set(covered)
    def _counts(sched):
        return {n: sum(1 for c in t.get("classes", []) if c.get("studio") in covset)
                for n, t in sched.get("teachers", {}).items()}
    old_counts = _counts(schedule)

    merged, report = M.merge(schedule, rows, covered)
    SCHED.write_text(json.dumps(merged, indent=2, ensure_ascii=False))
    print(f"\nmerged {report['matched']} rows; covered: {', '.join(covered)}")

    new_counts = _counts(merged)
    # only a REAL disappearance: had classes at a covered studio last run, none now.
    missing = sorted(n for n in old_counts if old_counts[n] > 0 and new_counts.get(n, 0) == 0)

    write_anomalies(failed_detail, missing, report["unknown_studios"], recovered)

    subprocess.run([sys.executable, str(ROOT / "build_profiles.py")], check=True, cwd=str(ROOT))
    print("profiles rebuilt.")


if __name__ == "__main__":
    main()
