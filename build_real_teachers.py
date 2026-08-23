#!/usr/bin/env python3
"""
build_real_teachers.py — "The Real Teachers of Yoga in Melbourne".

An opener on paper plus one photographic card per teacher. Renders the same
set at 1080x1350 (feed, collab post) and 1080x1920 (reel frames), so the reel
is not a crop of the feed card — the type is laid out for the frame it is in.
Names get cut when you crop 4:5 to 9:16; laying out twice costs nothing and
loses nothing.

The reel frames carry wider margins than the feed cards on purpose: the
Ken Burns push in build_reel_video.py crops ~6% off every edge by the end of
a hold, and 84px of padding does not survive that. The type has to be laid
out for the frame it ends on, not the frame it starts on.
"""
import re, os, sys, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "carousel" / "real-teachers"
BASE_CSS = (ROOT / "partials" / "base.css").read_text()
FONT_FACES = "\n".join(re.findall(r"@font-face\{[^}]*\}", BASE_CSS))

# object-position per teacher, per aspect. 9:16 keeps less width, so a face
# that sat comfortably at 50% in 4:5 can drift out of the taller frame.
TEACHERS = [
    ("Ryan Mannix",       "ryan.jpg",    "Good Vibes and Kozen Yoga", "50% 22%", "50% 20%"),
    ("Masha Gorodilova",  "masha.jpg",   "Within, South Yarra",       "50% 34%", "52% 32%"),
    ("Sarah Metzger",     "sarah.jpg",   "(Here) Yoga and Warrior One","50% 30%", "50% 28%"),
    ("Shelley Armstrong", "shelley.jpg", "Grass Roots, St Kilda",     "22% 34%", "29% 34%"),
    ("Franks Martin",     "franks.jpg",  "Warrior One, Brighton",     "50% 26%", "90% 24%"),
]

OM = "ॐ"

CSS = """
:root{
  --paper:#E7D9C0; --paper-deep:#DECDAE; --ink:#2A201A; --ink-soft:#5A4B3E;
  --henna:#9E3B26; --clay:#BC6B3C; --sage:#6F7155; --ochre:#C2974F;
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:#3a3a3a;font-family:'Hanken Grotesk',system-ui,sans-serif}
.card{width:__W__px;height:__H__px;background:var(--paper);color:var(--paper);
  position:relative;overflow:hidden;display:flex;flex-direction:column;
  justify-content:flex-end}
.card + .card{margin-top:40px}
.card img.bg{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.scrim{position:absolute;inset:0;
  background:
    linear-gradient(to top, rgba(20,14,10,.86) 0%, rgba(20,14,10,.62) 22%,
                    rgba(20,14,10,.12) 46%, rgba(20,14,10,0) 62%),
    linear-gradient(to bottom, rgba(20,14,10,.40) 0%, rgba(20,14,10,0) 26%);
}
.inner{position:relative;padding:0 __PADX__px __PADB__px}
.top{position:absolute;top:__TOP__px;left:__PADX__px;right:__PADX__px;
  padding-bottom:0}
.kicker{font-family:'Spline Sans Mono',monospace;font-size:__KICK__px;
  letter-spacing:.22em;text-transform:uppercase;color:#EBA95F;
  text-shadow:0 2px 14px rgba(20,14,10,.55)}
.name{font-family:'Fraunces',serif;font-weight:400;font-size:__NAME__px;
  line-height:1.0;letter-spacing:-.01em}
.sub{font-family:'Hanken Grotesk',sans-serif;font-size:__SUB__px;line-height:1.42;
  color:rgba(231,217,192,.88);margin-top:24px;max-width:26ch}
.rule{height:1px;background:rgba(231,217,192,.34);margin:__RULE__px 0 30px}
.mark{font-family:'Fraunces',serif;font-size:__MARK__px;line-height:1;color:var(--paper)}
.mark em{font-style:italic;color:#E8A88A}
.foot{display:flex;align-items:flex-end;justify-content:space-between}
.bio{font-family:'Spline Sans Mono',monospace;font-size:__BIO__px;letter-spacing:.14em;
  text-transform:uppercase;color:#E8A88A}

/* ---- opener: paper, centred, no photograph ---- */
.card.opener{background:var(--paper);color:var(--ink);
  justify-content:center;align-items:center;text-align:center}
.card.opener .wash{position:absolute;inset:0;
  background:radial-gradient(120% 80% at 50% 8%, rgba(255,255,255,.34) 0%,
             rgba(255,255,255,0) 58%)}
.om{position:absolute;font-family:'Fraunces',serif;color:rgba(42,32,26,.055);
  line-height:1;user-select:none}
.o1{top:__O1T__px;right:__O1R__px;font-size:__OMBIG__px}
.o2{bottom:__O2B__px;left:__O2L__px;font-size:__OMBIG__px}
.o3{bottom:__O3B__px;right:__O3R__px;font-size:__OMSM__px;
  color:rgba(42,32,26,.04)}
.opener .stack{position:relative;padding:0 __PADX__px}
.pre{font-family:'Fraunces',serif;font-style:italic;font-weight:400;
  font-size:__PRE__px;line-height:1.12;color:var(--ink)}
.orule{width:78px;height:2px;background:var(--clay);margin:__ORULE__px auto}
.big{font-family:'Fraunces',serif;font-weight:400;font-size:__BIG__px;
  line-height:1.02;color:var(--ink);letter-spacing:-.015em}
.big em{font-style:italic;color:var(--henna)}
.url{font-family:'Spline Sans Mono',monospace;font-size:__URL__px;
  letter-spacing:.14em;text-transform:uppercase;color:var(--clay);
  margin-top:__URLT__px}
.lib{font-family:'Spline Sans Mono',monospace;font-size:__URL__px;
  letter-spacing:.20em;text-transform:uppercase;color:var(--clay);margin-top:26px}
"""

