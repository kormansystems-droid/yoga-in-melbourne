#!/usr/bin/env python3
"""
build_carousel_cards.py — a three-card Instagram carousel announcing a profile.

Why a carousel and not a reel
-----------------------------
Measured 19 Aug 2026 across four pieces: the two that presented the publication
and its people converted at 2.5–3% follows per viewer; the two that promoted a
single podcast episode converted at 0–0.5%, despite better engagement and more
reach. Format was not the variable — proposition was. So the last card sells the
publication, not the post. See notes/YIM-instagram-acquisition-2026-08-19.md.

1080x1350, which is the tallest Instagram renders in feed without cropping.

    python3 build_carousel_cards.py --teacher shelley-armstrong
"""
import argparse, re, os, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCHED = ROOT / "data" / "schedule.json"

DAY_PLURAL = {"Mon": "Mondays", "Tue": "Tuesdays", "Wed": "Wednesdays",
              "Thu": "Thursdays", "Fri": "Fridays", "Sat": "Saturdays",
              "Sun": "Sundays"}
DAY_ORDER = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _start(t):
    """'6:15-7:15 AM' -> '6:15am'. The card wants the time you turn up, and the
    meridiem belongs to the range's end, so it has to be carried back."""
    m = re.match(r"\s*(\d{1,2})(?::(\d{2}))?", t or "")
    if not m:
        return (t or "").strip()
    ap = re.search(r"(am|pm)", t or "", re.I)
    hh, mm = m.group(1), m.group(2)
    return f"{hh}:{mm}{ap.group(1).lower()}" if mm else f"{hh}{ap.group(1).lower() if ap else ''}"


def from_schedule(name):
    """Everything the cards say about where a teacher teaches, read from the
    same file the site renders from.

    Typing it by hand is how a card ends up contradicting the page it points at
    — the Emma failure of 18 Aug in miniature, where a card announced classes
    that were not real. If she is not in schedule.json, that is an error worth
    stopping for, not a default worth guessing."""
    data = json.loads(SCHED.read_text(encoding="utf-8"))
    teachers = data.get("teachers", {})
    t = teachers.get(name)
    if not t:
        # schedule.json already records how a feed misspells her; reuse that
        # rather than making the operator guess the canonical spelling.
        for k, v in teachers.items():
            if name.lower() in [a.lower() for a in v.get("aliases", [])]:
                print(f"  '{name}' is an alias — using '{k}'")
                name, t = k, v
                break
    if not t:
        near = [k for k in teachers if name.split()[0].lower() in k.lower()]
        raise SystemExit(f"'{name}' is not in data/schedule.json."
                         + (f" Did you mean: {', '.join(near)}?" if near else
                            " Add her there first — the cards read from it, never around it."))
    classes = t.get("classes", [])
    if not classes:
        raise SystemExit(f"'{name}' has no classes in data/schedule.json. "
                         f"A 'where to find her' card with nothing to find is worse than no card.")

    studios = data["studios"]
    sids = sorted({c["studio"] for c in classes},
                  key=lambda s: -sum(1 for c in classes if c["studio"] == s))
    def label(sid):
        m = studios.get(sid, {})
        return m.get("name", sid), m.get("location", "")

    # One studio, one class: name it exactly. That specificity is the whole point.
    if len(classes) == 1:
        c = classes[0]
        line = f"{c['class']}, {DAY_PLURAL.get(c['day'], c['day'])} at {_start(c['time'])}."
    elif len(classes) <= 3:
        line = " · ".join(f"{c['class']}, {DAY_PLURAL.get(c['day'], c['day'])[:3]} {_start(c['time'])}"
                          for c in sorted(classes, key=lambda c: DAY_ORDER.index(c["day"])))
    else:
        # Past a handful, the count IS the story: no booking system can show it.
        line = (f"{len(classes)} classes a week"
                + (f", across {len(sids)} studios." if len(sids) > 1 else "."))

    # Group by BRAND, not by studio id. Ryan Mannix teaches at two Good Vibes
    # locations, and "Good Vibes and Good Vibes" is what naming them separately
    # produces. The count in the schedule line stays by location, because four
    # rooms is four rooms even when two share a sign.
    brands = {}
    for sid in sids:
        n, loc = label(sid)
        brands.setdefault(n, []).append(loc)

    names = list(brands)
    if len(names) == 1:
        n = names[0]
        locs = [l for l in brands[n] if l]
        if len(locs) == 1:
            where = f"{n}, {locs[0]}"
        elif len(locs) == 2:
            where = f"{n}, {locs[0]} and {locs[1]}"
        else:
            where = n
    elif len(names) == 2:
        where = f"{names[0]} and {names[1]}"
    elif len(names) == 3:
        where = f"{names[0]}, {names[1]} and {names[2]}"
    else:
        where = f"{names[0]}, {names[1]} and {len(names) - 2} more"
    return line, where
