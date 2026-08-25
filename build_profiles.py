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
Tokens filled per teacher: {{NAME_FULL}} {{NAME_GIVEN}} {{NAME_FAMILY}} {{NAME_POSS}} {{SCHED_NOTE}}
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
# For anything landing inside a quoted attribute. Studio urls are hand-maintained
# in schedule.json, but per-class urls arrive from the studio feeds, so a stray
# quote must not be able to escape the href.
def esc_attr(s): return html.escape(str(s), quote=True)

def start_minutes(t):
    """Minutes past midnight for the START of a '10:45–11:45 AM' style range.

    A class that crosses noon carries its own meridiem on the start time —
    '10:45 AM–12:00 PM' — because the range's single trailing AM/PM cannot
    describe it. Read the start's own meridiem where it has one, and only fall
    back to the range's when it does not. Without this, every AM class ending
    after noon parses as PM and sorts to the evening: Rayne's 75-minute Yin &
    Yoga Nidra at Mordialloc was the first such class on the roster, and it
    would have sorted silently, not crashed."""
    start = re.split(r"[–-]", t)[0].strip()
    own = re.search(r"(AM|PM)", start, re.I)
    mer = (own.group(1) if own else ("PM" if "PM" in t.upper() else "AM")).upper()
    h, m = (int(x) for x in re.sub(r"\s*(AM|PM)\s*", "", start, flags=re.I).split(":"))
    if mer=="PM" and h!=12: h+=12
    if mer=="AM" and h==12: h=0
    return h*60+m

def render_row(r, book_url):
    """One class row, as a link through to booking.

    Every row is clickable. Where the feed gives a per-class url we deep-link to
    that session; otherwise we fall back to the studio's booking page, which is
    still a booking intent we can count. Until this shipped the only outbound link
    on a profile was the studio-level 'Book ↗', so the tracked click event had
    almost no volume to measure and no way to say which class earned it.

    Attribution comes from GA4 enhanced measurement, which records link_text — the
    row's text is 'Wed 5:00-6:00 PM Slow Flow Yoga', so the class is identified
    without appending query parameters to a studio's booking URL (which we do not
    control and can break)."""
    href = r.get("url") or book_url
    # A row carrying `dates` happens on those days and no others — cover, a
    # one-off, a class that has not been on the roster long. Rendering it in the
    # weekly grid unqualified tells a reader she teaches it every week, which is
    # the same false statement that put Emma into three classes on 19 August;
    # this file simply had not been taught the lesson the story cards were.
    day = esc(r["day"])
    dates = r.get("dates") or []
    if dates:
        import datetime as _dt
        try:
            ds = [_dt.date.fromisoformat(x) for x in sorted(dates)]
            when = ", ".join(f"{d.day} {d.strftime('%b')}" for d in ds[:2])
            day = f'{esc(r["day"])} <span class="cls-once">{esc(when)}</span>'
        except ValueError:
            day = esc(r["day"])
    return (f'        <a class="cls" href="{esc_attr(href)}" target="_blank" rel="noopener">'
            f'<span class="cls-day">{day}</span>'
            f'<span class="cls-time">{esc(r["time"])}</span>'
            f'<span class="cls-name">{esc(r["class"])}</span></a>')

