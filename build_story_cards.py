#!/usr/bin/env python3
"""
build_story_cards.py: render the daily line-up as Instagram story cards.

  data/schedule.json  ──►  story/<date>/frame-NN-*.png   1080x1920, ready to post
                           story/<date>/cards.html       all frames, to eyeball first
                           story/<date>/captions.md      mentions + link per frame

Why this exists
---------------
"Yoga Tomorrow" runs every evening and "Yoga Today" every midday. Twice daily is
fourteen manual card builds a week, and a ritual that depends on a founder's daily
fiddling decays: usually just as it starts working. The schedule data already
exists; this is one more template over it.

Frames
------
    1  opener    the date, the count, every teacher named
    2  line-up   every class, chronological
    3+ teacher   one frame per teacher, that teacher's classes only
    last closer  who was on the mat, and the route to the full timetable

One frame per teacher at any roster size: a reshare audience enters at *that*
frame regardless of where it sits in the sequence, which is why frame position
does not decay tagged frames. The 18 Aug run is the clearest case yet: the
opener took 36 views and Steph Philip's frame took **183**, because her audience
entered at her frame and never saw the rest of the sequence.

The closer is the weakest frame every time it runs: 30 views on 15 Aug, 30 on
17 Aug, 16 on 18 Aug: and it stays, because at a small roster **volume is the
job, not views**: a four-frame story rolls past before anyone settles into it.
It is generated rather than hand-made so that keeping it costs nothing at 7pm,
and it now gets a captions.md row with the full mention list like every other
frame.

Every frame must carry a link sticker, and every frame that can name someone must
name them. The 15 Aug measurement: tagged frames averaged 123 views, untagged 36 -
3.4x. The opener was the best card and took the fewest views purely because nobody
was mentioned on it. captions.md exists so that never happens again.

Usage
-----
    python3 build_story_cards.py                      # tomorrow, all classes
    python3 build_story_cards.py --mode today         # today, only what is still ahead
    python3 build_story_cards.py --date 2026-08-23    # a specific date
    python3 build_story_cards.py --force              # override the thin-day guard

Cards are a draft, not a publication. Check them against the studios' own
timetables before posting: the pull window cannot see cancellations or covers
booked after the last run.
"""
import json, re, html, os, argparse, datetime, sys, base64
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).parent))
from build_profiles import start_minutes, esc, esc_attr, TEMPLATES  # one time parser, not two

ROOT = Path(__file__).parent
DATA = ROOT / "data" / "schedule.json"
BASE_CSS = (ROOT / "partials" / "base.css").read_text()
OUTDIR = ROOT / "story"

MELB = ZoneInfo("Australia/Melbourne")
SITE = "https://yogainmelbourne.com.au"
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DAY_FULL = {"Mon": "Monday", "Tue": "Tuesday", "Wed": "Wednesday", "Thu": "Thursday",
            "Fri": "Friday", "Sat": "Saturday", "Sun": "Sunday"}

# A one-class card advertises smallness; a missing story costs nothing. Silence is
# the correct output on a thin day, so a thin day is an error, not a warning.
MIN_CLASSES = 3
# "Yoga Today" lists only what a reader can still get to. Listing a 6am class at
# noon makes the format look inattentive.
TODAY_CUTOFF = "14:00"

# Above this many classes the line-up splits across two frames. Set from what a
# 1080x1920 card actually holds at the smallest legible type, not from taste.
LINEUP_MAX = 8

# Only the @font-face blocks: the real typefaces, none of the site's layout.
FONT_FACES = "\n".join(re.findall(r"@font-face\{[^}]*\}", BASE_CSS))

