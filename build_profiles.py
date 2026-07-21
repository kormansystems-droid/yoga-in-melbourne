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
HANDOFFS = ROOT / "data" / "handoffs.json"
try:
    HANDOFF = json.loads(HANDOFFS.read_text())
except Exception:
    HANDOFF = {"brands": {}, "teachers": {}}
HANDOFF_PREFIXES = tuple(m for br in HANDOFF.get("brands", {}).values() for m in br.get("match", []))
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

def render_handoff_cards(slug, classes):
    """Manual 'Also at <studio>' cards for teachers at feed-less studios — a link to
    book directly, no class times. Retired per studio once it gets a live feed."""
    out = []
    for bid in HANDOFF.get("teachers", {}).get(slug, []):
        b = HANDOFF.get("brands", {}).get(bid)
        if not b:
            continue
        prefixes = tuple(b.get("match", []))
        if prefixes and any(str(c.get("studio","")).startswith(prefixes) for c in classes):
            continue  # real timed classes exist here -> show those instead of a book-direct card
        url, nm = esc(b.get("book_url", "#")), esc(b.get("name", bid))
        out.append(
            '      <div class="studio studio-handoff">\n        <div class="studio-head">\n          <div>\n'
            f'            <a class="studio-name" href="{url}" target="_blank" rel="noopener">{nm}</a>\n'
            '            <span class="studio-loc">Book directly at their studio</span>\n'
            '          </div>\n'
            f'          <a class="book-link" href="{url}" target="_blank" rel="noopener">Go to {nm} ↗</a>\n'
            '        </div>\n      </div>')
    return out


# ---- SEO head generation (per-teacher; suburbs from where they teach + capped catchment) ----
SITE = "https://yogainmelbourne.com.au"
try:
    CATCHMENT = json.loads((ROOT / "data" / "catchment.json").read_text())
except Exception:
    CATCHMENT = {}

def _teacher_suburbs(rec, studios):
    from collections import Counter
    c = Counter()
    for cls in rec.get("classes", []):
        loc = studios.get(cls.get("studio"), {}).get("location")
        if loc: c[loc] += 1
    return [loc for loc, _ in c.most_common()]

def _handoff_suburbs(teacher, studios):
    out = []
    for bid in HANDOFF.get("teachers", {}).get(teacher, []):
        prefixes = tuple(HANDOFF.get("brands", {}).get(bid, {}).get("match", []))
        for sid, meta in studios.items():
            if prefixes and sid.startswith(prefixes):
                loc = meta.get("location")
                if loc and loc not in out: out.append(loc)
    return out

def _join_suburbs(subs):
    if not subs: return ""
    if len(subs) == 1: return subs[0]
    return ", ".join(subs[:-1]) + " & " + subs[-1]

def seo_head(teacher, rec, studios, slug):
    given = rec["name"]["given"]; family = rec["name"]["family"]; full = (given + " " + family).strip()
    url = SITE + "/" + slug + ".html"; img = SITE + "/img/" + slug + ".jpg"
    teaching = _teacher_suburbs(rec, studios)
    for s in _handoff_suburbs(teacher, studios):
        if s not in teaching: teaching.append(s)
    # capped catchment: nearest 3 per teaching suburb, deduped, excluding teaching suburbs
    catch = []
    for s in teaching:
        for c in CATCHMENT.get(s, [])[:3]:
            if c not in teaching and c not in catch: catch.append(c)
    area = teaching + catch
    if teaching:
        title = full + ", Yoga in " + _join_suburbs(teaching[:2]) + " | Yoga in Melbourne"
        desc = given + " teaches yoga across " + _join_suburbs(teaching[:4]) + ". Explore " + given + "'s weekly class schedule, story and where to book, on Yoga in Melbourne."
    else:
        title = full + ", Yoga Nidra & Meditation | Yoga in Melbourne"
        desc = given + " guides Yoga Nidra and meditation, in Melbourne and online. Explore " + given + "'s story and practices on Yoga in Melbourne."
    person = {"@context":"https://schema.org","@type":"Person","name":full,"jobTitle":"Yoga Teacher","url":url,"image":img,"description":desc,"worksFor":{"@type":"Organization","name":"Yoga in Melbourne","url":SITE+"/"}}
    if area: person["areaServed"] = [{"@type":"Place","name":s} for s in area]
    crumb = {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"Yoga in Melbourne","item":SITE+"/"},{"@type":"ListItem","position":2,"name":"Teachers","item":SITE+"/#teachers"},{"@type":"ListItem","position":3,"name":full}]}
    def a(x): return html.escape(x, quote=True)
    return "\n".join([
        "<title>"+a(title)+"</title>",
        '<meta name="description" content="'+a(desc)+'">',
        '<link rel="canonical" href="'+url+'">',
        '<meta property="og:type" content="profile">',
        '<meta property="og:title" content="'+a(title)+'">',
        '<meta property="og:description" content="'+a(desc)+'">',
        '<meta property="og:url" content="'+url+'">',
        '<meta property="og:image" content="'+img+'">',
        '<meta property="og:site_name" content="Yoga in Melbourne">',
        '<meta name="twitter:card" content="summary_large_image">',
        '<meta name="twitter:title" content="'+a(title)+'">',
        '<meta name="twitter:description" content="'+a(desc)+'">',
        '<meta name="twitter:image" content="'+img+'">',
        '<script type="application/ld+json">'+json.dumps(person, ensure_ascii=False)+'</script>',
        '<script type="application/ld+json">'+json.dumps(crumb, ensure_ascii=False)+'</script>',
    ])
# ---- end SEO ----

def build_one(tpl, data):
    src = tpl.read_text()
    teacher = re.search(r'studio-grid" data-teacher="([^"]+)"', src)
    if not teacher: raise SystemExit(f"{tpl.name}: no schedule data-teacher")
    teacher = teacher.group(1)
    rec = data["teachers"].get(teacher)
    if rec is None:
        # online-only teacher (no studio feed): derive name, render an empty schedule slot
        parts = teacher.split()
        rec = {"name": {"given": parts[0], "family": " ".join(parts[1:])}, "classes": []}

    given, family = rec["name"]["given"], rec["name"]["family"]
    full = f"{given} {family}"
    cards, count = render_cards(rec.get("classes", []), data["studios"])
    handoff_cards = render_handoff_cards(teacher, rec.get("classes", []))
    if handoff_cards:
        joined = "\n\n".join(handoff_cards)
        cards = (cards + "\n\n" + joined) if cards.strip() else joined
    if count:
        cw = WORDS[count] if count < len(WORDS) else str(count)
        note = f"{given}'s current weekly classes across {cw} studios. Tap a studio to book."
    elif handoff_cards:
        note = f"Book with {given} directly at their studio."
    else:
        note = f"{given}'s class timetable is coming soon."

    out = src.replace("/* BASE_CSS:INJECT */", BASE_CSS, 1)
    out = out.replace("<!-- SEO_HEAD -->", seo_head(teacher, rec, data["studios"], tpl.name.replace(".template.html","")), 1)
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
