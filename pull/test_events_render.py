#!/usr/bin/env python3
"""
Regression tests for build_events.py.

These exist because the events sections failed silently once already: cards
expired, a client-side script hid them, and nothing refilled the band. Every test
here pins one of the behaviours that failure depended on.

    python3 pull/test_events_render.py
"""
import json, sys, tempfile, datetime, importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("be", ROOT / "build_events.py")
be = importlib.util.module_from_spec(spec); spec.loader.exec_module(be)

STS = {"within-south-yarra": {"name": "Within", "location": "South Yarra"},
       "grass-roots-st-kilda": {"name": "Grass Roots", "location": "St Kilda"}}

FAILS = []
def check(name, cond, detail=""):
    print(("  ok   " if cond else "  FAIL ") + name + (f"\n         {detail}" if not cond and detail else ""))
    if not cond:
        FAILS.append(name)


# --- the caption line -------------------------------------------------------
feed = {"kind": "workshop", "title": "Flight School", "studio": "within-south-yarra",
        "starts": "2026-08-22T13:00:00+10:00", "price": 50, "url": "https://x/flight",
        "source": "page"}
check("a feed event composes when · where · how much",
      be.compose_cat(feed, STS) == "Sat 22 Aug · South Yarra · $50",
      be.compose_cat(feed, STS))

free = dict(feed, price=0, teacher="Masha")
check("price 0 renders as Free, not $0",
      "Free" in be.compose_cat(free, STS) and "$0" not in be.compose_cat(free, STS),
      be.compose_cat(free, STS))

nop = dict(feed); nop.pop("price")
check("a missing price is omitted, not guessed",
      "$" not in be.compose_cat(nop, STS) and "None" not in be.compose_cat(nop, STS),
      be.compose_cat(nop, STS))

manual = {"kind": "workshop", "title": "Yin, Poetry & Cello",
          "cat": "Sun 23 Aug · Brighton · $90", "blurb": "Warrior One",
          "url": "https://x", "until": "2026-08-23", "source": "manual"}
check("the studio is not named in both the caption and the blurb",
      be.compose_cat(feed, STS).count("Within") == 0
      and "<p>Within</p>" in be.strip_card(feed, STS), be.strip_card(feed, STS))

check("a hand-written caption is never recomposed",
      'Sun 23 Aug · Brighton · $90' in be.strip_card(manual, STS))

# --- escaping ---------------------------------------------------------------
amp = dict(manual, title="Sound & Slow Flow", cat="15–16 & 22–23 Aug")
html_out = be.strip_card(amp, STS)
check("an ampersand is escaped exactly once",
      "&amp;amp;" not in html_out and "&amp;" in html_out, html_out)

check("a double space typed into a booking system is collapsed",
      "Sarah Metzger" in be.strip_card(
          {"kind": "workshop", "title": "Info Session", "url": "https://x",
           "cat": "Sun 23 Aug · Sarah  Metzger", "blurb": "b", "source": "momence"}, STS))

donation = dict(feed, price="By donation")
check("a non-numeric price is passed through, not formatted as currency",
      "By donation" in be.compose_cat(donation, STS) and "$" not in be.compose_cat(donation, STS),
      be.compose_cat(donation, STS))

# --- expiry -----------------------------------------------------------------
check("expiry prefers `until`, then `ends`, then `starts`",
      be.expiry({"until": "2026-01-01", "ends": "2026-02-02"}) == "2026-01-01"
      and be.expiry({"ends": "2026-02-02T10:00"}) == "2026-02-02"
      and be.expiry({"starts": "2026-03-03T10:00"}) == "2026-03-03")
check("an evergreen entry (no dates) never expires", be.expiry({"title": "200hr"}) is None)