CARD_CSS = """
:root{
  --paper:#E7D9C0; --paper-deep:#DECDAE; --ink:#2A201A; --ink-soft:#5A4B3E;
  --henna:#9E3B26; --clay:#BC6B3C; --sage:#6F7155; --ochre:#C2974F;
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:#3a3a3a;font-family:'Hanken Grotesk',system-ui,sans-serif}
.card{
  width:1080px;height:1920px;background:var(--paper);color:var(--ink);
  position:relative;overflow:hidden;display:flex;flex-direction:column;
  /* Centre the content as a group between the safe zones: a 3-class day and a
     12-class day both sit balanced instead of hugging the top. */
  justify-content:center;
  /* Instagram's own UI eats roughly the top 220px and bottom 250px of a story,
     so nothing that must be read lives there. */
  padding:230px 92px 330px;
  --k:1;
}
.card + .card{margin-top:40px}
.kicker{
  font-family:'Spline Sans Mono',monospace;font-size:26px;letter-spacing:.20em;
  text-transform:uppercase;color:var(--henna);margin-bottom:26px;
}
.date{font-family:'Fraunces',serif;font-weight:400;font-size:96px;line-height:1.02;margin-bottom:18px}
.date em{font-style:italic;color:var(--henna)}
.count{
  font-family:'Spline Sans Mono',monospace;font-size:27px;letter-spacing:.06em;
  color:var(--sage);padding-top:22px;border-top:2px solid var(--ochre);
}
.names{margin-top:74px;padding-top:40px}
.names-lbl{
  font-family:'Spline Sans Mono',monospace;font-size:23px;letter-spacing:.14em;
  text-transform:uppercase;color:var(--sage);margin-bottom:22px;
}
.names li{font-family:'Fraunces',serif;line-height:1.30;list-style:none;
  display:flex;align-items:center;gap:calc(26px * var(--k));
  margin-bottom:calc(16px * var(--k))}
.names li:last-child{margin-bottom:0}
/* A vignette, not an avatar: the crop fades into the paper rather than sitting
   on it as a hard disc. Small, because the name is the thing being read: the
   face is there to make the roster feel like people. A teacher with no
   photograph gets the name alone and no empty circle. */
.n-vig{flex:0 0 calc(96px * var(--k));width:calc(96px * var(--k));height:calc(96px * var(--k));
  border-radius:50%;overflow:hidden;
  -webkit-mask-image:radial-gradient(circle at 50% 46%,#000 58%,rgba(0,0,0,.55) 80%,transparent 100%);
  mask-image:radial-gradient(circle at 50% 46%,#000 58%,rgba(0,0,0,.55) 80%,transparent 100%)}
.n-vig img{width:100%;height:100%;object-fit:cover;display:block}
/* No photograph: hold the column so the names stay on one left edge, but draw
   nothing. An empty circle reads as a missing image; empty space reads as a
   name. */
.n-gap{flex:0 0 calc(96px * var(--k))}

/* Row metrics scale off --k, which fit() lowers until the frame fits. The roster
   is meant to grow, so a fixed set of density breakpoints would quietly start
   clipping classes off the bottom of the card on the day it outgrew them. */
.rows{display:flex;flex-direction:column;gap:0;margin-top:14px}
.row{padding:calc(26px * var(--k)) 0;border-bottom:1.5px solid rgba(42,32,26,.16);display:grid;
     grid-template-columns:calc(238px * var(--k)) 1fr;column-gap:calc(30px * var(--k));
     align-items:baseline}
.row:last-child{border-bottom:none}
.row .t{font-family:'Spline Sans Mono',monospace;font-size:calc(30px * var(--k));
        color:var(--henna);white-space:nowrap}
.row .c{font-family:'Fraunces',serif;font-size:calc(42px * var(--k));line-height:1.18}
.row .w{font-family:'Hanken Grotesk',sans-serif;font-size:calc(27px * var(--k));
        color:var(--ink-soft);margin-top:calc(9px * var(--k))}
.row .w b{font-weight:600;color:var(--ink)}
.sub{font-style:italic;color:var(--sage)}
.names li{font-size:calc(58px * var(--k))}

.teacher-name{font-family:'Fraunces',serif;font-size:104px;line-height:1.02;margin-bottom:14px}
.t-head{display:flex;align-items:center;gap:34px;margin-bottom:14px}
.t-head .teacher-name{margin-bottom:0}
.t-portrait{flex:0 0 170px;width:170px;height:170px;border-radius:50%;overflow:hidden;
  border:1px solid rgba(42,32,26,.18)}
.t-portrait img{width:100%;height:100%;object-fit:cover;display:block}
.teacher-sub{font-family:'Hanken Grotesk',sans-serif;font-size:32px;color:var(--ink-soft);
             padding-bottom:30px;border-bottom:2px solid var(--ochre)}

.closer-lead{
  font-family:'Fraunces',serif;font-size:64px;line-height:1.10;margin-bottom:40px;
}
.closer-lead em{font-style:italic;color:var(--henna)}
.closer-names{list-style:none;margin-bottom:auto}
.closer-names li{
  font-family:'Fraunces',serif;font-size:calc(52px * var(--k));line-height:1.34;
}
.closer-cta{
  margin-top:56px;padding-top:26px;border-top:2px solid var(--ochre);
  font-family:'Hanken Grotesk',sans-serif;font-size:31px;line-height:1.42;color:var(--ink-soft);
}
.closer-cta b{color:var(--ink);font-weight:600}

.foot{position:absolute;left:92px;right:92px;bottom:150px;
      display:flex;justify-content:space-between;align-items:flex-end;
      padding-top:26px;border-top:1.5px solid rgba(42,32,26,.22)}
.mark{font-family:'Fraunces',serif;font-size:40px;line-height:1}
.mark em{font-style:italic;color:var(--henna)}
.url{font-family:'Spline Sans Mono',monospace;font-size:23px;letter-spacing:.05em;color:var(--sage)}
"""

# Shrink each card's rows until it fits inside the frame. Runs in the page, so the
# HTML preview and the PNGs are always the same thing. A card that cannot fit even
# at the floor sets data-overflow, which the build then refuses to ship silently.
FIT_JS = """
(() => {
  const FLOOR = 0.62, STEP = 0.02;
  for (const card of document.querySelectorAll('.card')) {
    let k = 1;
    card.style.setProperty('--k', k);
    while (card.scrollHeight > card.clientHeight && k > FLOOR) {
      k = Math.round((k - STEP) * 100) / 100;
      card.style.setProperty('--k', k);
    }
    card.dataset.k = k;
    if (card.scrollHeight > card.clientHeight) card.dataset.overflow = '1';
  }
})();
"""


