#!/usr/bin/env python3
"""
merge.py — fold normalized class rows from the studio feeds into data/schedule.json.

Pipeline position:
    recon/fetch (per platform)  ->  normalize  ->  [normalized.json]  ->  merge.py  ->  data/schedule.json  ->  build_profiles.py

A "normalized row" is platform-agnostic and looks like:
    {"studio": "<studio_id>", "teacher": "<raw name as the feed spells it>",
     "day": "Mon", "start": "06:00", "time": "6:00–7:00 AM", "class": "Vinyasa Flow"}

merge.py does three jobs and nothing platform-specific:
  1. Name matching — maps each feed's raw teacher string to a canonical teacher
     via the per-teacher `aliases` list already in schedule.json. Unmatched names
     are reported, never guessed.
  2. Partial-failure safety — only studios listed in `covered` are rewritten. If a
     feed failed this run and its studio isn't covered, every teacher keeps their
     existing classes for that studio. A broken Mindbody pull can never silently
     wipe Warrior One off every profile.
  3. Dedup + write — collapses the pulled window to unique (studio, day, start,
     class) rows per teacher and writes schedule.json, preserving the studios
     registry and each teacher's aliases/pronoun untouched.
"""

import json, sys, argparse
from pathlib import Path

DAY_ORDER = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}


def load(path):
    return json.loads(Path(path).read_text())


def alias_index(teachers):
    """lowercased alias / canonical name -> canonical teacher key."""
    idx = {}
    for canonical, rec in teachers.items():
        idx[canonical.lower()] = canonical
        for a in rec.get("aliases", []):
            idx[a.lower().strip()] = canonical
    return idx


def merge(schedule, rows, covered):
    studios = schedule["studios"]
    teachers = schedule["teachers"]
    idx = alias_index(teachers)
    covered = set(covered)

    report = {"unmatched_names": {}, "unknown_studios": {}, "matched": 0}

    # collect new classes per teacher, only for covered studios
    new_by_teacher = {name: set() for name in teachers}
    for r in rows:
        sid = r["studio"]
        if sid not in studios:
            report["unknown_studios"][sid] = report["unknown_studios"].get(sid, 0) + 1
            continue
        if sid not in covered:
            continue  # ignore rows for studios we didn't formally cover this run
        canonical = idx.get(r["teacher"].lower().strip())
        if canonical is None:
            report["unmatched_names"][r["teacher"]] = report["unmatched_names"].get(r["teacher"], 0) + 1
            continue
        new_by_teacher[canonical].add((sid, r["day"], r["start"], r["time"], r["class"], bool(r.get("sub"))))
        report["matched"] += 1

    # rebuild each teacher's class list: keep uncovered-studio classes, replace covered ones
    for name, rec in teachers.items():
        kept = [c for c in rec.get("classes", []) if c["studio"] not in covered]
        fresh = [
            ({"studio": sid, "day": day, "time": time, "class": cls, "sub": True}
             if sub else {"studio": sid, "day": day, "time": time, "class": cls})
            for (sid, day, start, time, cls, sub) in new_by_teacher[name]
        ]
        # stable sort: studio registry order, then weekday, then start time
        sid_order = {sid: i for i, sid in enumerate(studios)}
        start_of = {(c["studio"], c["day"], c["time"], c["class"]): "00:00" for c in kept}
        for (sid, day, start, time, cls, sub) in new_by_teacher[name]:
            start_of[(sid, day, time, cls)] = start
        combined = kept + fresh
        combined.sort(key=lambda c: (
            sid_order.get(c["studio"], 99),
            DAY_ORDER.get(c["day"], 99),
            start_of.get((c["studio"], c["day"], c["time"], c["class"]), "00:00"),
        ))
        rec["classes"] = combined

    return schedule, report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--schedule", default="data/schedule.json")
    ap.add_argument("--rows", required=True, help="normalized rows JSON (list)")
    ap.add_argument("--covered", required=True,
                    help="comma-separated studio ids actually pulled this run")
    ap.add_argument("--out", default=None, help="defaults to --schedule (in place)")
    a = ap.parse_args()

    schedule = load(a.schedule)
    rows = load(a.rows)
    covered = [s.strip() for s in a.covered.split(",") if s.strip()]

    merged, report = merge(schedule, rows, covered)
    out = a.out or a.schedule
    Path(out).write_text(json.dumps(merged, indent=2, ensure_ascii=False))

    print(f"merged {report['matched']} class rows -> {out}")
    print(f"covered studios: {', '.join(covered)}")
    if report["unmatched_names"]:
        print("⚠ unmatched teacher names (add to aliases in schedule.json):")
        for n, c in sorted(report["unmatched_names"].items()):
            print(f"    {n!r}  ({c} classes)")
    if report["unknown_studios"]:
        print("⚠ rows for unknown studio ids (add to studios registry):")
        for s, c in sorted(report["unknown_studios"].items()):
            print(f"    {s!r}  ({c} rows)")


if __name__ == "__main__":
    main()