# --- rendering --------------------------------------------------------------
band = {"kind": "retreat", "title": "Warrior One, Thailand", "url": "https://x/th",
        "cat": "30 Aug–5 Sep", "blurb": "b", "until": "2026-09-05",
        "image": "https://img/a.jpg?q=80&w=1000", "alt": "A bay", "region": "Koh Samui",
        "band_title": "Thailand", "source": "manual"}
plain = {"kind": "retreat", "title": "Feed Retreat", "url": "https://x/f",
         "starts": "2026-10-01T09:00:00+10:00", "studio": "grass-roots-st-kilda",
         "source": "momence"}
out = be.render("retreat", [band, plain], STS)
check("only an entry with a photograph gets a band card", out.count('class="jb-card"') == 1)
check("every retreat still appears in the strip", out.count('class="strip-card"') == 2)
check("a feed retreat with no photo degrades to a strip card, it is not dropped",
      "Feed Retreat" in out)
check("an image URL's query separators are escaped for HTML",
      'a.jpg?q=80&amp;w=1000' in out, out[out.find("<img"):out.find("<img") + 90])
# The regression Mark has reported more than once: the photographs and the text
# cards beneath them are read as pairs, and a plain date sort breaks the pairing
# as soon as one entry has no photograph.
band2 = dict(band, title="B", url="https://x/b", starts="2026-12-01T09:00:00+10:00",
             until="2026-12-01", image="https://img/b.jpg", band_title="B")
noimg = {"kind": "retreat", "title": "No Photo", "url": "https://x/n",
         "until": "2026-09-01", "cat": "c", "blurb": "b", "source": "manual"}
ordered = sorted([band2, noimg, band],
                 key=lambda e: (0 if e.get("image") else 1,
                                e.get("starts") or e.get("until") or "9999", e.get("title", "")))
out2 = be.render("retreat", ordered, STS)
import re as _re
_band = _re.findall(r'class="jb-card"[\s\S]*?<h3>([^<]*)</h3>', out2)
_strip = _re.findall(r'class="strip-card"[\s\S]*?<h3>([^<]*)</h3>', out2)
check("every photograph pairs with the text card in the same position",
      _strip[:len(_band)] == [e["title"] for e in ordered if e.get("image")],
      f"band={_band} strip={_strip}")
check("a retreat with no photograph sorts BELOW all the photographed ones",
      _strip[-1] == "No Photo", str(_strip))

check("workshops and trainings render no band",
      'jb-card' not in be.render("workshop", [manual], STS))

# --- the failure this pipeline exists to prevent ----------------------------
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    (td / "data").mkdir()
    marked = ('<section class="section" id="events"><p></p>\n'
              '    <!-- EVENTS:workshop -->\n<a class="strip-card">KEEP ME</a>\n'
              '    <!-- /EVENTS:workshop -->\n  </section>\n'
              '<section class="section" id="retreats"><p></p>\n'
              '    <!-- EVENTS:retreat -->\nx\n    <!-- /EVENTS:retreat -->\n  </section>\n'
              '<section class="section" id="training"><p></p>\n'
              '    <!-- EVENTS:training -->\ny\n    <!-- /EVENTS:training -->\n  </section>\n')
    (td / "index.html").write_text(marked, encoding="utf-8")
    (td / "data" / "events.json").write_text(json.dumps({"events": [
        dict(manual, until="2020-01-01")]}), encoding="utf-8")   # everything expired
    (td / "data" / "schedule.json").write_text(json.dumps({"studios": STS}), encoding="utf-8")
    be.ROOT, be.EVENTS, be.SCHED, be.INDEX = td, td/"data"/"events.json", td/"data"/"schedule.json", td/"index.html"
    be.main()
    after = (td / "index.html").read_text(encoding="utf-8")
    check("a band with nothing live is LEFT ALONE, not emptied", "KEEP ME" in after,
          "an empty band is the exact silent failure this pipeline was built to stop")

print()
if FAILS:
    print(f"{len(FAILS)} FAILED: " + ", ".join(FAILS)); sys.exit(1)
print("all events-render tests pass")
