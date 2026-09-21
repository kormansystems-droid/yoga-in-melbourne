# The Ken Burns zoom was undoing the safe-zone fix

**9 September 2026.** Found while building Rayne's podcast reel. Fixed in
`build_podcast_reel.py`. Still present in `build_solo_reel.py`.

---

## Conclusion

**Laying type to Instagram's safe zones is not enough, because the reel builder
zooms the frame after the type is rendered.** A centred zoom moves everything
away from the middle, so type placed exactly at the safe margin drifts into the
covered area before the frame ends. The margins have to be computed for the zoom,
not for the still.

This is a second, separate bug sitting underneath yesterday's. Yesterday's was
that the margins were far too small. This one is that even correct margins fail
once the frame moves.

---

## How it was found, and why it nearly was not

Yesterday's fix moved the type to the verified safe zone: 150px top, 420px
bottom, 100px right. I set 206 / 452 / 104 and **the rendered PNG frames measured
clean**.

Then I pulled stills from the finished MP4 and **the last word of two quotations
was sitting on the engagement buttons.**

The PNGs are the input to the zoom. The MP4 is the output. Checking the input and
declaring the output correct is the same shape of error as reading a success
message instead of the artefact, and it would have shipped.

## The arithmetic

`build_reel_video.py` drifts each still from zoom 1.00 to **1.13** across the
segment, 1.06 for the opener and the closer. The zoom is centred on 540, 960. For
a point to still clear its zone at zoom Z:

| Edge | Constraint | At Z=1.13 |
|---|---|---|
| Right | x ≤ 540 + 440/Z | 151px margin |
| Bottom | y ≤ 960 + 540/Z | 482px margin |
| Top | y ≥ 960 − 810/Z | 243px margin |

Rounded up for headroom, since the covered area is not identical on every
handset:

**top 250, bottom 500, right 160, left 112.**

**Left is padded too**, which I did not expect. The same zoom pushes left-hand
type toward the edge, and at 92px it finished 34px off the frame edge, which
reads as a crop rather than a margin.

| | Before yesterday | Yesterday's fix | Today |
|---|---|---|---|
| Top | 104 | 206 | **250** |
| Bottom | 132 | 452 | **500** |
| Right | 92 | 104 | **160** |
| Left | 92 | 92 | **112** |

The scrim gradient moved with the type. A scrim tuned to type at 132px throws its
weight under the caption and leaves the quotation on bare photograph.

## What this costs

The type block loses roughly 350px of height and 130px of width. In practice the
bottom 420px was never visible anyway, so the real cost is about 80px at the
bottom, 100px at the top and 60px at the right. Quotations wrap one line more
often. That is the correct trade: a line that wraps is readable, a line under the
caption is not.

---

## State of the three builders

| Builder | Safe zones | Zoom-aware | Notes |
|---|---|---|---|
| `build_video_overlay.py` | Yes, 8 Sep | **Not applicable** | Overlays sit on live footage, no zoom is applied |
| `build_podcast_reel.py` | **Yes, today** | **Yes, today** | Verified against MP4 stills at maximum zoom |
| `build_solo_reel.py` | **No** | **No** | Foot at 132px, kicker at 104px |

**`build_solo_reel.py` is the one still broken.** Emma's podcast reel is built and
**unposted**, so unlike Emma's profile reel and Shelley's podcast reel it can
still be rebuilt. That is the argument for doing it now rather than at the next
teacher.

---

## Rayne's podcast reel

Built and delivered: `rayne-podcast-reel.mp4`, 26.6s, silent, four frames.
Three quotations then a closer naming Yoga in Melbourne, Apple Podcasts and
Spotify. Full brief in `rayne-podcast-brief.md`.

Two things in it worth recording here because they will recur.

**Her photograph set cannot support this format.** With the type across the lower
two thirds, the subject has to sit high in the frame. The handstand and the floor
twist both fill 1080x1920 at their exact natural scale, so there is **no crop room
at all** and anchoring is inert. Neither can be lifted by any amount. Only the
portrait and one still from her own video put her high enough. Worth checking
this before promising a teacher a card reel: a photograph that works for a
profile page may be unusable for a format with type at the bottom.

**Holds ran 7.0s rather than the format's 6.5s.** Her quotations are 22 to 28
words against the format's designed 18, because the sentences that carry her
story are long ones. The format assumes 18 spoken words per 6.5s frame; the fix
is to lengthen the hold, not to cut the sentence.

---

## Two things I could not verify, flagged rather than assumed

1. **Whether Episode 8 has reached Apple and Spotify.** Web fetching was blocked
   in this session and Chrome was not connected. The show is on both platforms
   and those links are live on the site; what is unconfirmed is episode-level
   propagation. The episode went live yesterday at 13:40 and platforms normally
   pull within hours, so it almost certainly has. **The closer card names all
   three platforms, so this is a claim on a public asset and wants a ten-second
   check before posting.**
2. **Whether the Yin teacher training comes up in the audio.** It decides whether
   @sarahhammondyoga or @_inndriya takes the fourth collaborator slot. I lean
   toward Inndriya, because the profile post already tags Warrior One and Sarah
   Hammond, and Inndriya carries a third of Rayne's teaching week and would
   otherwise never be tagged. Two studios who are both future subscription
   customers should not be sorted by which one filled a slot first.

## What has not changed

Every quotation is verbatim from her approved profile, trimmed only at the ends
of contiguous sentences. Nothing is stitched from separate passages. The reel
still says nothing about the podcast until frame four, because the 19 August
measurement holds: publication pieces converted at **2.93%** follows per eligible
viewer against **0.30%** for single-episode promos, a **9.6x** gap with Fisher
two-tailed p = 8.6e-6.

## Open questions

| Question | How to check | When |
|---|---|---|
| Does a reel whose furniture is actually visible convert better? | Profile visits per viewer, this reel against Shelley's podcast reel | 72h after posting |
| Does the longer 7.0s hold hurt completion? | Instagram's average watch time against Shelley's 6.5s reel | 72h |

## Still outstanding

- Zoe router change: four files delivered, **not committed**, Chrome was down
- Four notes now uncommitted: search baseline, retreat brokerage, Instagram
  handles, router roster, and this one
- `build_solo_reel.py` safe zones and zoom margins: **now worth doing**, because
  Emma's podcast reel is still unposted
- Emma's studio handle, so her caption stops shipping with a blank
- Rayne's high-resolution selfie, which would take frame two from a 2.57x upscale
  to something native
