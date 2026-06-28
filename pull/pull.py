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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import normalizers as N
import merge as M

ROOT = Path(__file__).resolve().parent.parent
SCHED = ROOT / "data" / "schedule.json"
SESSION_TYPES = ["course-class", "fitness", "retreat", "special-event", "special-event-new"]
UA = {"User-Agent": "Mozilla/5.0 (compatible; YIM-timetable/1.0)"}


def momence_fetch(host):
    base = f"https://readonly-api.momence.com/host-plugins/host/{host}/host-schedule/sessions"
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    payload, page = [], 0
    while True:
        q = [("sessionTypes[]", t) for t in SESSION_TYPES] + \
            [("fromDate", now), ("pageSize", "50"), ("page", str(page)), ("timeZone", "UTC")]
        req = Request(base + "?" + urlencode(q), headers=UA)
        d = json.loads(urlopen(req, timeout=30).read().decode("utf-8"))
        payload += d.get("payload", [])
        total = d.get("pagination", {}).get("totalCount", len(payload))
        page += 1
        if page * 50 >= total or page > 40:
            break
    return payload


def healcode_fetch(url):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        try:
            pg.goto(url, wait_until="networkidle", timeout=60000)
        except Exception:
            pass
        pg.wait_for_timeout(6000)
        html = pg.content()
        b.close()
    return html


def main():
    schedule = json.loads(SCHED.read_text())
    rows, covered = [], []

    for sid, meta in schedule["studios"].items():
        feed = meta.get("feed", {})
        ftype = feed.get("type")
        try:
            if ftype == "momence":
                r = N.momence_rows(momence_fetch(feed["host"]), sid)
            elif ftype == "healcode":
                r = N.healcode_rows(healcode_fetch(feed["page"]), sid)
                if not r:
                    raise RuntimeError("no sessions parsed (markup change or block)")
            else:
                continue  # manual / unconfigured — left untouched
            rows += r
            covered.append(sid)
            print(f"  {sid}: {len(r)} rows [{ftype}]")
        except Exception as e:
            print(f"  {sid}: FAILED — {e}  (left untouched)")

    if not covered:
        print("No studios pulled successfully; leaving schedule.json untouched.")
        return

    merged, report = M.merge(schedule, rows, covered)
    SCHED.write_text(json.dumps(merged, indent=2, ensure_ascii=False))
    print(f"\nmerged {report['matched']} rows; covered: {', '.join(covered)}")
    if report["unmatched_names"]:
        print("unmatched (unregistered teachers, ignored):",
              ", ".join(sorted(report["unmatched_names"])))

    subprocess.run([sys.executable, str(ROOT / "build_profiles.py")], check=True, cwd=str(ROOT))
    print("profiles rebuilt.")


if __name__ == "__main__":
    main()