def slug_of(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def story_link(path, campaign, content=None):
    """Link-sticker target. Convention from the 15 Aug audit: reel/story links
    carry utm_medium and a campaign slug, so this traffic separates cleanly from
    the bio link in GA.

    utm_content names the FRAME, and it is not optional decoration. Four frames
    point at "/": opener, both line-ups and the closer. Without utm_content those
    four are one indistinguishable row in GA: you can see that story traffic
    arrived and never which card earned it. The teacher frames were always
    separable by landing page; these four were not. Added 20 Aug 2026 after Mark
    pointed out he reads the attribution report regularly: so ambiguity in it
    costs him something real."""
    tail = f"&utm_content={content}" if content else ""
    return (f"{SITE}{path}?utm_source=instagram&utm_medium=story"
            f"&utm_campaign={campaign}{tail}")


# ---- teacher portraits -----------------------------------------------------
_PORTRAIT_CACHE = {}


def teacher_portrait(slug, px=340):
    """A small square portrait for a teacher's own story frame, as a data URI.

    Source of truth is the portrait already embedded in templates/<slug>.template.html
   : the photograph the teacher supplied, at 880x1100. Reusing it means the card and
    the page can never drift, and no new asset has to be kept in step.

    Returns None where there is no photograph. Sarah Metzger and Steph Philip have
    none today, and their cards render exactly as they did before: a name, a suburb
    and a timetable. A missing photo is a card without a photo, never a broken one.
    """
    if slug in _PORTRAIT_CACHE:
        return _PORTRAIT_CACHE[slug]
    out = None
    tpl = TEMPLATES / f"{slug}.template.html"
    if tpl.exists():
        m = re.search(r'data:image/jpeg;base64,([A-Za-z0-9+/=]{500,})', tpl.read_text(encoding="utf-8"))
        if m:
            try:
                from PIL import Image
                import io as _io
                im = Image.open(_io.BytesIO(base64.b64decode(m.group(1)))).convert("RGB")
                w, h = im.size
                side = min(w, h)
                # Anchor high: a head sits in the top third of a portrait crop, so a
                # centre square would cut the face off at the chin.
                top = min(max(int(h * 0.06), 0), h - side)
                im = im.crop(((w - side) // 2, top, (w - side) // 2 + side, top + side))
                im = im.resize((px, px), Image.LANCZOS)
                buf = _io.BytesIO()
                im.save(buf, "JPEG", quality=86, optimize=True)
                out = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
            except Exception:                                     # noqa: BLE001
                out = None
    _PORTRAIT_CACHE[slug] = out
    return out


def classes_for(schedule, day, date, cutoff=None):
    """Every class actually running on `date`, one entry per teacher, earliest first.

    A class co-taught appears once per teacher because each teacher's own frame
    has to show it. The line-up frame dedups on (time, class, studio).

    THE DATE TEST IS THE POINT OF THIS FUNCTION. schedule.json holds a weekly
    pattern collapsed from a rolling fortnight, so matching on weekday alone says
    "someone teaches Wednesdays", not "she teaches this Wednesday". On 18 Aug 2026
    that shipped: Emma Strembickyj was announced into three classes on a day she
    was overseas: her Kozen slots were being taught by Fai Mos, and the pattern
    row came from the following Wednesday. She saw it. Do not weaken this back to
    a weekday match.

    A row with NO `dates` is included. Undated does not mean unknown: Inndriya
    publishes a live weekly grid, and Warrior One's timetable is verified by hand
    from the studio's own screenshots and carries a `verified` date on the studio
    record. A weekly timetable nobody has contradicted is the best evidence those
    studios can give, and dropping it silently deletes people: Rayne Watkin
    teaches only at Warrior One and Inndriya, so excluding undated rows removed
    her from On the Mat entirely. That is a worse failure than the one above, not
    a safer one.

    The rule is asymmetric and deliberately so. A DATED row must match the date,
    because a dated feed actively told us who is teaching and ignoring it is what
    caught Emma. An UNDATED row rides on the weekly timetable, because nothing
    told us otherwise. `confirmed` marks which is which so captions.md can say
    what still needs a human eye before posting."""
    studios = schedule["studios"]
    iso = date.isoformat()
    out = []
    for teacher, rec in schedule.get("teachers", {}).items():
        for c in rec.get("classes", []):
            if c.get("day") != day:
                continue
            dates = c.get("dates")
            if dates and iso not in dates:
                continue
            mins = start_minutes(c["time"])
            if cutoff is not None and mins < cutoff:
                continue
            meta = studios.get(c["studio"], {})
            out.append({
                "teacher": teacher, "mins": mins, "time": c["time"], "class": c["class"],
                "studio": meta.get("name", c["studio"]), "suburb": meta.get("location", ""),
                "confirmed": bool(c.get("dates")), "verified": meta.get("verified"),
            })
    return sorted(out, key=lambda r: (r["mins"], r["teacher"]))


def hhmm_to_mins(s):
    h, m = s.split(":")
    return int(h) * 60 + int(m)


def _rows_html(items, show_teacher):
    out = []
    for r in items:
        bits = [f'<b>{esc(r["studio"])}</b>']
        if r["suburb"]:
            bits.append(esc(r["suburb"]))
        if show_teacher:
            bits.insert(0, f'<b>{esc(r["teacher"])}</b>')
        out.append(
            f'<div class="row"><div class="t">{esc(r["time"])}</div>'
            f'<div><div class="c">{esc(r["class"])}</div>'
            f'<div class="w">{" · ".join(bits)}</div></div></div>')
    return "\n".join(out)


def _foot():
    return ('<div class="foot"><div class="mark">Yoga <em>in</em> Melbourne</div>'
            '<div class="url">yogainmelbourne.com.au</div></div>')


def _vignette_html(slug):
    """The small soft-edged portrait beside a name on the opener and closer."""
    src = teacher_portrait(slug, px=200)
    if not src:
        return '<div class="n-gap"></div>'
    return f'<div class="n-vig"><img src="{src}" alt=""></div>' 


def _portrait_html(slug):
    src = teacher_portrait(slug)
    return f'<div class="t-portrait"><img src="{src}" alt=""></div>' if src else ""


def build_frames(schedule, day, date, items, mode):
    """-> list of {name, html, link, mentions, note}. One frame per teacher, always."""
    kicker = "Yoga Today" if mode == "today" else "Yoga Tomorrow"
    campaign = "daily-lineup-today" if mode == "today" else "daily-lineup"
    day_full = DAY_FULL[day]
    date_str = date.strftime("%-d %B")

    by_teacher = {}
    for r in items:
        by_teacher.setdefault(r["teacher"], []).append(r)
    teachers = sorted(by_teacher, key=lambda t: min(r["mins"] for r in by_teacher[t]))

    # The line-up frame shows each class once, however many teachers are on it.
    # The suburb is part of the key, not decoration. r["studio"] holds the display
    # NAME, and a brand can run more than one venue: (Here) Yoga teaches Slow Flow
    # at 7:15 on Friday in BOTH Port Melbourne and Malvern, with different teachers.
    # Keying on name alone collapsed those into one row, dropped Steph Philip's
    # class from the line-up entirely, and printed Sarah Metzger's suburb over it -
    # a class that runs, with a teacher who is never named. Found 20 Aug 2026.
    seen, uniq = set(), []
    for r in items:
        key = (r["time"], r["class"], r["studio"], r["suburb"])
        if key not in seen:
            seen.add(key)
            uniq.append(r)
    studios = {r["studio"] for r in items}
    suburbs = {r["suburb"] for r in items if r["suburb"]}

    def plural(n, word):
        if n == 1:
            return f"{n} {word}"
        return f"{n} {word + 'es' if word.endswith(('s', 'sh', 'ch', 'x')) else word + 's'}"

    frames = []

    # 1: opener. Names every teacher, because this frame has to be taggable.
    # The headline is the weekday, not the date: "Tuesday Yoga" is the thing being
    # announced. The date is a fact about it, so it leads the fact line instead.
    # In tomorrow mode there is no lead phrase: the kicker already says
    # "Yoga Tomorrow", and repeating it under the headline said nothing twice.
    facts = [date_str] + (["still to come"] if mode == "today" else []) + [
        plural(len(uniq), "class"), plural(len(teachers), "teacher"),
        plural(len(studios), "studio"), plural(len(suburbs), "suburb")]
    frames.append({
        "name": "opener",
        "link": story_link("/", campaign, "opener"),
        "mentions": [],
        "note": "NO mentions on this frame. The standing rule (YIM-growth-model-2026-08-15, "
                "\u00a711) is: mention each teacher on her own frame only, so the frame she "
                "reshares is entirely about her. A mention here hands her the option to "
                "reshare a card naming four other people, and she will only reshare once. "
                "A build between 16 and 20 Aug 2026 overrode this, arguing from the 15 Aug "
                "tagged-vs-untagged view gap (123 vs 36). That gap measures reshare traffic "
                "entering at a tagged frame; it does not measure whether mentioning five "
                "people on one frame helps. Restored 20 Aug 2026 when Mark caught it.",
        "html": f'<div class="card"><div class="kicker">{esc(kicker)}</div>'
                f'<div class="date">{esc(day_full)} <em>Yoga</em></div>'
                f'<div class="count">{esc(" · ".join(facts))}</div>'
                f'<div class="names"><div class="names-lbl">Our teachers</div><ul>'
                + "".join(f'<li>{_vignette_html(slug_of(t))}<span>{esc(t)}</span></li>'
                          for t in teachers)
                + f'</ul></div>{_foot()}</div>',
    })

    # 2: the line-up, split above LINEUP_MAX.
    #
    # Wed 19 Aug was the first day the roster broke a single card: 14 classes
    # overflow even at the 0.62 scale floor, and the type is already at its
    # legible limit, so shrinking further is not available. The build correctly
    # refused to ship a card with a class cut off the bottom: which meant the
    # nightly workflow published nothing at all.
    #
    # Split by TIME OF DAY rather than an arbitrary midpoint, because that is how
    # a reader uses it: she already knows whether she wants a 6am class or a 6pm
    # one. A day that falls entirely into one half splits in halves instead, so
    # the rule degrades sensibly rather than producing one empty frame.
    #
    # Each part mentions only the teachers ON that part. Tagging the whole roster
    # on both would put a teacher's name against a card her classes are not on,
    # and the reshare is supposed to be about her day.
    def _lineup_frame(rows, label, slug):
        head = f"{esc(kicker)} · the line-up" + (f" · {esc(label)}" if label else "")
        return {
            "name": f"lineup-{slug}" if slug else "lineup",
            "link": story_link("/", campaign, f"lineup-{slug}" if slug else "lineup"),
            "mentions": [],
            "note": "NO mentions on this frame. Same rule as the opener \u2014 a line-up names "
                    "everyone, so it is nobody's frame to reshare.",
            "html": f'<div class="card"><div class="kicker">{head}</div>'
                    f'<div class="date">{esc(day_full)}</div>'
                    f'<div class="rows">{_rows_html(rows, show_teacher=True)}</div>{_foot()}</div>',
        }

    if len(uniq) <= LINEUP_MAX:
        frames.append(_lineup_frame(uniq, None, None))
    else:
        morning = [r for r in uniq if r["mins"] < 720]
        later = [r for r in uniq if r["mins"] >= 720]
        if morning and later:
            parts = [(morning, "the morning", "morning"),
                     (later, "the afternoon & evening", "afternoon-evening")]
        else:                                   # all one half of the day
            half = (len(uniq) + 1) // 2
            parts = [(uniq[:half], "1 of 2", "1-of-2"), (uniq[half:], "2 of 2", "2-of-2")]
        for rows, label, slug in parts:
            frames.append(_lineup_frame(rows, label, slug))

    # 3+: one per teacher
    for t in teachers:
        rows = by_teacher[t]
        slug = slug_of(t)
        where = ", ".join(sorted({r["suburb"] for r in rows if r["suburb"]}))
        frames.append({
            "name": slug,
            "link": story_link(f"/{slug}.html", campaign, slug),
            "mentions": [t],
            "note": f"This frame carries {t}'s name and NO ONE else's, so the frame she "
                    f"reshares is entirely about her, and it is the ONLY frame she is "
                    f"mentioned on: one notification, one reshare, undiluted. Link sticker "
                    f"goes to her page, not the homepage.",
            "html": f'<div class="card"><div class="kicker">{esc(kicker)} · {esc(day_full)}</div>'
                    f'<div class="t-head">{_portrait_html(slug)}'
                    f'<div><div class="teacher-name">{esc(t)}</div>'
                    f'<div class="teacher-sub">{esc(where)}</div></div></div>'
                    f'<div class="rows">{_rows_html(rows, show_teacher=False)}</div>{_foot()}</div>',
        })

    # last: the closer.
    #
    # It is the weakest frame every time it runs (30 views on 15 Aug, 30 on 17 Aug,
    # 16 on 18 Aug) and it stays anyway, because at this roster size the job is
    # VOLUME, not views: a four-frame story rolls past before anyone settles into
    # it. Generating it removes the only real argument against keeping it: a frame
    # that has to be tagged by hand at 7pm every night is exactly the friction that
    # kills a daily ritual.
    #
    # RETIRE IT ON ROSTER SIZE, NOT ON PERFORMANCE: around six teachers on a normal
    # day, when the per-teacher frames already give the story enough length on their
    # own. Its view count will never justify it and is not the test.
    #
    # Before retiring it, move the "full timetable" call to action onto the line-up
    # frame. The closer is currently the only frame that carries it, so dropping
    # this card without moving that line first would silently remove the story's
    # one route to the whole schedule.
    lead = "Today" if mode == "today" else "Tomorrow"
    frames.append({
        "name": "closer",
        "link": story_link("/", campaign, "closer"),
        "mentions": [],
        "note": "NO mentions on this frame. It is the story's route to the full timetable and "
                "the last thing anyone sees \u2014 but it names everyone, so it is nobody's "
                "frame to reshare, and a second notification for a card she will not reshare "
                "spends goodwill for nothing. Link sticker still goes on it.",
        "html": f'<div class="card closer"><div class="kicker">{esc(kicker)}</div>'
                f'<div class="closer-lead">{esc(lead)} <em>on the mat</em> with</div>'
                f'<ul class="closer-names">'
                + "".join(f"<li>{esc(t)}</li>" for t in teachers)
                + '</ul>'
                # Two corrections live in this one sentence, in order.
                #
                # 1. "Every class, every studio" claimed the whole city. The site covers
                #    twelve studios, so the sentence was false in the one place a reader
                #    could most easily check it. The scope that IS true is the teacher:
                #    for anyone we cover, it really is every class she teaches.
                #
                # 2. The fix for (1) was "across the studios we cover", which is accurate
                #    but unreadable: "the studios we cover" is an editorial-desk concept
                #    the reader has never been told and cannot evaluate. It answers an
                #    objection nobody raised and costs the sentence its confidence.
                #    Mark, 31 Aug 2026: it should not appear anywhere reader-facing.
                #
                # So the claim is scoped to the teacher and left unqualified. It stays
                # true as long as every studio a ROSTER teacher works at is one we pull.
                # That is a checkable invariant, not a hope: the Warrior One audit of
                # 30 Aug confirmed it for Alessia and Rayne across three studios. Add a
                # roster teacher who also teaches somewhere we do not pull and this
                # sentence becomes false, silently. Check before you add.
                #
                # "studios we cover" is still correct in privacy.html, where explaining
                # the site's scope IS the point. This rule is about marketing copy.
                f'<div class="closer-cta">Every class our teachers teach, in one '
                f'place: <b>yogainmelbourne.com.au</b></div>{_foot()}</div>',
    })
    return frames


def write_links_page(path, frames, day, date, mode):
    """A phone-sized page of link stickers, one per frame, each with a copy button.

    captions.md is the reference document; this is the thing you hold in one hand
    at 7pm while Instagram is open in the other. Selecting a 130-character URL out
    of a markdown table on a phone is the step where a link sticker silently ends
    up with the wrong utm_content: or with a trailing space that breaks it. One
    tap removes that. Written every run so it is never stale."""
    kicker = "Yoga Today" if mode == "today" else "Yoga Tomorrow"
    rows = []
    for i, f in enumerate(frames, 1):
        mentions = ", ".join(f.get("mentions") or []) or "-"
        rows.append(
            f'<li class="row">'
            f'<div class="head"><span class="n">{i:02d}</span>'
            f'<span class="fname">{esc(f["name"])}</span></div>'
            f'<div class="mentions"><span class="lbl">Mention</span> {esc(mentions)}</div>'
            f'<div class="linkrow">'
            f'<input id="u{i}" class="u" readonly value="{esc_attr(f["link"])}">'
            f'<button class="copy" data-t="u{i}">Copy</button>'
            f'</div></li>')
    css = """
:root{--paper:#E7D9C0;--paper-deep:#DECDAE;--ink:#2A201A;--ink-soft:#5A4B3E;
      --henna:#9E3B26;--clay:#BC6B3C;--sage:#6F7155;--ochre:#C2974F}
*{box-sizing:border-box}
body{margin:0;padding:22px 16px 60px;background:var(--paper);color:var(--ink);
     font-family:'Hanken Grotesk',system-ui,-apple-system,sans-serif;
     -webkit-font-smoothing:antialiased}
.wrap{max-width:620px;margin:0 auto}
.kicker{font-family:'Spline Sans Mono',ui-monospace,monospace;font-size:11.5px;
        letter-spacing:.16em;text-transform:uppercase;color:var(--henna)}
h1{font-family:'Fraunces',Georgia,serif;font-weight:500;font-size:34px;
   line-height:1.05;margin:8px 0 4px;letter-spacing:-.01em}
h1 em{font-style:italic;color:var(--henna)}
.sub{font-size:14.5px;color:var(--ink-soft);margin:0 0 22px;max-width:46ch}
ol{list-style:none;margin:0;padding:0}
.row{background:var(--paper-deep);border:1px solid rgba(42,32,26,.16);
     padding:14px 14px 12px;margin-bottom:12px}
.head{display:flex;align-items:baseline;gap:10px}
.n{font-family:'Spline Sans Mono',ui-monospace,monospace;font-size:12px;
   color:var(--sage);letter-spacing:.08em}
.fname{font-family:'Fraunces',Georgia,serif;font-size:19px;font-weight:500}
.mentions{font-size:13px;color:var(--ink-soft);margin:5px 0 10px;line-height:1.45}
.mentions .lbl{font-family:'Spline Sans Mono',ui-monospace,monospace;font-size:10.5px;
     letter-spacing:.12em;text-transform:uppercase;color:var(--clay);margin-right:6px}
.linkrow{display:flex;gap:10px;align-items:stretch}
input.u{flex:1;min-width:0;width:100%;font-family:'Spline Sans Mono',ui-monospace,monospace;
     font-size:11px;line-height:1.4;color:var(--ink-soft);background:rgba(42,32,26,.05);
     border:1px solid rgba(42,32,26,.12);padding:9px;border-radius:0;
     -webkit-appearance:none;text-overflow:ellipsis}
input.u:focus{outline:2px solid var(--clay);outline-offset:-2px;color:var(--ink)}
.copy{flex:0 0 auto;align-self:stretch;min-width:82px;cursor:pointer;
      font-family:'Spline Sans Mono',ui-monospace,monospace;font-size:11.5px;
      letter-spacing:.1em;text-transform:uppercase;color:var(--paper);
      background:var(--henna);border:1px solid var(--henna);border-radius:0;
      transition:background .15s,border-color .15s}
.copy:hover{background:var(--clay);border-color:var(--clay)}
.copy.done{background:var(--sage);border-color:var(--sage)}
.foot{margin-top:26px;padding-top:16px;border-top:1px solid rgba(42,32,26,.18);
      font-size:13px;color:var(--ink-soft);line-height:1.55}
.foot b{font-family:'Fraunces',Georgia,serif;font-weight:500;color:var(--ink)}
"""
    js = """
/* Three ways to copy, in order of preference. An artifact renders inside a
   sandboxed iframe, where navigator.clipboard is usually blocked by permissions
   policy and execCommand can fail too: which is exactly how the first version of
   this page shipped with buttons that did nothing (20 Aug 2026). So the URL lives
   in a readonly <input>: even if BOTH copy paths fail, one tap selects the whole
   string and the OS copy menu takes it. The button reports what actually happened
   rather than always claiming success. */
document.querySelectorAll('input.u').forEach(function(i){
  function all(){ i.setSelectionRange(0, i.value.length); }
  i.addEventListener('focus', all);
  i.addEventListener('click', all);
});
document.querySelectorAll('.copy').forEach(function(b){
  b.addEventListener('click', function(){
    var el = document.getElementById(b.dataset.t), txt = el.value;
    function flash(word){
      b.textContent = word; b.classList.add('done');
      setTimeout(function(){ b.textContent = 'Copy'; b.classList.remove('done'); }, 2200);
    }
    function selectIt(){
      el.focus(); el.setSelectionRange(0, txt.length);
      try { return document.execCommand('copy'); } catch(e){ return false; }
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(txt).then(
        function(){ flash('Copied'); },
        function(){ flash(selectIt() ? 'Copied' : 'Selected'); });
    } else {
      flash(selectIt() ? 'Copied' : 'Selected');
    }
  });
});
"""
    doc = (f"<!doctype html><html lang='en-AU'><head><meta charset='utf-8'>"
           f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
           f"<title>{esc(kicker)}: link stickers</title>"
           f"<link rel='preconnect' href='https://fonts.googleapis.com'>"
           f"<link rel='preconnect' href='https://fonts.gstatic.com' crossorigin>"
           f"<link href='https://fonts.googleapis.com/css2?family=Fraunces:ital,wght@0,400;0,500;1,400"
           f"&family=Hanken+Grotesk:wght@400;500;600&family=Spline+Sans+Mono:wght@400;500&display=swap'"
           f" rel='stylesheet'>"
           f"<style>{css}</style></head><body><div class='wrap'>"
           f"<div class='kicker'>{esc(kicker)} · link stickers</div>"
           f"<h1>{DAY_FULL[day]} <em>{date.strftime('%-d %B')}</em></h1>"
           f"<p class='sub'>One link sticker per frame, in post order. Tap Copy, then paste "
           f"straight into the sticker. If a button says <b>Selected</b> rather than Copied, "
           f"the browser blocked the clipboard: the text is highlighted, use your own "
           f"copy. The tags are what make this show up as story "
           f"traffic in GA, and utm_content is what names the frame.</p>"
           f"<ol>{''.join(rows)}</ol>"
           f"<div class='foot'><b>Every frame takes a link sticker</b>, and a "
           f"<b>mention</b> sticker for everyone named on it. A mention notifies her and "
           f"gives the one-tap reshare; a tag does not.</div>"
           f"</div><script>{js}</script></body></html>")
    path.write_text(doc, encoding="utf-8")

def write_captions(path, frames, day, date, mode, items):
    kicker = "Yoga Today" if mode == "today" else "Yoga Tomorrow"
    when = "around midday" if mode == "today" else "in the evening, around 7pm"
    L = [f"# {kicker}: {DAY_FULL[day]} {date.strftime('%-d %B %Y')}",
         "",
         f"{len(frames)} frames. Post them as one run, {when}: and at the *same* hour "
         "every day, so yesterday's frames expire as these go up.",
         "",
         "**Before posting:** check these against the studios' own timetables. The pull "
         "window cannot see a cancellation or a cover booked since the last run.",
         ""]
    # Rows a live feed confirmed for this date need no second look. Rows riding on a
    # weekly timetable do: that is the whole gap Warrior One's dark feed leaves, and
    # naming it here is what stops it becoming another teacher's phone call.
    unconfirmed = [r for r in items if not r.get("confirmed")]
    if unconfirmed:
        L += ["**These rows are not date-confirmed**: they come from a weekly timetable, "
              "not a live feed, so a cover or an absence this week would not show. Worth a "
              "glance before you post:", ""]
        for r in sorted(unconfirmed, key=lambda r: r["mins"]):
            v = f" · timetable verified {r['verified']}" if r.get("verified") else ""
            L.append(f"- {r['time']}: **{r['teacher']}**, {r['class']}, {r['studio']}{v}")
        L.append("")
    L += [
         "**Every frame takes a link sticker, and a MENTION sticker for everyone named on it.** "
         "A story has mentions, not tags: the mention is what notifies her and gives her "
         "the one-tap reshare.",
         "",
         "| # | Frame | Mention | Link sticker |",
         "|---|---|---|---|"]
    for i, f in enumerate(frames, 1):
        m = ", ".join(f["mentions"]) or "-"
        L.append(f'| {i} | `{f["name"]}` | {m} | `{f["link"]}` |')
    L += ["", "## Frame notes", ""]
    for i, f in enumerate(frames, 1):
        L.append(f'**{i}. {f["name"]}**: {f["note"]}')
        L.append("")
    L += ["## After posting", "",
          "- Stories are one rolling 24h sequence, so post ~24h apart and let yesterday's "
          "frames expire on their own. **Never delete frames to make room**: deleting "
          "destroys their insights permanently.",
          "- Screenshot Insights at ~20h, before expiry, and log views per frame in the "
          "rotation ledger. Tagged vs untagged is the number worth watching.",
          "- Judge this on taps, exits, link taps and reshares. Not likes: story likes "
          "are ~0 and always will be.",
          "- When a teacher reshares: react warmly, one line, and do not re-reshare an "
          "echo. The point is that replying opens a DM thread.",
          ""]
    path.write_text("\n".join(L))


def main():
    ap = argparse.ArgumentParser(description="Render the daily line-up as story cards.")
    ap.add_argument("--mode", choices=["tomorrow", "today"], default="tomorrow")
    ap.add_argument("--date", help="YYYY-MM-DD; default is tomorrow (or today in --mode today)")
    ap.add_argument("--cutoff", default=TODAY_CUTOFF,
                    help=f"--mode today: hide classes starting before this (default {TODAY_CUTOFF})")
    ap.add_argument("--force", action="store_true", help="build even on a thin day")
    ap.add_argument("--no-png", action="store_true", help="write the HTML preview only")
    a = ap.parse_args()

    schedule = json.loads(DATA.read_text())
    now = datetime.datetime.now(MELB)
    if a.date:
        date = datetime.date.fromisoformat(a.date)
    else:
        date = now.date() + (datetime.timedelta(days=0) if a.mode == "today"
                             else datetime.timedelta(days=1))
    day = DAYS[date.weekday()]
    cutoff = hhmm_to_mins(a.cutoff) if a.mode == "today" else None

    items = classes_for(schedule, day, date, cutoff)
    n_teachers = len({r["teacher"] for r in items})
    if len(items) < MIN_CLASSES and not a.force:
        raise SystemExit(
            f"{DAY_FULL[day]} {date}: {len(items)} class(es), below the {MIN_CLASSES}-class "
            f"threshold: not building.\nSilence costs nothing in stories; a one-class card "
            f"advertises smallness. Use --force to override.")
    if not items:
        raise SystemExit(f"{DAY_FULL[day]} {date}: no classes at all.")
    if a.mode == "today" and n_teachers < 5:
        print(f"⚠ Yoga Today is a five-teacher format and the roster shows {n_teachers}. "
              "It is the commercially valuable one: availability, not aspiration: but it "
              "needs the density to never look thin.")

    out = OUTDIR / f"{date.isoformat()}-{a.mode}"
    out.mkdir(parents=True, exist_ok=True)
    # Clear old frames first. A rebuild that produces FEWER frames than the last
    # run leaves the surplus behind, and the leftovers are indistinguishable from
    # real output in the folder: which is how the wrong Rayne frame and a second
    # closer ended up in a set that had already been corrected once.
    stale = sorted(out.glob("frame-*.png"))
    for f in stale:
        f.unlink()
    if stale:
        print(f"  cleared {len(stale)} frame(s) from a previous build")
    frames = build_frames(schedule, day, date, items, a.mode)

    doc = (f"<!doctype html><html lang=\"en-AU\"><head><meta charset=\"utf-8\">"
           f"<title>{esc_attr(a.mode)} {date.isoformat()}</title>"
           f"<style>{FONT_FACES}{CARD_CSS}</style></head><body>"
           + "\n".join(f["html"] for f in frames)
           + f"<script>{FIT_JS}</script></body></html>")
    (out / "cards.html").write_text(doc)
    write_captions(out / "captions.md", frames, day, date, a.mode, items)
    write_links_page(out / "links.html", frames, day, date, a.mode)

    print(f"{DAY_FULL[day]} {date}: {len(items)} classes, {n_teachers} teachers, "
          f"{len(frames)} frames -> {out.relative_to(ROOT)}/")

    if a.no_png:
        return
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit("cards.html and captions.md written. Install playwright for PNGs: "
                         "pip install playwright")
    # Set CHROMIUM_EXECUTABLE where a Chromium is already on disk and playwright's
    # own build number does not match it (any preinstalled-browser environment).
    exe = os.environ.get("CHROMIUM_EXECUTABLE")
    with sync_playwright() as p:
        b = p.chromium.launch(**({"executable_path": exe} if exe else {}))
        pg = b.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=1)
        pg.goto((out / "cards.html").as_uri())
        pg.wait_for_timeout(600)   # let the embedded webfonts paint
        pg.evaluate(FIT_JS)        # re-fit now the real metrics are known
        scales = pg.evaluate(
            "() => [...document.querySelectorAll('.card')]"
            ".map(c => ({k: c.dataset.k, over: !!c.dataset.overflow}))")
        for i, f in enumerate(frames):
            name = f"frame-{i+1:02d}-{f['name']}.png"
            pg.locator(".card").nth(i).screenshot(path=str(out / name))
            s = scales[i]
            note = "" if s["k"] == "1" else f"   (fitted to {s['k']})"
            print(f"  {name}{note}")
        b.close()

    over = [f["name"] for f, s in zip(frames, scales) if s["over"]]
    if over:
        raise SystemExit(
            f"\n⚠ {', '.join(over)} still overflow at the smallest size. The PNGs are "
            "written but a class is cut off the bottom: split the line-up across two "
            "frames rather than posting these.")


if __name__ == "__main__":
    main()
