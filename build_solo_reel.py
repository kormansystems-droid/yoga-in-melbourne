#!/usr/bin/env python3
"""
build_solo_reel.py: 1080x1920 frames for a solo teacher reel.

Three frames, revised 1 Sep 2026 (Mark):

  01-opener-teacher  her name, and the fact that the profile is live
                     (named "opener" so build_reel_video.py gives it its own hold)
  02-story    the arc and her own words, merged into one card
  03-retreat  what she runs away from the studio (optional, see below)
  04-closer   read the profile, hear the story, at yogainmelbourne.com.au

The retreat card renders two ways. Drop a 1080x1920 photograph at
<dir>/retreat.jpg and it becomes a photo card; with no file there it falls back
to a paper card in ink on cream, which is a deliberate design and not a
placeholder. Pass --no-retreat to drop the card entirely.

NOTHING PERISHABLE GOES ON THAT CARD. As of the 20 Aug interview the retreat had
"two places left" and no published dates, price or booking link. A reel outlives
the day it is posted, and a sold-out retreat advertised as having places is worse
than no card. State the shape of the thing; let the profile carry the details.

No episode frame, no schedule frame, no map opener. Earlier cuts carried all
three. What replaced them: the podcast is not named at all, because the thing
being promoted is the PROFILE, and "hear her story" already routes a listener
to the audio that sits on the profile page.

Worth keeping in view. notes/YIM-instagram-acquisition-2026-08-19.md measured
podcast-episode promos at 0.30% follows per viewer against 2.93% for everything
else (9.6x, Fisher p = 8.6e-6) and concluded the variable is the PROPOSITION,
not the container. This cut is consistent with that finding rather than against
it: the note's two best performers were pieces presenting the publication and
its people, and a profile announcement is exactly that. What has gone is the
explicit map proposition in the opening seconds, so the publication now rests on
the closer alone.

Judge on PROFILE VISITS PER VIEWER. It moves first and on smaller numbers than
follows. Baselines: Alessia's podcast reel 1.27%, Alessia's carousel 4.35%.

    python3 build_solo_reel.py --teacher "Shelley Armstrong" --dir reel/shelley
    python3 build_reel_video.py --dir reel/shelley --out reel/shelley/reel.mp4 \
            --hold 3.8 --final 4.4
"""
import argparse, re, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCHED = ROOT / "data" / "schedule.json"
BASE_CSS = (ROOT / "partials" / "base.css").read_text()
FONT_FACES = "\n".join(re.findall(r"@font-face\{[^}]*\}", BASE_CSS))

DAY_PLURAL = {"Mon":"Mondays","Tue":"Tuesdays","Wed":"Wednesdays","Thu":"Thursdays",
              "Fri":"Fridays","Sat":"Saturdays","Sun":"Sundays"}
DAY_ORDER = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]


def _start(t):
    m = re.match(r"\s*(\d{1,2})(?::(\d{2}))?", t or "")
    if not m: return (t or "").strip()
    ap = re.search(r"(am|pm)", t or "", re.I)
    hh, mm = m.group(1), m.group(2)
    return f"{hh}:{mm}{ap.group(1).lower()}" if mm else f"{hh}{ap.group(1).lower() if ap else ''}"


def from_schedule(name):
    """Read the classes off the same file the site renders from. Never retype
    them; that is how a card ends up contradicting the page it points at."""
    data = json.loads(SCHED.read_text(encoding="utf-8"))
    teachers = data.get("teachers", {})
    t = teachers.get(name)
    if not t:
        for k, v in teachers.items():
            if name.lower() in [a.lower() for a in v.get("aliases", [])]:
                print(f"  '{name}' is an alias, using '{k}'"); name, t = k, v; break
    if not t:
        raise SystemExit(f"'{name}' is not in data/schedule.json. Add her there first.")
    classes = sorted(t.get("classes", []), key=lambda c: DAY_ORDER.index(c["day"]))
    if not classes:
        raise SystemExit(f"'{name}' has no classes in data/schedule.json.")
    studios = data["studios"]
    sids = sorted({c["studio"] for c in classes})
    brands = {}
    for sid in sids:
        m = studios.get(sid, {})
        brands.setdefault(m.get("name", sid), []).append(m.get("location", ""))
    n = list(brands)[0]; locs = [l for l in brands[n] if l]
    where = f"{n}, {locs[0]}" if len(locs) == 1 else n
    rows = [(f"{DAY_PLURAL[c['day']]}", _start(c["time"]), c["class"]) for c in classes]
    return rows, where, len(classes), len(sids)


