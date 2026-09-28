#!/usr/bin/env python3
"""
build_podcast_reel.py: 1080x1920 frames for a Conversations episode reel.

Rebuilt 25 Sep 2026. The original lived outside the repo and was lost with a
workspace; that is why it now sits here beside build_solo_reel.py, where the
nightly cannot reach it but a future session can.

Shape: her words first, the episode last. notes/YIM-instagram-acquisition-2026-08-19.md
measured 0.30% follows per eligible viewer for reels that led with the thing
being promoted against 2.93% for reels that led with people. So the opening
frames carry quotations and nothing else, and only the closer says where to
listen.

    python3 build_podcast_reel.py --spec reel/masha/spec.json --dir reel/masha \\
        --title "Masha Gorodilova" --episode "Episode 9" \\
        --sub "Siberia, a back room on Collins Street, and what a class is for."

The spec is a JSON list, one object per photo frame:

    {"name": "01-open", "plate": "hero.jpg", "quote": "My life without yoga is miserable.",
     "cite": "Masha Gorodilova", "zoom": 1.00, "ay": 0.22}

`quote` is verbatim and is wrapped in quotation marks here, so the spec must not
include them. `zoom` and `ay` crop the plate: a plate is already 1080x1920, so
object-position alone is inert and every frame renders identically without them.

SAFE ZONES. Instagram covers the bottom 420px, the top 150px and the right 100px
of a 1080x1920 reel. Those are not the margins used here, because
build_reel_video.py zooms each still to 1.13 and a centred zoom pushes type
outward: a line sitting 420px off the bottom lands at about 300px once the zoom
is at maximum. The margins below are the covered area scaled back through that
zoom, with a little air on top:

    top 250   bottom 500   right 160   left 112

Verify a finished reel against stills pulled from the MP4, never against these
PNGs. The PNGs are the unzoomed frame and will always look safe.
"""
import argparse, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE_CSS = (ROOT / "partials" / "base.css").read_text()
FONT_FACES = "\n".join(re.findall(r"@font-face\{[^}]*\}", BASE_CSS))