def render_cards(classes, studios):
    import datetime as _dt
    today = _dt.date.today().isoformat()
    # A one-off whose date has gone is not a class, it is history. Weekly rows
    # (no `dates`) are untouched.
    classes = [c for c in classes
               if not c.get("dates") or max(c["dates"]) >= today]
    by = {}
    for c in classes: by.setdefault(c["studio"], []).append(c)
    cards=[]
    reg = list(studios.keys())
    # registry order. There is no "her studio" versus "a studio she covers at":
    # rosters churn, nobody owns a slot, and the teacher named is the teacher.
    order_sids = sorted(by.keys(), key=lambda s: reg.index(s) if s in reg else 99)
    for sid in order_sids:
        meta = studios[sid]
        rows = sorted(by[sid], key=lambda c:(DAY_ORDER.get(c["day"],99), start_minutes(c["time"])))
        rh = "\n".join(render_row(r, meta["book"]) for r in rows)
        cards.append(
            '      <div class="studio">\n        <div class="studio-head">\n          <div>\n'
            f'            <a class="studio-name" href="{esc_attr(meta["url"])}" target="_blank" rel="noopener">{esc(meta["name"])}</a>\n'
            f'            <span class="studio-loc">{esc(meta["location"])}</span>\n'
            '          </div>\n'
            f'          <a class="book-link" href="{esc_attr(meta["book"])}" target="_blank" rel="noopener">Book ↗</a>\n'
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
        url, nm = esc_attr(b.get("book_url", "#")), esc(b.get("name", bid))
        # Most handoffs are studios anyone can book. Some are not: Saint Haven is
        # a private members' club, and telling a reader to "book directly" at a
        # place that requires an application is worse than saying nothing — she
        # turns up to a door that will not open. `note` and `cta` let a brand say
        # what it actually is.
        note = esc(b.get("note", "Book directly at their studio"))
        cta = esc(b.get("cta", f"Go to {b.get('name', bid)} ↗"))
        out.append(
            '      <div class="studio studio-handoff">\n        <div class="studio-head">\n          <div>\n'
            f'            <a class="studio-name" href="{url}" target="_blank" rel="noopener">{nm}</a>\n'
            f'            <span class="studio-loc">{note}</span>\n'
            '          </div>\n'
            f'          <a class="book-link" href="{url}" target="_blank" rel="noopener">{cta}</a>\n'
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

def _handoff_suburbs(teacher, rec, studios):
    """Suburbs a teacher reaches through a feed-less studio, for the SEO head.

    Mirrors render_handoff_cards(): a brand contributes nothing once she has real
    timed classes there, because those classes already name her suburbs and the
    brand's OTHER locations are not places she teaches. Without that rule,
    registering Warrior One Mornington put "Mornington" into Alessia's and Rayne's
    titles, descriptions and schema areaServed — neither teaches there. It stayed
    invisible for months because every Warrior One suburb had happened to be one
    they did teach in, so the extra entries deduplicated away."""
    own = {c.get("studio") for c in rec.get("classes", [])}
    out = []
    for bid in HANDOFF.get("teachers", {}).get(teacher, []):
        prefixes = tuple(HANDOFF.get("brands", {}).get(bid, {}).get("match", []))
        if not prefixes:
            continue
        if any(str(sid).startswith(prefixes) for sid in own):
            continue          # real classes at this brand — they speak for themselves
        for sid, meta in studios.items():
            if sid.startswith(prefixes):
                loc = meta.get("location")
                if loc and loc not in out: out.append(loc)
    return out

def _join_suburbs(subs):
    if not subs: return ""
    if len(subs) == 1: return subs[0]
    return ", ".join(subs[:-1]) + " & " + subs[-1]

MISSING_OG = []          # teachers built without a share image, reported at the end


def seo_head(teacher, rec, studios, slug):
    """A teacher with no photograph gets a profile with no photograph — never a
    profile pointing at one that isn't there.

    Until 19 Aug 2026 this emitted og:image, twitter:image and a schema.org
    Person.image for every teacher, whether or not img/<slug>.jpg existed. Three
    teachers had no file, so every time one of their pages was shared the preview
    resolved a 404. Ryan Mannix took 354 story views and 21 page views in a night
    with a broken preview the whole time.

    So the image tags are written only when the file is actually on disk at build
    time, and twitter:card falls back from summary_large_image to summary — a
    large-image card with no image renders as an empty box, a summary card reads
    as a clean text preview. Missing files are named on stdout at the end of the
    build; they are a gap to fill, not a state to hide."""
    given = rec["name"]["given"]; family = rec["name"]["family"]; full = (given + " " + family).strip()
    url = SITE + "/" + slug + ".html"
    has_img = (ROOT / "img" / (slug + ".jpg")).exists()
    img = SITE + "/img/" + slug + ".jpg" if has_img else ""
    if not has_img:
        MISSING_OG.append(slug)
    teaching = _teacher_suburbs(rec, studios)
    for s in _handoff_suburbs(teacher, rec, studios):
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
    person = {"@context":"https://schema.org","@type":"Person","name":full,"jobTitle":"Yoga Teacher","url":url,"description":desc,"worksFor":{"@type":"Organization","name":"Yoga in Melbourne","url":SITE+"/"}}
    if has_img: person["image"] = img
    if area: person["areaServed"] = [{"@type":"Place","name":s} for s in area]
    crumb = {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"Yoga in Melbourne","item":SITE+"/"},{"@type":"ListItem","position":2,"name":"Teachers","item":SITE+"/#teachers"},{"@type":"ListItem","position":3,"name":full}]}
    def a(x): return html.escape(x, quote=True)
    tags = [
        "<title>"+a(title)+"</title>",
        '<meta name="description" content="'+a(desc)+'">',
        '<link rel="canonical" href="'+url+'">',
        '<meta property="og:type" content="profile">',
        '<meta property="og:title" content="'+a(title)+'">',
        '<meta property="og:description" content="'+a(desc)+'">',
        '<meta property="og:url" content="'+url+'">',
        '<meta property="og:site_name" content="Yoga in Melbourne">',
        '<meta name="twitter:title" content="'+a(title)+'">',
        '<meta name="twitter:description" content="'+a(desc)+'">',
        '<meta name="twitter:card" content="'+("summary_large_image" if has_img else "summary")+'">',
    ]
    if has_img:
        tags += ['<meta property="og:image" content="'+img+'">',
                 '<meta name="twitter:image" content="'+img+'">']
    tags += ['<script type="application/ld+json">'+json.dumps(person, ensure_ascii=False)+'</script>',
             '<script type="application/ld+json">'+json.dumps(crumb, ensure_ascii=False)+'</script>']
    return "\n".join(tags)
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
        note = (f"{poss(given)} current weekly classes across {cw} "
                f"{'studio' if count == 1 else 'studios'}. Tap any class to book.")
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
              .replace("{{NAME_POSS}}", esc(poss(given)))
              .replace("{{SCHED_NOTE}}", esc(note)))
    out = out.replace("</body>", COMMUNITY_SCRIPTS + "</body>", 1)
    leftover = re.findall(r"\{\{[A-Z_]+\}\}", out)
    if leftover: raise SystemExit(f"{tpl.name}: unfilled tokens {leftover}")
    return out

