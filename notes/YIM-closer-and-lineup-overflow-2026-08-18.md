# The closer ships; the line-up frame breaks

**Date:** 18 August 2026 (morning)
**Live on `main` at `e971789`.**
**Blocker: tonight's 7pm story will not publish unless the line-up frame is fixed first.**

---

## The conclusion first

Two changes shipped as briefed: the closer is now a generated frame, and the growth-model
note's §12 ledger carries follower and audience-type columns.

But the overnight pull grew the roster faster than the format can render it, and that
produced a real break. **The line-up frame cannot fit Wednesday's 13 classes.** It shrinks to
the floor and still overflows, so the build fails rather than shipping a card with a class cut
off the bottom. `story.yml` reads a non-zero exit as "thin day", commits nothing and files no
issue — so tonight's story would fail **silently**.

This is not caused by the closer. Only frame 2 overflows; the closer sits at full scale.

---

## What the 05:00 pull proved

Three fixes from the last two days were validated overnight without anyone testing them
(`3b9d3a8`):

| Fix | Prediction | Result |
|---|---|---|
| Pull window 7 → 14 days | Emma's empty timetable was a window artefact, not "no classes" | **0 → 14 classes** |
| `"Ryan ."` alias (Good Vibes publishes first names only) | Would match despite the literal full stop | Matched; **7 → 10** live classes |
| Two-L `"Steph Phillip"` alias kept alongside her real spelling | Dropping it would empty her Malvern schedule | Matched; 11 classes intact |

Dark feeds unchanged and still exactly the three `gomindbody` ones — now **26 runs** since
27 July.

---

## The blocker, precisely

Wednesday 19 Aug is Alessia 6 + Emma 3 + Ryan 4 = **13 classes, 3 teachers, 6 frames**.

Measured per frame: every frame renders at `--k` 1.0 except the line-up, which reaches the
0.62 floor and still overflows. The auto-fit guard then fails the build deliberately — that
guard is doing its job, and the job is refusing to ship a truncated timetable.

```
⚠ lineup still overflow at the smallest size. The PNGs are written but a class is
  cut off the bottom — split the line-up across two frames rather than posting these.
exit code 1  →  story.yml sets built=0  →  no commit, no issue
```

**This is the wrap problem flagged on the opener two briefs ago, arriving on the line-up frame
first and much faster than expected** — because the roster grew by 14 classes in a single pull
rather than one teacher at a time.

### Two options, and a recommendation

1. **Split the line-up chronologically across two frames** when it will not fit — morning /
   afternoon, or simply first half and second half. Every class stays visible.
2. **Drop the line-up frame above a class threshold** and let the per-teacher frames carry the
   day, moving the "full timetable" call to action as the closer's comment already anticipates.

**Recommend (1).** The line-up is the only frame that shows the whole cross-studio day, which
is the moat rendered as content. Losing it at exactly the roster size where it finally looks
impressive is the wrong trade.

**Time:** 8.8 hours to the 09:00 UTC run at the time of writing. *(An earlier verbal estimate
of ~19 hours was wrong — the run is tonight, not tomorrow night.)*

---

## What shipped

### The closer, generated

A final frame plus a `.closer` CSS block. Reads "Tomorrow *on the mat* with" — or **"Today on
the mat with"** in `--mode today` — then every teacher named, then the full-timetable route.
It gets a `captions.md` row with the complete mention list like every other frame.

It is the weakest frame every time it runs — 30 views on 15 Aug, 30 on 17 Aug, 16 on 18 Aug —
and it stays, because at this roster size **volume is the job, not views**: a four-frame story
rolls past before anyone settles into it. Generating it removes the only real argument against
keeping it, since a frame hand-tagged at 7pm nightly is exactly the friction that kills a daily
ritual.

The code comment records the retirement rule: **retire on roster size, not performance** —
around six teachers on a normal day — and **move the "full timetable" call to action onto the
line-up frame first**, because the closer is currently the only frame carrying it.

The module docstring claimed there is no closer. Corrected, and it now records the 18 Aug
measurement: **opener 36 views against Steph Philip's 183**, because her audience entered at
her frame and never saw the rest of the sequence.

### The rotation ledger

§12 gains **IG followers** and **audience type** columns and three teachers, plus the finding
that group reels beat sequential solos by about **70% per collaborator** (5-way: 3,200 views
from five; solo: 383 from one — 8.4×, not 5×). Rule that follows: bank teachers, fire them as a
five. Verified byte-identical outside the §12 ledger block.

---

## Correction to the brief's expectations

The brief expected Wednesday at **10 classes, 2 teachers, 5 frames**. It reports **13 / 3 / 6**.
The brief was written before the 05:00 pull landed; the counts are right and the expectation
was stale. Frame 5 is Ryan Mannix, not the closer — the closer is frame 6.

`build_story_cards.py` was described as attached but did not arrive. It was implemented from
the brief's specification rather than copied.

---

## Open

| Item | Check |
|---|---|
| **Fix the line-up overflow before 09:00 UTC tonight** | `python3 build_story_cards.py --date 2026-08-19` exits 0 |
| Move the full-timetable CTA to the line-up frame | Do it before the closer is retired, not after |
| Retire the closer at ~6 teachers on a normal day | Roster size, not view count |
| The opener's fact line also wraps at this density | Same underlying pressure; decide whether `--k` should scale `.count` |
| `captions.md` per-teacher note still reads "the frame **she** reshares" | Internal copy Mark reads, not teacher-facing, but it is the same pronoun bug fixed on the listing pages yesterday. Left unchanged — out of the brief's scope |
| AEDT in October moves the 09:00 UTC run to 8pm | Change to `0 8 * * *` |

---

## Unchanged

The editorial firewall. Nothing here touches it. The closer names teachers who are listed with
their consent and links to the public timetable; the failure mode being guarded against — a
card that silently drops a class — is a data-honesty protection, which is the same instinct
applied to the schedule rather than to prose.
