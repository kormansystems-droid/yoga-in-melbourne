#!/usr/bin/env python3
"""
Build teacher profile pages from templates + shared partials + schedule data.

  partials/base.css              shared stylesheet + embedded fonts (one copy)
  templates/<name>.template.html one per teacher (carries data-teacher + tokens)
  data/schedule.json             studios registry + per-teacher name/aliases/classes
        |  python3 build_profiles.py
        v
  <name>.html                    self-contained static page (Netlify publishes)

Templates starting with "_" are skeletons and are skipped.
Tokens filled per teacher: {{NAME_FULL}} {{NAME_GIVEN}} {{NAME_FAMILY}} {{SCHED_NOTE}}
Plus /* BASE_CSS:INJECT */ (shared css) and the SCHEDULE:START/END schedule slot.
"""
import json, re, html
from pathlib import Path

ROOT = Path(__file__).parent
TEMPLATES = ROOT / "templates"
OUT = ROOT
DATA = ROOT / "data" / "schedule.json"
BASE_CSS = (ROOT / "partials" / "base.css").read_text()

DAY_ORDER = {"Mon":0,"Tue":1,"Wed":2,"Thu":3,"Fri":4,"Sat":5,"Sun":6}
WORDS = ["zero","one","two","three","four","five","six","seven","eight","nine"]

# Loaded on every profile; community.js self-injects the "Join the Community" button + popup.
COMMUNITY_SCRIPTS = (
    '<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>\n'
    '<script src="/community.js"></script>\n'
)

def esc(s): return html.escape(s, quote=False)

def start_minutes(t):
    start = re.split(r"[–-]", t)[0].strip()
    mer = "PM" if "PM" in t.upper() else "AM"
    h,m = (int(x) for x in start.split(":"))
    if mer=="PM" and h!=12: h+=12
    if mer=="AM" and h==12: h=0
    return h*60+m

def render_cards(classes, studios):
    by = {}
    for c in classes: by.setdefault(c["studio"], []).append(c)
    cards=[]
    reg = list(studios.keys())
    # own-class studios first, sub-only studios last, registry order within each tier
    order_sids = sorted(by.keys(),
        key=lambda s:(1 if all(c.get("sub") for c in by[s]) else 0, reg.index(s) if s in reg else 99))
    for sid in order_sids:
        meta = studios[sid]
        rows = sorted(by[sid], key=lambda c:(DAY_ORDER.get(c["day"],99), start_minutes(c["time"])))
        rh = "\n".join(
            f'        <div class="cls"><span class="cls-day">{esc(r["day"])}</span>'
            f'<span class="cls-time">{esc(r["time"])}</span>'
            f'<span class="cls-name">{esc(r["class"])}'
            f'{" <span class=\"cls-sub\" style=\"opacity:.55;font-style:italic;font-weight:400\">substitute</span>" if r.get("sub") else ""}'
            f'</span></div>' for r in rows)
        cards.append(
            '      <div class="studio">\n        <div class="studio-head">\n          <div>\n'
            f'            <a class="studio-name" href="{esc(meta["url"])}" target="_blank" rel="noopener">{esc(meta["name"])}</a>\n'
            f'            <span class="studio-loc">{esc(meta["location"])}</span>\n'
            '          </div>\n'
            f'          <a class="book-link" href="{esc(meta["book"])}" target="_blank" rel="noopener">Book ↗</a>\n'
            f'        </div>\n{rh}\n      </div>')
    return "\n\n".join(cards), len(cards)

def build_one(tpl, data):
    src = tpl.read_text()
    teacher = re.search(r'studio-grid" data-teacher="([^"]+)"', src)
    if not teacher: raise SystemExit(f"{tpl.name}: no schedule data-teacher")
    teacher = teacher.group(1)
    rec = data["teachers"].get(teacher)
    if rec is None: raise SystemExit(f"{tpl.name}: '{teacher}' not in schedule.json")

    given, family = rec["name"]["given"], rec["name"]["family"]
    full = f"{given} {family}"
    cards, count = render_cards(rec.get("classes", []), data["studios"])
    if count:
        cw = WORDS[count] if count < len(WORDS) else str(count)
        note = f"{given}'s current weekly classes across {cw} studios. Tap a studio to book."
    else:
        note = f"{given}'s class timetable is coming soon."

    out = src.replace("/* BASE_CSS:INJECT */", BASE_CSS, 1)
    out = re.sub(r"(<!-- SCHEDULE:START -->).*?(<!-- SCHEDULE:END -->)",
                 lambda _: f"<!-- SCHEDULE:START -->\n{cards}\n      <!-- SCHEDULE:END -->",
                 out, count=1, flags=re.S)
    # Legacy name+email follow form -> account-based follow buttons (tokens filled below).
    out = re.sub(r'<a class="btn hero-follow" href="#follow">[^<]*</a>',
                 '<button class="btn hero-follow yim-follow-btn" type="button" '
                 'data-teacher="{{NAME_FULL}}" data-given="{{NAME_GIVEN}}">＋ Follow {{NAME_GIVEN}}</button>',
                 out, count=1)
    out = re.sub(r'<form class="follow-form" id="followForm".*?</form>',
                 '<div class="follow-cta">\n'
                 '        <button class="btn light yim-follow-btn" type="button" '
                 'data-teacher="{{NAME_FULL}}" data-given="{{NAME_GIVEN}}">＋ Follow {{NAME_GIVEN}}</button>\n'
                 '        <p class="ff-note">Following saves {{NAME_GIVEN}} to your account. '
                 "Not a member yet? We'll set you up in one step.</p>\n"
                 '      </div>',
                 out, count=1, flags=re.S)
    out = re.sub(r"<script>\s*\(function\(\)\{\s*var form = document\.getElementById\(['\"]followForm['\"]\).*?</script>",
                 '', out, count=1, flags=re.S)
    out = (out.replace("{{NAME_FULL}}", esc(full))
              .replace("{{NAME_GIVEN}}", esc(given))
              .replace("{{NAME_FAMILY}}", esc(family))
              .replace("{{SCHED_NOTE}}", esc(note)))
    out = out.replace("</body>", COMMUNITY_SCRIPTS + "</body>", 1)
    leftover = re.findall(r"\{\{[A-Z_]+\}\}", out)
    if leftover: raise SystemExit(f"{tpl.name}: unfilled tokens {leftover}")
    return out

def main():
    data = json.loads(DATA.read_text())
    tpls = sorted(t for t in TEMPLATES.glob("*.template.html") if not t.name.startswith("_"))
    if not tpls: raise SystemExit("no templates")
    for t in tpls:
        name = t.name.replace(".template.html",".html")
        (OUT/name).write_text(build_one(t, data))
        print(f"built {name:32s} <- {t.name}")

if __name__ == "__main__":
    main()
