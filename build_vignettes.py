#!/usr/bin/env python3
"""
build_vignettes.py: the small round portraits beside each name in the homepage
router. Writes img/vig/<slug>.jpg, one per teacher template that carries a photo.

    python3 build_vignettes.py

Run this by hand after adding a teacher. It is NOT part of the nightly build,
and that is deliberate: see "Why these are files" below.

Why these are files and not data URIs
-------------------------------------
Every other portrait on this site is a base64 data URI embedded straight into the
HTML. That is right for a teacher's own page (one photo, self-contained, no second
request) and for the Teachers grid (a showcase, and the images are the content).

It is wrong here. The router lists EVERY registered teacher, so the cost scales
with the roster: the eleven template portraits are 64–187 KB of base64 each, and
inlining them would add roughly 1.2 MB to a 878 KB index.html. The homepage would
more than double in size to decorate a navigation strip. As separate files at
160x160 they are ~6 KB each, they cache independently of the HTML, and
`loading="lazy"` means the ones below the fold cost nothing on first paint.

Why this is not in the nightly build
------------------------------------
`pull.yml` installs exactly one package: playwright. It does NOT install Pillow.
`pull/pull.py` runs `build_profiles.py` with `check=True`, so an ImportError in
build_profiles would fail the subprocess, fail pull.py, and take the whole nightly
timetable refresh down with it.

So build_profiles.py must never import PIL. It only checks whether
img/vig/<slug>.jpg exists on disk and links to it, which needs no dependency at
all. All the image work happens here, manually, where Pillow is available.

If you add Pillow to the workflow one day you could fold this in: but the current
split means a missing vignette degrades to a name with no photo, while a broken
build_profiles.py stops the timetable updating. Those are not the same failure.

Source of truth
---------------
The photograph already embedded in templates/<slug>.template.html at 880x1100 -
the one the teacher supplied. Same source `build_story_cards.py` uses, so the
homepage, the profile page and the Instagram cards can never drift apart, and no
new asset has to be kept in step by hand.
"""
import base64, io, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TEMPLATES = ROOT / "templates"
OUT = ROOT / "img" / "vig"

# 160px covers a ~56px display box on a 2.8x screen. Larger buys nothing at this
# size and every extra kilobyte is multiplied by the length of the roster.
PX = 160
QUALITY = 82

# Per-teacher crop overrides: slug -> (centre_x, centre_y, side), all as a
# fraction: x and y of the source's width and height, side of its short edge.
#
# The default below (a full-width square anchored 6% down) assumes a portrait
# where the head sits in the top third. That holds for ten of eleven photographs
# and produces a good 56px circle with no hand-tuning.
#
# It fails for Janita. Her photograph is not a headshot: it is a wide seated
# shot, taken from her right while she adjusts a student, her face turned down
# and roughly 58% across the frame. The default square puts her shoulder in the
# middle of the circle and her face against the top edge, and NO vertical anchor
# fixes it, because the problem is horizontal. Tested 0.0 through 0.30: all bad.
#
# So the escape hatch is a crop box, not a different anchor. Add an entry here
# rather than re-tuning the default: the default is right for the common case
# and every teacher who follows.
#
# Judge these at 56px, not at 160. A crop that looks tight in a contact sheet
# reads correctly in the router; one that looks fine large becomes a smudge.
CROP = {
    "janita-doelken": (0.58, 0.22, 0.58),
}


def portrait_bytes(tpl: Path):
    m = re.search(r'data:image/jpeg;base64,([A-Za-z0-9+/=]{500,})',
                  tpl.read_text(encoding="utf-8"))
    return base64.b64decode(m.group(1)) if m else None


def main():
    from PIL import Image
    OUT.mkdir(parents=True, exist_ok=True)
    tpls = sorted(t for t in TEMPLATES.glob("*.template.html")
                  if not t.name.startswith("_"))
    if not tpls:
        raise SystemExit("no templates")

    made, skipped = 0, []
    for tpl in tpls:
        slug = tpl.name.replace(".template.html", "")
        raw = portrait_bytes(tpl)
        if not raw:
            skipped.append(slug)
            continue
        im = Image.open(io.BytesIO(raw)).convert("RGB")
        w, h = im.size
        if slug in CROP:
            cx, cy, sf = CROP[slug]
            side = int(min(w, h) * sf)
            left = int(w * cx - side / 2)
            top = int(h * cy - side / 2)
        else:
            side = min(w, h)
            left = (w - side) // 2
            # Anchor high. A head sits in the top third of a portrait crop, so a
            # centred square cuts the face off at the chin. Same 6% as
            # build_story_cards.teacher_portrait, so the two crops agree.
            top = int(h * 0.06)
        # Clamp last, so an override can be written in natural coordinates
        # without having to know the source dimensions.
        left = max(0, min(left, w - side))
        top = max(0, min(top, h - side))
        im = im.crop((left, top, left + side, top + side)).resize(
            (PX, PX), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=QUALITY, optimize=True, progressive=True)
        (OUT / f"{slug}.jpg").write_bytes(buf.getvalue())
        print(f"  img/vig/{slug}.jpg  {len(buf.getvalue()):,} bytes")
        made += 1

    print(f"\n{made} vignettes -> img/vig/")
    if skipped:
        # Not an error. build_profiles.py renders these as a name with no photo,
        # holding the column so the names keep one left edge. An empty circle
        # reads as a broken image; empty space reads as a name.
        print("no photograph in the template, so no vignette (name renders alone):")
        for s in skipped:
            print(f"  {s}")


if __name__ == "__main__":
    main()