def build_index(data):
    """Fill the homepage router's teacher row from schedule.json.

    Hand-maintained lists rot the moment onboarding gets easy: Steph Philip and
    Ryan Mannix both went live with working pages and no route to them from the
    homepage, because someone had to remember to add a line and didn't.

    Only the router row is generated. The Teachers grid stays hand-curated — it
    carries portraits and standfirsts for teachers whose profile has been written
    and approved, which is an editorial decision, not a list of rows in a table.
    A listing belongs in the router because a reader looking for her timetable
    should find it; it does not belong in the showcase until she has said yes to
    a profile."""
    idx = ROOT / "index.html"
    src = idx.read_text()
    # Alphabetical, by the name a reader actually reads first. Mark's call,
    # 20 Aug 2026, overruling the class-count sort this used to have: "no one
    # cares about the number, only the name."
    #
    # He is right, and the old reasoning was worse than wrong — it was ranking
    # teachers by how much work they happen to have. A row that reorders itself
    # when someone loses a class is a row that quietly publishes a league table,
    # which is the one thing this publication has said it will never do.
    #
    # The real cost, recorded so it is a known trade and not a surprise: on mobile
    # this row is a horizontal scroll strip (flex-wrap:nowrap; overflow-x:auto),
    # so position is visibility — about two and a half chips are on screen. Names
    # late in the alphabet need a swipe. Fix that with the row's design if it
    # matters, not by reordering people.
    order = sorted(data["teachers"], key=lambda n: (n.split()[0].lower(), n.lower()))
    links = "".join(f'\n      <a href="{slug_of(n)}.html">{esc(n)}</a>' for n in order)
    out = re.sub(r"(<!-- ROUTER_PEOPLE:START -->).*?(<!-- ROUTER_PEOPLE:END -->)",
                 lambda m: m.group(1) + links + "\n    " + m.group(2), src, flags=re.S)
    if out == src and "ROUTER_PEOPLE:START" not in src:
        raise SystemExit("index.html: ROUTER_PEOPLE markers missing")
    if out != src:
        idx.write_text(out)
        print(f"built index.html router          <- {len(data['teachers'])} teachers")


def poss(name):
    """Possessive of a given name. A name already ending in s takes the bare
    apostrophe — Franks', not Franks's. Mark's call, 20 Aug 2026, and correct.
    Written as a rule rather than a fix to one page because the roster will keep
    producing them: Franks, and any Jess, Tess or James after her."""
    return name + ("'" if name.rstrip().endswith(("s", "S")) else "'s")


def slug_of(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def main():
    data = json.loads(DATA.read_text())
    build_index(data)
    tpls = sorted(t for t in TEMPLATES.glob("*.template.html") if not t.name.startswith("_"))
    if not tpls: raise SystemExit("no templates")
    for t in tpls:
        name = t.name.replace(".template.html",".html")
        (OUT/name).write_text(build_one(t, data))
        print(f"built {name:32s} <- {t.name}")
    if MISSING_OG:
        # Not an error — the page is correct without one. But a teacher whose page
        # gets shared is better off with a photo, so the gap is named every build
        # rather than discovered when a link preview looks bare.
        print("\nno share image (img/<slug>.jpg) — link previews render as text only:")
        for slug in sorted(set(MISSING_OG)):
            print(f"  {slug}")
        print("  fix: python3 crop-portrait.py <photo> <slug>")

if __name__ == "__main__":
    main()
