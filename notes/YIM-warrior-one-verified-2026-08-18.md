# Warrior One verified; a noon-crossing class, and what registering Mornington did

**Date:** 18 August 2026 (afternoon)
**Live on `main` at `6e339e2`.**
**Two things still open, one of them on a clock — see the end.**

---

## The conclusion first

Warrior One was checked against the studio app end to end after three weeks of a dark feed:
**sixteen rows, fifteen exactly right.** The one wrong row exposed a parser bug that had been
latent since launch, and registering Warrior One's third studio surfaced a second latent bug
that is now live on two teachers' pages.

Both bugs have the same shape and it is worth naming: **correct until the first case that
exercises them.** Neither would ever have appeared in a test written against the data as it
stood.

---

## 1. The fix, and the bug under it

Rayne's Yin & Yoga Nidra at Mordialloc on Tuesday is **75 minutes, not 60**:
`10:45–11:45 AM` → `10:45 AM–12:00 PM`.

`start_minutes()` took the meridiem from the whole range string. It now reads the start's own
meridiem where it has one.

**Regression-checked across all 23 distinct time strings in the repo: 22 parse identically,
0 changed, and the one that previously raised `ValueError` now returns 645.**

### A refinement to how this was described

The brief said the old parser mis-sorted "silently, never crashing". Measured, it is both, and
which one depends on the string:

| String | Old parser | New parser |
|---|---|---|
| `10:45 AM–12:00 PM` | **crash** — `int('45 AM')` raises | `645` — 10:45, correct |
| `10:45–12:00 PM` | `1365` — 22:45, silently wrong | `1365` — **still wrong** |

**The fix is the parser and the data together.** A noon-crossing class must carry its own `AM`
on the start time; nothing in `10:45–12:00 PM` says the start is morning, so no parser can
rescue it. That is now in the commit message, because a future session reading only the
docstring could reasonably assume the parser alone protects them.

Verified on the story card: Rayne's Tuesday frame sorts `6:00–7:00 AM` → `10:45 AM–12:00 PM`
→ `7:30–8:30 PM`.

---

## 2. Mornington registered — and the side effect to decide on

Warrior One has three locations; Mornington was never in the registry. Its feed is `manual`
(no YiM teacher there, no widget slug captured), so nothing pulls. Mindbody activation switches
all three on from the one `site_id` 211566.

**But registering it put Mornington on Alessia's and Rayne's pages as somewhere they teach.**
Rayne's meta description now reads:

> "Rayne teaches yoga across Brighton, Mordialloc, Highett **& Mornington**."

Neither teaches there. The cause is `_handoff_suburbs()`, which matches studios by the
`warrior-one` id prefix and returns every location under that brand. Until now every Warrior
One suburb was already one where they had real classes, so the extra entries were deduplicated
away and nothing showed. Mornington is the first that isn't.

This is live on a search-facing description and in schema.org `areaServed`. It is a false
statement about a named person — the exact class of thing the coverage-honesty line on the
listing pages exists to prevent.

**The fix is small and already exists elsewhere in the file.** `render_handoff_cards()` skips a
brand when the teacher has real timed classes there; `_handoff_suburbs()` does not. Applying
the same rule removes Mornington from both pages and leaves Emma's Happy Melon handoff
untouched. **Not applied — it changes SEO output for every teacher, so it is Mark's call.**

---

## 3. `verified` stamps

All three Warrior One studios carry `"verified": "2026-08-18"`. The repo stored only the last
successful *pull* date, which every session then read as staleness — and did twice on 18 Aug,
asking Mark to re-screenshot rows he had already confirmed. Nothing renders this yet; putting
the fact in the data is the point.

---

## What changed

| File | |
|---|---|
| `data/schedule.json` | Rayne's class corrected; Mornington registered; `verified` on all three Warrior One studios |
| `build_profiles.py` | `start_minutes()` reads the start's own meridiem |
| `alessia-frisina.html`, `rayne-watkin.html` | Regenerated — and only these two |

---

## Did not arrive

**The updated roster note.** `notes/YIM-teacher-roster-2026-08-16.md` was described as attached
and replacing the version on main, but the file delivered is **byte-identical to the one already
there**, with no 18 Aug content. So these three corrections are **not in the repo**:

- Rach is **Rach**, not Rachael — the feed was wrong, same failure as Steph's spelling
- Brighton and Mordialloc are **separate catchments with independent timetables**; do not infer
  one studio's slots from another's
- Observed class counts **include substitutions**, so they overstate a teacher's regular load
  and must not be used to rank recruitment targets

The third is the one that would quietly distort a decision. Emma currently shows 14 classes, of
which **6 are subs** — she looks like the busiest teacher on the roster and is not.

---

## Open

| Item | Check |
|---|---|
| **Line-up frame still overflows.** Wed 19 Aug is 13 classes, Tue 25 Aug is 14. Both fail at the 0.62 floor, the build exits 1, and `story.yml` reads that as a thin day: **no commit, no issue, nothing published** | `build_story_cards.py --date 2026-08-19` exits 0. **~6 hours to the 7pm run at the time of writing** |
| **Mornington on two teachers' pages** | Decide whether `_handoff_suburbs()` should skip brands where the teacher has real classes |
| **Roster note corrections not in the repo** | Re-send the updated file |
| Move the full-timetable CTA to the line-up frame | Before the closer is retired, not after |
| `captions.md` per-teacher note still says "the frame **she** reshares" | Same pronoun bug fixed on the listing pages; internal copy, still wrong |
| AEDT in October moves the 09:00 UTC run to 8pm | Change to `0 8 * * *` |

---

## Unchanged

The editorial firewall. What this session did touch is the adjacent discipline: whether the
factual layer says true things. A 75-minute class shown as 60, and a teacher credited with a
suburb she does not teach in, are both failures of the same promise the schedule makes — and
the second is live right now.