CSS = """
:root{
  --paper:#E7D9C0; --paper-deep:#DECDAE; --ink:#2A201A; --ink-soft:#5A4B3E;
  --henna:#9E3B26; --clay:#BC6B3C; --sage:#6F7155; --ochre:#C2974F;
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:#3a3a3a;font-family:'Hanken Grotesk',system-ui,sans-serif}
.f{width:1080px;height:1920px;background:var(--paper);color:var(--paper);
   position:relative;overflow:hidden;display:flex;flex-direction:column;
   justify-content:flex-end}
.f + .f{margin-top:40px}
.f img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;
        transform-origin:50% 22%}
/* The plate is exactly 1080x1920, so object-position alone is inert: a cover
   image the same size as its box has nothing to slide. Frames 2-4 came out
   identical until these scales were added. Each frame is now a real crop, and
   build_reel_video.py's zoompan drifts on top of it. */
.f.z1 img{transform:scale(1.00)}
.f.z2 img{transform:scale(1.34) translateY(4%)}
.f.z3 img{transform:scale(1.62) translateY(4%)}   /* translate is applied BEFORE scale, so it is multiplied by it; 9% left an 18px gap at the top edge */
/* Two scrims, as on the carousel cards: a deep one at the foot for the type,
   a whisper at the head so the kicker reads without greying her face. */
.scrim{position:absolute;inset:0;
  background:
    linear-gradient(to top, rgba(20,14,10,.90) 0%, rgba(20,14,10,.68) 26%,
                    rgba(20,14,10,.14) 52%, rgba(20,14,10,0) 66%),
    linear-gradient(to bottom, rgba(20,14,10,.36) 0%, rgba(20,14,10,0) 22%);
}
/* A landscape plate is bright in exactly the band where a portrait plate is
   dark, so the scrim above leaves the kicker and the headline sitting on cloud.
   Measured on the Kula Muriwai photograph, 1 Sep 2026: the stock scrim put
   "RETREAT . MURIWAI, NEW ZEALAND" over blown highlights and it was unreadable
   at phone size. This one is deeper and reaches higher, and still leaves the top
   sixth of the frame clear so the picture is a picture and not a texture.
   Applied to the retreat photo card only. Do not make it the default: on a
   portrait plate it crushes the face. */
.scrim.deep{
  background:
    linear-gradient(to top, rgba(20,14,10,.94) 0%, rgba(20,14,10,.88) 30%,
                    rgba(20,14,10,.66) 50%, rgba(20,14,10,.24) 68%,
                    rgba(20,14,10,0) 84%),
    linear-gradient(to bottom, rgba(20,14,10,.30) 0%, rgba(20,14,10,0) 20%);
}
.inner{position:relative;padding:0 92px 132px}
.top{position:absolute;top:104px;left:92px;right:92px}
.kicker{font-family:'Spline Sans Mono',monospace;font-size:27px;letter-spacing:.22em;
        text-transform:uppercase;color:#E8C9A8;margin-bottom:30px}
.name{font-family:'Fraunces',serif;font-weight:400;font-size:116px;line-height:1.0;
      letter-spacing:-.01em}
.name em{font-style:italic;color:#E8A88A}
.lead{font-family:'Fraunces',serif;font-weight:400;font-size:74px;line-height:1.14}
.lead em{font-style:italic;color:#E8A88A}
.arc{font-family:'Hanken Grotesk',sans-serif;font-size:34px;line-height:1.46;
     color:rgba(231,217,192,.84);margin-bottom:34px;max-width:30ch}
.arc em{font-style:italic;color:#E8A88A;font-weight:500}
.quote{font-family:'Fraunces',serif;font-weight:400;font-size:56px;line-height:1.20}
.quote em{font-style:italic;color:#E8A88A}
.sub{font-size:36px;line-height:1.42;color:rgba(231,217,192,.86);margin-top:30px;max-width:26ch}
.sub b{font-weight:600;color:var(--paper)}
.rule{height:1px;background:rgba(231,217,192,.34);margin:46px 0 34px}
.mark{font-family:'Fraunces',serif;font-size:42px;line-height:1;color:var(--paper)}
.mark em{font-style:italic;color:#E8A88A}
.url{font-family:'Spline Sans Mono',monospace;font-size:27px;letter-spacing:.06em;
     color:rgba(231,217,192,.78);margin-top:36px}
.foot{display:flex;align-items:flex-end;justify-content:space-between}
.bio{font-family:'Spline Sans Mono',monospace;font-size:25px;letter-spacing:.14em;
     text-transform:uppercase;color:#E8A88A}
.cite{font-family:'Spline Sans Mono',monospace;font-size:26px;letter-spacing:.06em;
      color:rgba(231,217,192,.66);margin-top:30px}


/* Paper frames: the map opener and the closer. Ink on cream, no photograph:
   these are the publication speaking, not the teacher. */
.f.paper{background:var(--paper);color:var(--ink);justify-content:center}
.f.paper .inner{padding:0 92px}
.f.paper .kicker{color:var(--henna)}
.f.paper .lead{color:var(--ink)}
.f.paper .lead em{color:var(--henna)}
.f.paper .sub{color:var(--ink-soft)}
.f.paper .sub b{color:var(--ink)}
.f.paper .rule{background:rgba(42,32,26,.22)}
.f.paper .mark{color:var(--ink)}
.f.paper .mark em{color:var(--henna)}
.f.paper .bio{color:var(--henna)}
.f.paper .url{color:var(--sage)}
.f.paper .foot{position:absolute;bottom:132px;left:92px;right:92px}
.omega{position:absolute;top:104px;left:92px;font-family:'Fraunces',serif;
       font-size:64px;color:rgba(42,32,26,.20)}
"""