BASE_CSS = (ROOT / "partials" / "base.css").read_text()
FONT_FACES = "\n".join(re.findall(r"@font-face\{[^}]*\}", BASE_CSS))

CSS = """
:root{
  --paper:#E7D9C0; --paper-deep:#DECDAE; --ink:#2A201A; --ink-soft:#5A4B3E;
  --henna:#9E3B26; --clay:#BC6B3C; --sage:#6F7155; --ochre:#C2974F;
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:#3a3a3a;font-family:'Hanken Grotesk',system-ui,sans-serif}
.card{
  width:1080px;height:1350px;background:var(--paper);color:var(--paper);
  position:relative;overflow:hidden;display:flex;flex-direction:column;
  justify-content:flex-end;
}
.card + .card{margin-top:40px}
.card img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
/* Two scrims, not one. A single long gradient greys the whole photograph; a
   short deep one at the foot plus a whisper at the head keeps her face clean
   and still gives the type something to sit on. */
.scrim{position:absolute;inset:0;
  background:
    linear-gradient(to top, rgba(20,14,10,.86) 0%, rgba(20,14,10,.62) 22%,
                    rgba(20,14,10,.12) 46%, rgba(20,14,10,0) 62%),
    linear-gradient(to bottom, rgba(20,14,10,.34) 0%, rgba(20,14,10,0) 26%);
}
.inner{position:relative;padding:0 84px 92px}
.top{position:absolute;top:76px;left:84px;right:84px}
.kicker{
  font-family:'Spline Sans Mono',monospace;font-size:25px;letter-spacing:.22em;
  text-transform:uppercase;color:#E8C9A8;margin-bottom:26px;
}
.kicker.dark{color:var(--henna)}
.name{font-family:'Fraunces',serif;font-weight:400;font-size:108px;line-height:1.0;
      letter-spacing:-.01em}
.name em{font-style:italic;color:#E8A88A}
.lead{font-family:'Fraunces',serif;font-weight:400;font-size:70px;line-height:1.14}
.lead em{font-style:italic;color:#E8A88A}
.sub{font-family:'Hanken Grotesk',sans-serif;font-size:34px;line-height:1.42;
     color:rgba(231,217,192,.86);margin-top:26px;max-width:30ch}
.sub b{font-weight:600;color:var(--paper)}
.rule{height:1px;background:rgba(231,217,192,.34);margin:40px 0 30px}
.mark{font-family:'Fraunces',serif;font-size:38px;line-height:1;color:var(--paper)}
.mark em{font-style:italic;color:#E8A88A}


/* The closing card is paper, not photograph. Her pose spans the full width of a
   square frame, so any 4:5 crop amputates a foot or a hand — and an asana
   photograph with a limb cut off is worse than no photograph. Containing it on
   the site's own cream keeps the pose whole and lets the call to action read in
   ink rather than fighting a scrim. */
/* Type at the head, not the foot. The teaching photograph puts the student at the
   very bottom of the frame, which is exactly where a bottom-set card keeps its
   headline — so the two collide and she reads as decapitated whichever way the
   crop is biased. Flipping the card fixes the composition rather than fighting
   it, and gives the carousel a middle beat that is not a third bottom-left
   block of text. */
.card.topset{justify-content:flex-start}
.card.topset .scrim{
  background:
    linear-gradient(to bottom, rgba(20,14,10,.88) 0%, rgba(20,14,10,.66) 24%,
                    rgba(20,14,10,.14) 50%, rgba(20,14,10,0) 66%),
    linear-gradient(to top, rgba(20,14,10,.30) 0%, rgba(20,14,10,0) 24%);
}
.card.topset .inner{padding:84px 84px 0}
.card.topset .top{position:static;padding:0}
.card.topset .rule{margin:36px 0 28px}
.card.topset .foot{position:absolute;bottom:84px;left:84px;right:84px}

.card.paper{background:var(--paper);color:var(--ink);justify-content:flex-start}
.card.paper .photo{position:relative;height:780px;margin:0;overflow:hidden;
  background:#657F73}   /* sampled from the photo's own edges */
/* contain, not cover: an asana photograph with a foot cropped off is a
   worse photograph, and the letterbox on paper-deep reads as deliberate. */
.card.paper .photo img{position:absolute;inset:0;object-fit:contain;object-position:50% 50%}
.card.paper .inner{padding:56px 84px 0;flex:1;display:flex;flex-direction:column}
.card.paper .kicker{color:var(--henna)}
.card.paper .lead{color:var(--ink);font-size:60px;line-height:1.16}
.card.paper .lead em{color:var(--henna)}
.card.paper .rule{background:rgba(42,32,26,.22);margin:auto 0 30px}
.tag{font-family:'Fraunces',serif;font-size:46px;line-height:1.2;color:var(--ink);
     margin-top:26px}
.tag em{font-style:italic;color:var(--henna)}
.card.paper .mark{color:var(--ink)}
.card.paper .mark em{color:var(--henna)}
.card.paper .pip{color:var(--sage)}
.card.paper .url{color:var(--sage)}
.card.paper .foot{padding-bottom:84px}
.url{font-family:'Spline Sans Mono',monospace;font-size:25px;letter-spacing:.06em;
     color:rgba(231,217,192,.78);margin-top:34px}
.foot{display:flex;align-items:flex-end;justify-content:space-between}
.pip{font-family:'Spline Sans Mono',monospace;font-size:22px;letter-spacing:.18em;
     color:rgba(231,217,192,.55)}
"""