SIZES = {
    "feed": dict(W=1080, H=1350, PADX=84, PADB=92, TOP=76, KICK=25, NAME=100,
                 SUB=34, RULE=40, MARK=38, BIO=23,
                 PRE=78, ORULE=44, BIG=126, URL=30, URLT=96,
                 OMBIG=620, OMSM=430, O1T=-140, O1R=-90, O2B=-180, O2L=-120,
                 O3B=240, O3R=300),
    "reel": dict(W=1080, H=1920, PADX=112, PADB=232, TOP=228, KICK=27, NAME=100,
                 SUB=36, RULE=44, MARK=40, BIO=24,
                 PRE=84, ORULE=50, BIG=134, URL=32, URLT=110,
                 OMBIG=760, OMSM=520, O1T=-180, O1R=-120, O2B=-220, O2L=-150,
                 O3B=340, O3R=340),
}


def css_for(kind):
    c = CSS
    for k, v in SIZES[kind].items():
        c = c.replace(f"__{k}__", str(v))
    return c


def opener_html():
    return f"""
<div class="card opener">
  <div class="wash"></div>
  <div class="om o1">{OM}</div><div class="om o2">{OM}</div><div class="om o3">{OM}</div>
  <div class="stack">
    <div class="pre">The Real Teachers<br>of&hellip;</div>
    <div class="orule"></div>
    <div class="big">Yoga <em>in</em><br>Melbourne</div>
    <div class="url">yogainmelbourne.com.au</div>
    <div class="lib">Link in bio</div>
  </div>
</div>"""


def teacher_html(name, img, sub, pos):
    return f"""
<div class="card">
  <img class="bg" src="src/{img}" style="object-position:{pos}" alt="">
  <div class="scrim"></div>
  <div class="top"><div class="kicker">The Real Teachers</div></div>
  <div class="inner">
    <div class="name">{name}</div>
    <div class="sub">{sub}</div>
    <div class="rule"></div>
    <div class="foot">
      <div class="mark">Yoga <em>in</em> Melbourne</div>
      <div class="bio">Link in bio</div>
    </div>
  </div>
</div>"""


def build(kind):
    idx = 3 if kind == "feed" else 4
    frames = [("00-opener", opener_html())]
    for i, (name, img, sub, p45, p916) in enumerate(TEACHERS, 1):
        slug = name.split()[0].lower()
        frames.append((f"{i:02d}-{slug}", teacher_html(name, img, sub,
                                                       p45 if kind == "feed" else p916)))
    doc = ("<!doctype html><html lang='en-AU'><head><meta charset='utf-8'>"
           "<title>The Real Teachers</title>"
           f"<style>{FONT_FACES}{css_for(kind)}</style></head><body>"
           + "\n".join(h for _, h in frames) + "</body></html>")
    page = OUT / f"cards-{kind}.html"
    page.write_text(doc, encoding="utf-8")

    from playwright.sync_api import sync_playwright
    exe = os.environ.get("CHROMIUM_EXECUTABLE")
    s = SIZES[kind]
    dest = OUT / kind
    dest.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(**({"executable_path": exe} if exe else {}))
        pg = b.new_page(viewport={"width": s["W"], "height": s["H"]}, device_scale_factor=1)
        pg.goto(page.as_uri())
        pg.wait_for_timeout(1100)
        for i, (nm, _) in enumerate(frames):
            f = dest / f"{nm}.png"
            pg.locator(".card").nth(i).screenshot(path=str(f))
            print(f"  {kind}/{f.name}")
        b.close()


if __name__ == "__main__":
    for k in (sys.argv[1:] or ["feed", "reel"]):
        build(k)