WORDMARK = "<div class='mark'>Yoga <em>in</em> Melbourne</div>"
BIO = "<div class='bio'>Link in bio</div>"


def build(teacher, given, where, plate, quote, cite, arc,
          retreat, retreat_img, retreat_kicker, retreat_lead, retreat_body):
    F = []

    # 1. The announcement. Her name, and the one fact the reel exists to carry.
    F.append(("01-opener-teacher", f"""
<div class="f z1">
  <img src="{plate}" alt="">
  <div class="scrim"></div>
  <div class="top"><div class="kicker">Teacher &middot; {where}</div></div>
  <div class="inner">
    <div class="name">{teacher}</div>
    <div class="sub"><b>Her profile is now live on Yoga in Melbourne.</b></div>
    <div class="rule"></div>
    <div class="foot">{WORDMARK}{BIO}</div>
  </div>
</div>"""))

    # 2. Arc and quote merged. These were two cards until 1 Sep; separating the
    #     setup from the line it sets up cost four seconds and said it twice.
    F.append(("02-story", f"""
<div class="f z2">
  <img src="{plate}" alt="">
  <div class="scrim"></div>
  <div class="inner">
    <div class="arc">{arc}</div>
    <div class="quote">{quote}</div>
    <div class="cite">{cite}</div>
    <div class="rule"></div>
    <div class="foot">{WORDMARK}{BIO}</div>
  </div>
</div>"""))

    # 3. The retreat. Photo card if <dir>/retreat.jpg exists, paper card if not.
    if retreat:
        body = (f"<div class='kicker'>{retreat_kicker}</div>"
                f"<div class='lead'>{retreat_lead}</div>"
                f"<div class='sub'>{retreat_body}</div>")
        if retreat_img:
            F.append(("03-retreat", f"""
<div class="f z1">
  <img src="{retreat_img}" alt="">
  <div class="scrim deep"></div>
  <div class="inner">
    {body}
    <div class="rule"></div>
    <div class="foot">{WORDMARK}{BIO}</div>
  </div>
</div>"""))
        else:
            F.append(("03-retreat", f"""
<div class="f paper">
  <div class="omega">&#2384;</div>
  <div class="inner">
    {body}
  </div>
  <div class="foot">{WORDMARK}{BIO}</div>
</div>"""))

    # 4. The closer. The podcast is not named: "hear her story" routes to the
    #     player that already sits on her profile page, and the publication is
    #     the thing being sold.
    F.append(("04-closer", f"""
<div class="f paper">
  <div class="omega">&#2384;</div>
  <div class="inner">
    <div class="kicker">Yoga in Melbourne</div>
    <div class="lead">Read her profile.<br>Hear her story <em>in her own words.</em></div>
    <div class="url">www.yogainmelbourne.com.au</div>
  </div>
  <div class="foot">{WORDMARK}{BIO}</div>
</div>"""))
    return F


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--teacher", required=True, help="exactly as in data/schedule.json")
    ap.add_argument("--dir", required=True)
    ap.add_argument("--plate", default="plate.jpg", help="1080x1920 photo plate in --dir")
    ap.add_argument("--quote", required=True)
    ap.add_argument("--cite", required=True)
    ap.add_argument("--arc", required=True, help="the one-card biography beat")
    ap.add_argument("--no-retreat", action="store_true", help="drop the retreat card")
    ap.add_argument("--retreat-img", default="retreat.jpg",
                    help="1080x1920 photo in --dir; falls back to a paper card if absent")
    ap.add_argument("--retreat-kicker", default="")
    ap.add_argument("--retreat-lead", default="")
    ap.add_argument("--retreat-body", default="")
    ap.add_argument("--no-png", action="store_true")
    a = ap.parse_args()

    # Still read from schedule.json even though no timetable is shown: `where`
    # must not be retyped by hand, and a teacher missing from the file is an
    # error worth stopping for.
    rows, where, n, nst = from_schedule(a.teacher)
    given = a.teacher.split()[0]
    out = ROOT / a.dir; out.mkdir(parents=True, exist_ok=True)
    if not (out / a.plate).exists():
        raise SystemExit(f"{a.dir}/{a.plate} missing. The reel needs a 1080x1920 plate.")
    print(f"  {a.teacher} / {where} / {n} class(es) across {nst} studio(s)")

    rimg = a.retreat_img if (out / a.retreat_img).exists() else None
    if not a.no_retreat:
        print(f"  retreat card: {'photo (' + a.retreat_img + ')' if rimg else 'paper fallback, no ' + a.retreat_img}")
    frames = build(a.teacher, given, where, a.plate, a.quote, a.cite, a.arc,
                   not a.no_retreat, rimg, a.retreat_kicker, a.retreat_lead, a.retreat_body)
    doc = (f"<!doctype html><html lang='en-AU'><head><meta charset='utf-8'>"
           f"<title>{a.teacher} reel</title><style>{FONT_FACES}{CSS}</style></head>"
           f"<body>" + "\n".join(h for _, h in frames) + "</body></html>")
    (out / "frames.html").write_text(doc, encoding="utf-8")
    print(f"{len(frames)} frames -> {a.dir}/frames.html")
    if a.no_png: return

    import os
    from playwright.sync_api import sync_playwright
    exe = os.environ.get("CHROMIUM_EXECUTABLE")
    with sync_playwright() as p:
        b = p.chromium.launch(**({"executable_path": exe} if exe else {}))
        pg = b.new_page(viewport={"width":1080,"height":1920}, device_scale_factor=1)
        pg.goto((out / "frames.html").as_uri()); pg.wait_for_timeout(1200)
        for i,(name,_) in enumerate(frames):
            f = out / f"{name}.png"
            pg.locator(".f").nth(i).screenshot(path=str(f)); print(f"  {f.name}")
        b.close()


if __name__ == "__main__":
    main()
