#!/usr/bin/env python3
"""Crop a teacher's supplied photograph into the three sizes YiM needs.

    python3 crop-portrait.py <photo> <slug> [face_x_pct] [face_y_pct]

Anchors on her face, not the geometric centre. Shelley's original was 7903x5271
with her left of centre and high in frame — a naive centre crop removed her head
entirely, which is exactly the error this exists to prevent. Pass the face position
as percentages if the defaults miss.

Writes:
  <slug>-portrait.jpg   880x1100   -> base64 into templates/<slug>.template.html
  img/<slug>.jpg        1200x630   -> Open Graph; seo_head() already expects it,
                                      so without it every link preview 404s
  <slug>-square.jpg     900x900    -> held for story cards
"""
import sys, os
from PIL import Image

src, slug = sys.argv[1], sys.argv[2]
fxp = float(sys.argv[3]) if len(sys.argv) > 3 else 50.0
fyp = float(sys.argv[4]) if len(sys.argv) > 4 else 25.0

im = Image.open(src).convert("RGB")
W, H = im.size
fx, fy = int(W * fxp / 100), int(H * fyp / 100)

def crop(ar, anchor):
    if W / H > ar: h = H; w = int(h * ar)
    else:          w = W; h = int(w / ar)
    x = min(max(fx - w // 2, 0), W - w)
    y = min(max(int(fy - h * anchor), 0), H - h)
    return im.crop((x, y, x + w, y + h))

os.makedirs("img", exist_ok=True)
for name, ar, anchor, size, q in [
    (f"{slug}-portrait.jpg", 0.8,       0.28, (880, 1100), 84),
    (f"img/{slug}.jpg",      1200/630,  0.34, (1200, 630), 84),
    (f"{slug}-square.jpg",   1.0,       0.30, (900, 900),  86),
]:
    crop(ar, anchor).resize(size, Image.LANCZOS).save(name, "JPEG", quality=q, optimize=True)
    print(f"  {name:34} {size[0]}x{size[1]}  {os.path.getsize(name)//1024} KB")

print("\nNow embed the portrait:")
print(f"  python3 -c \"import base64;print(base64.b64encode(open('{slug}-portrait.jpg','rb').read()).decode())\"")
print(f"  paste into templates/{slug}.template.html, replacing PASTE_880x1100_JPEG_BASE64_HERE")
