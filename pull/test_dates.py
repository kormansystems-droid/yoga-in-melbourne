#!/usr/bin/env python3
"""Regression test for the 18 Aug 2026 On the Mat failure.

Emma Strembickyj was announced into three classes on a Wednesday she was
overseas. Her Kozen slots that day were taught by Fai Mos; the row that put her
on the card came from the FOLLOWING Wednesday, because schedule.json held a
weekday pattern with no dates in it.

Run: python3 pull/test_dates.py
"""
import sys, datetime, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import normalizers, merge
import build_story_cards as story

FAILS = []
def check(name, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + name + (f"   {detail}" if detail and not cond else ""))
    if not cond: FAILS.append(name)

def sess(start_utc, end_utc, name, teacher, original):
    return {"startsAt": start_utc, "endsAt": end_utc, "sessionName": name,
            "teacher": teacher, "originalTeacher": original, "isCancelled": False,
            "additionalTeachers": []}

# Kozen, exactly as the live feed reads tonight (Melbourne = UTC+10).
payload = [
    sess("2026-08-19T08:15:00Z", "2026-08-19T09:15:00Z", "Flow Class", "Fai Mos", "Emma Strembickyj"),
    sess("2026-08-19T09:30:00Z", "2026-08-19T10:30:00Z", "Yin Class",  "Fai Mos", "Emma Strembickyj"),
    sess("2026-08-26T08:15:00Z", "2026-08-26T09:15:00Z", "Flow Class", "Emma Strembickyj", "Emma Strembickyj"),
    sess("2026-08-26T09:30:00Z", "2026-08-26T10:30:00Z", "Yin Class",  "Emma Strembickyj", "Emma Strembickyj"),
]
rows = normalizers.momence_rows(payload, "kozen-yoga-hawthorn")

check("every row carries a date", all("date" in r for r in rows))
check("originalTeacher is never read",
      all("Emma" not in r["teacher"] for r in rows if r["date"] == "2026-08-19"),
      json.dumps([r for r in rows if r["date"] == "2026-08-19"]))
check("no sub flag survives", all("sub" not in r for r in rows))
check("Fai Mos is named on the 19th",
      {r["teacher"] for r in rows if r["date"] == "2026-08-19"} == {"Fai Mos"})

schedule = {
    "studios": {"kozen-yoga-hawthorn": {"name": "Kozen", "location": "Hawthorn",
                                        "book": "https://example.com", "feed": {"type": "momence"}}},
    "suppressed": [],
    "teachers": {
        "Emma Strembickyj": {"name": {"given": "Emma", "family": "Strembickyj"},
                             "aliases": ["Emma Strembickyj"], "classes": []},
        "Fai Mos": {"name": {"given": "Fai", "family": "Mos"},
                    "aliases": ["Fai Mos"], "classes": []},
    },
}
merged, report = merge.merge(schedule, rows, covered=["kozen-yoga-hawthorn"])
emma = merged["teachers"]["Emma Strembickyj"]["classes"]
fai  = merged["teachers"]["Fai Mos"]["classes"]

check("Emma keeps a weekly Wed pattern", [c["day"] for c in emma] == ["Wed", "Wed"], str(emma))
check("Emma's dates are the 26th only",
      all(c["dates"] == ["2026-08-26"] for c in emma), json.dumps(emma))
check("Fai Mos's dates are the 19th only",
      all(c["dates"] == ["2026-08-19"] for c in fai), json.dumps(fai))

wed19 = datetime.date(2026, 8, 19)
wed26 = datetime.date(2026, 8, 26)
items19 = story.classes_for(merged, "Wed", wed19)
items26 = story.classes_for(merged, "Wed", wed26)

check("THE BUG: Emma is not announced on the 19th",
      not any(i["teacher"] == "Emma Strembickyj" for i in items19),
      json.dumps([i["teacher"] for i in items19]))
check("Fai Mos is announced on the 19th",
      sorted({i["teacher"] for i in items19}) == ["Fai Mos"])
check("Emma is announced on the 26th",
      sorted({i["teacher"] for i in items26}) == ["Emma Strembickyj"])

# An undated row — Inndriya's live weekly grid, or Warrior One's hand-verified
# timetable. These ARE announced: undated is not the same as unknown, and dropping
# them deleted Rayne Watkin from On the Mat entirely. The asymmetry is the point —
# a dated row must match, an undated row rides on the weekly timetable.
merged["teachers"]["Fai Mos"]["classes"].append(
    {"studio": "kozen-yoga-hawthorn", "day": "Wed", "time": "9:00–10:00 AM", "class": "Undated Grid"})
u19 = story.classes_for(merged, "Wed", wed19)
check("undated rows ARE announced", any(i["class"] == "Undated Grid" for i in u19))
check("undated rows are flagged unconfirmed",
      all(not i["confirmed"] for i in u19 if i["class"] == "Undated Grid"))
check("dated rows are flagged confirmed",
      all(i["confirmed"] for i in u19 if i["class"] != "Undated Grid"))
check("an undated row does not resurrect Emma on the 19th",
      not any(i["teacher"] == "Emma Strembickyj" for i in u19))

print("\n" + ("ALL PASS" if not FAILS else f"{len(FAILS)} FAILED: {FAILS}"))
sys.exit(1 if FAILS else 0)