VARS = """
:root{
  --paper:#E7D9C0; --paper-deep:#DECDAE; --ink:#2A201A; --ink-soft:#5A4B3E;
  --henna:#9E3B26; --clay:#BC6B3C; --sage:#6F7155; --ochre:#C2974F;
}
"""

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{background:#3a3a3a;font-family:'Hanken Grotesk',system-ui,sans-serif}
.f{width:1080px;height:1920px;background:var(--paper);color:var(--paper);
   position:relative;overflow:hidden;display:flex;flex-direction:column;
   justify-content:flex-end}
.f + .f{margin-top:40px}
/* The plate lives in its own clipping box. A frame's crop is a CSS transform on
   the photograph, and a scaled image still counts toward its parent's
   scrollHeight even under overflow:hidden, so without this wrapper every
   zoomed frame reports an overflow and the build refuses to ship a set that is
   fine. Clipping here keeps the overflow check about the type, which is the
   thing that actually breaks. */
.plate{position:absolute;inset:0;overflow:hidden}
.plate img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.scrim{position:absolute;inset:0;
  background:
    linear-gradient(to top, rgba(20,14,10,.92) 0%, rgba(20,14,10,.72) 30%,
                    rgba(20,14,10,.16) 56%, rgba(20,14,10,0) 70%),
    linear-gradient(to bottom, rgba(20,14,10,.34) 0%, rgba(20,14,10,0) 22%);
}
/* Safe zones, zoom-aware. See the module docstring before changing a number. */
.inner{position:relative;padding:0 160px 500px 112px}
.top{position:absolute;top:250px;left:112px;right:160px}
.kicker{font-family:'Spline Sans Mono',monospace;font-size:27px;letter-spacing:.22em;
        text-transform:uppercase;color:#E8C9A8;margin-bottom:30px}
.quote{font-family:'Fraunces',serif;font-weight:400;font-size:62px;line-height:1.18}
.quote em{font-style:italic;color:#E8A88A}
/* 22px, not 58: the block is bottom-aligned, so every pixel of gap below the
   quotation pushes the quotation up into her face. Tightened 21 Sep 2026 after
   Ryan's frame covered his jaw. */
.cite{font-family:'Spline Sans Mono',monospace;font-size:26px;letter-spacing:.06em;
      color:rgba(231,217,192,.66);margin-top:22px}
.rule{height:1px;background:rgba(231,217,192,.34);margin:30px 0 26px}
.mark{font-family:'Fraunces',serif;font-size:42px;line-height:1;color:var(--paper)}
.mark em{font-style:italic;color:#E8A88A}
.bio{font-family:'Spline Sans Mono',monospace;font-size:25px;letter-spacing:.14em;
     text-transform:uppercase;color:#E8A88A}
.foot{display:flex;align-items:flex-end;justify-content:space-between}

/* The closer: the publication speaking, so ink on cream and no photograph. */
.f.paper{background:var(--paper);color:var(--ink);justify-content:center}
.f.paper .inner{padding:0 160px 0 112px}
.f.paper .kicker{color:var(--henna)}
.f.paper .foot{position:absolute;bottom:500px;left:112px;right:160px}
.f.paper .mark{color:var(--ink)}
.f.paper .mark em{color:var(--henna)}
.f.paper .bio{color:var(--henna)}
.f.paper .title{font-family:'Fraunces',serif;font-size:86px;line-height:1.06;
      color:var(--ink);margin-top:24px}
.f.paper .title em{font-style:italic;color:var(--henna)}
.f.paper .sub{font-size:34px;line-height:1.4;color:var(--ink-soft);margin-top:28px;max-width:22ch}
.f.paper .where{margin-top:44px;font-family:'Spline Sans Mono',monospace;font-size:27px;
      letter-spacing:.14em;text-transform:uppercase;color:var(--henna)}
.omega{position:absolute;top:250px;left:112px;font-family:'Fraunces',serif;
       font-size:64px;color:rgba(42,32,26,.20)}
"""

WORDMARK = "<div class='mark'>Yoga <em>in</em> Melbourne</div>"
BIO = "<div class='bio'>Link in bio</div>"


def build(spec, title, episode, sub, listen):
    F = []
    for fr in spec:
        zoom, ay = fr.get("zoom", 1.0), fr.get("ay", 0.22)
        style = f"transform:scale({zoom});transform-origin:50% {ay * 100:.0f}%"
        kicker = f"<div class='top'><div class='kicker'>{fr['kicker']}</div></div>" if fr.get("kicker") else ""
        F.append((fr["name"], f"""
<div class="f">
  <div class="plate"><img src="{fr['plate']}" alt="" style="{style}"></div>
  <div class="scrim"></div>
  {kicker}
  <div class="inner">
    <div class="quote">&ldquo;{fr['quote']}&rdquo;</div>
    <div class="cite">{fr['cite']}</div>
    <div class="rule"></div>
    <div class="foot">{WORDMARK}{BIO}</div>
  </div>
</div>"""))

    F.append(("99-closer", f"""
<div class="f paper">
  <div class="omega">&#2384;</div>
  <div class="inner">
    <div class="kicker">Conversations &middot; {episode}</div>
    <div class="title">{title}</div>
    <div class="sub">{sub}</div>
    <div class="where">{listen}</div>
  </div>
  <div class="foot">{WORDMARK}{BIO}</div>
</div>"""))
    return F


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--dir", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--episode", required=True)
    ap.add_argument("--sub", default="")
    ap.add_argument("--listen", default="Listen at Yoga in Melbourne")
    ap.add_argument("--no-png", action="store_true")
    a = ap.parse_args()

    out = ROOT / a.dir
    out.mkdir(parents=True, exist_ok=True)
    spec = json.loads(Path(a.spec).read_text(encoding="utf-8"))
    for fr in spec:
        if not (out / fr["plate"]).exists():
            raise SystemExit(f"{a.dir}/{fr['plate']} is missing")
        if '"' in fr["quote"] or "“" in fr["quote"]:
            raise SystemExit(f"{fr['name']}: the builder adds the quotation marks")

    frames = build(spec, a.title, a.episode, a.sub, a.listen)
    doc = (f"<!doctype html><html lang='en-AU'><head><meta charset='utf-8'>"
           f"<style>{FONT_FACES}{VARS}{CSS}</style></head><body>"
           + "\n".join(h for _, h in frames) + "</body></html>")
    (out / "frames.html").write_text(doc, encoding="utf-8")
    print(f"  {len(frames)} frames -> {a.dir}/frames.html")
    if a.no_png:
        return

    import os
    from playwright.sync_api import sync_playwright
    exe = os.environ.get("CHROMIUM_EXECUTABLE")
    with sync_playwright() as p:
        b = p.chromium.launch(**({"executable_path": exe} if exe else {}))
        pg = b.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=1)
        pg.goto((out / "frames.html").as_uri())
        pg.wait_for_timeout(1600)
        over = pg.eval_on_selector_all(".f", "els => els.map(e => e.scrollHeight > 1920)")
        for i, (name, _) in enumerate(frames):
            f = out / f"{name}.png"
            pg.locator(".f").nth(i).screenshot(path=str(f))
            print(f"  {f.name}{'  OVERFLOW' if over[i] else ''}")
        b.close()
    if any(over):
        raise SystemExit("A frame overflowed. Do not post this set.")


if __name__ == "__main__":
    main()