WORDMARK = "<div class='mark'>Yoga <em>in</em> Melbourne</div>"


def card(n, total, img, pos, top_kicker, body, topset=False):
    if topset:
        return f"""
<div class="card topset">
  <img src="{img}" style="object-position:{pos}" alt="">
  <div class="scrim"></div>
  <div class="inner">
    <div class="kicker">{top_kicker}</div>
    {body}
    <div class="rule"></div>
  </div>
  <div class="foot">{WORDMARK}<div class="pip">{n} / {total}</div></div>
</div>"""
    return f"""
<div class="card">
  <img src="{img}" style="object-position:{pos}" alt="">
  <div class="scrim"></div>
  <div class="top"><div class="kicker">{top_kicker}</div></div>
  <div class="inner">
    {body}
    <div class="rule"></div>
    <div class="foot">{WORDMARK}<div class="pip">{n} / {total}</div></div>
  </div>
</div>"""


def build(teacher, where, sched_line, lead):
    c1 = card(1, 3, "01-oak.jpg", "36% 40%", "A new profile",
              f"<div class='name'>{teacher}</div>"
              f"<div class='sub'><b>{where}</b></div>")
    # Schedule data is factual and public and needs nobody's approval to state.
    # It is also the one thing a studio-siloed booking system cannot show, so it
    # belongs on the card that shows her teaching.
    # The schedule IS the card. It is factual, public, needs nobody's approval,
    # and it is the one thing a studio-siloed booking system cannot show. A line
    # of invented atmosphere in its place would say nothing and risk saying it
    # wrongly about a person who has not yet read her own profile.
    # 18%, not 96%. The SOURCE photograph already slices the student's head at its
    # own bottom edge, so biasing the crop downward only enlarges a decapitation
    # that no crop can undo. Cropping above her hairline removes the partial head
    # entirely — a torso being adjusted reads as a hands-on class; half a head at
    # the frame edge reads as a mistake.
    c2 = card(2, 3, "02-teaching.jpg", "52% 18%", "Where to find her",
              f"<div class='lead'>{sched_line}</div>"
              f"<div class='sub'>{where}</div>", topset=True)
    # No kicker and no second wordmark here: the line already says "coming soon"
    # and already names the publication, so repeating either underneath is the
    # card arguing with itself.
    c3 = f"""
<div class="card paper">
  <div class="photo"><img src="03-practice.jpg" alt=""></div>
  <div class="inner">
    <div class="lead">{lead}</div>
    <div class="tag">Coming soon to Yoga <em>in</em> Melbourne</div>
    <div class="url">yogainmelbourne.com.au</div>
    <div class="rule"></div>
    <div class="foot"><div class="pip">3 / 3</div></div>
  </div>
</div>"""
    return [("01-announce", c1), ("02-in-the-room", c2), ("03-coming-soon", c3)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="carousel/shelley")
    ap.add_argument("--teacher", required=True,
                    help="exactly as she appears in data/schedule.json")
    ap.add_argument("--where", help="override the studio line (rarely needed)")
    ap.add_argument("--schedule", help="override the schedule line (rarely needed)")
    ap.add_argument("--lead", default="Her story\u2026",
                    help="the closing headline. 'His story…' for a man — the script "
                         "will not guess a pronoun from a name.")
    ap.add_argument("--no-png", action="store_true")
    a = ap.parse_args()

    sched_line, where = from_schedule(a.teacher)
    if a.schedule or a.where:
        print("  ! overriding schedule.json — the card can now contradict the site")
    sched_line, where = a.schedule or sched_line, a.where or where
    print(f"  {a.teacher} — {where} — {sched_line}")

    out = ROOT / a.dir
    out.mkdir(parents=True, exist_ok=True)
    missing = [f for f in ("01-oak.jpg", "02-teaching.jpg", "03-practice.jpg")
               if not (out / f).exists()]
    if missing:
        raise SystemExit(f"{out.relative_to(ROOT)}/ is missing {', '.join(missing)}")
    frames = build(a.teacher, where, sched_line, a.lead)
    doc = (f"<!doctype html><html lang='en-AU'><head><meta charset='utf-8'>"
           f"<title>{a.teacher} carousel</title>"
           f"<style>{FONT_FACES}{CSS}</style></head><body>"
           + "\n".join(h for _, h in frames) + "</body></html>")
    (out / "cards.html").write_text(doc, encoding="utf-8")
    print(f"{len(frames)} cards -> {out.relative_to(ROOT)}/cards.html")
    if a.no_png:
        return

    from playwright.sync_api import sync_playwright
    exe = os.environ.get("CHROMIUM_EXECUTABLE")
    with sync_playwright() as p:
        b = p.chromium.launch(**({"executable_path": exe} if exe else {}))
        pg = b.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=1)
        pg.goto((out / "cards.html").as_uri())
        pg.wait_for_timeout(900)      # let the embedded webfonts and photos paint
        for i, (name, _) in enumerate(frames):
            f = out / f"card-{name}.png"
            pg.locator(".card").nth(i).screenshot(path=str(f))
            print(f"  {f.name}")
        b.close()


if __name__ == "__main__":
    main()
