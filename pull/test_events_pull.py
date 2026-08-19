#!/usr/bin/env python3
"""
Tests for pull/events.py — the discovery half.

Every case here comes from something that actually went wrong or nearly did.

    python3 pull/test_events_pull.py
"""
import sys, datetime, importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pull"))
import events as EV

FIX = (ROOT / "pull" / "_fixtures" / "warrior-one-workshops.txt").read_text(encoding="utf-8")
URL = "https://warrioroneyoga.com.au/workshops/"
LOC = {"BRIGHTON": "warrior-one-brighton", "MORDIALLOC": "warrior-one-mordialloc",
       "MORNINGTON": "warrior-one-mornington"}
TODAY = datetime.date(2026, 8, 19)

FAILS = []
def check(name, cond, detail=""):
    print(("  ok   " if cond else "  FAIL ") + name + (f"\n         {detail}" if not cond and detail else ""))
    if not cond:
        FAILS.append(name)

evs, probs = EV.page_events(FIX, "warrior-one-brighton", URL, locations=LOC, expect=5)
by = {e["title"]: e for e in evs}

# --- the failure that started this: one-of-five -----------------------------
check("an index page yields EVERY event, not just the first", len(evs) == 5, f"got {len(evs)}")
check("no anomalies on a page that parses cleanly", not probs, str(probs))

# --- routing ---------------------------------------------------------------
check("each event is filed at the studio named after the @",
      by["Slow Flow to Yin with Lucy"]["studio"] == "warrior-one-mornington"
      and by["Spring Resonance — A Spring Sound & Slow Flow Journey"]["studio"] == "warrior-one-mordialloc"
      and by["21-Day Brighton August Challenge"]["studio"] == "warrior-one-brighton")

# --- dates -----------------------------------------------------------------
lucy = by["Slow Flow to Yin with Lucy"]
check("a single-day event keeps its start and end time",
      lucy["starts"][:16] == "2026-09-02T10:45" and lucy["ends"][:16] == "2026-09-02T12:00", lucy["starts"])
ch = by["21-Day Brighton August Challenge"]
check("a range carries the year that appears only at its END",
      ch["starts"][:10] == "2026-08-29" and ch["ends"][:10] == "2026-09-18",
      f'{ch["starts"]} -> {ch["ends"]}')

# --- price -----------------------------------------------------------------
check("two-tier pricing takes the number a non-member actually pays",
      ch["price"] == 225, str(ch["price"]))
check("an event with no price stated gets None, not a guess", lucy["price"] is None)
check("a plain investment line is read", by["Sound Bath with IKSRE"]["price"] == 45)

# --- titles ----------------------------------------------------------------
check("an ALL CAPS heading becomes a title, and small words stay small",
      by["Slow Flow to Yin with Lucy"]["title"] == "Slow Flow to Yin with Lucy")
check("a known acronym survives title casing", "IKSRE" in by["Sound Bath with IKSRE"]["title"])
check("a small word after a dash opens a subtitle and is capitalised",
      EV.title_case("SPRING RESONANCE — A SPRING SOUND JOURNEY")
      == "Spring Resonance — A Spring Sound Journey")
check("a title that is already sentence case is left alone",
      EV.title_case("The Cyclical Practice") == "The Cyclical Practice")

# --- the shrink detector ---------------------------------------------------
_, p2 = EV.page_events(FIX, "warrior-one-brighton", URL, locations=LOC, expect=6)
check("yielding FEWER events than last time is reported, not accepted",
      any("expected at least" in x for x in p2), str(p2))

# --- merge: the bug that would have deleted every hand-written card --------
manual = [
 {"id": "m1", "source": "manual", "title": "Hand-written", "until": "2026-12-01", "kind": "workshop"},
 {"id": "m2", "source": "manual", "title": "Evergreen", "kind": "training"},
 {"id": "m3", "source": "manual", "title": "Long past", "until": "2026-01-01", "kind": "workshop"},
 {"id": "m4", "source": "manual", "title": "Yin, Poetry & Cello with Franks", "until": "2026-08-23",
  "kind": "workshop", "supersedes": [by["Yin, Poetry & Cello with Franks"]["id"]]},
]
merged = EV.merge_events(manual, evs, {"page"}, today=TODAY)
t = [e["title"] for e in merged]
check("a manual card dated only by `until` SURVIVES a merge", "Hand-written" in t,
      "reading ends/starts alone made every manual card look expired")
check("a manual card with no dates at all is evergreen and survives", "Evergreen" in t)
check("a genuinely past manual card is still dropped", "Long past" not in t)
check("a manual card supersedes the scraped copy of the same event",
      t.count("Yin, Poetry & Cello with Franks") == 1,
      f'appears {t.count("Yin, Poetry & Cello with Franks")}x')
check("events from a source that did not run this pass are untouched",
      "Hand-written" in [e["title"] for e in EV.merge_events(manual, [], set(), today=TODAY)])

print()
if FAILS:
    print(f"{len(FAILS)} FAILED: " + ", ".join(FAILS)); sys.exit(1)
print("all events-pull tests pass")
