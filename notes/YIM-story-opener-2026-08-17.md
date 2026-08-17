# Story opener: weekday as headline, date as fact

**Date:** 17 August 2026 (evening)
**Live on `main` at `0a05200`.** Small change — one frame, one function, no CSS.

---

## What changed

Frame 1 of the daily story only. The headline was the date over two lines; it is now the
weekday plus the word Yoga on one line, and the date has moved into the fact row.

| | Before | After |
|---|---|---|
| `.date` | `Tuesday`<br>`18 August` *(two lines)* | `Tuesday **Yoga**` *(one line, Yoga italic in henna)* |
| `.count` | `Tomorrow · 7 classes · 3 teachers · 3 studios · 4 suburbs` | `18 August · 7 classes · 3 teachers · 3 studios · 4 suburbs` |

**Why.** The headline should name the thing being announced, and that is "Tuesday Yoga" — a
weekly occasion — not a calendar entry. The date is a fact *about* it, so it belongs with the
other facts, where it reads as one scannable line rather than competing with the headline for
the eye.

**The "Tomorrow" lead is gone in tomorrow mode.** The kicker directly above already reads
"YOGA TOMORROW", so the word under the headline said nothing twice. Today mode keeps a
lowercase "still to come" after the date, because on that frame it is doing real work: it is
the whole reason the list is shorter than the day's full timetable.

Frame 2, the per-teacher frames and `CARD_CSS` are untouched. The change uses the existing
`.date em` rule for the henna italic; no new styling.

---

## Verified across all three modes

| Run | `.date` | `.count` |
|---|---|---|
| `--date 2026-08-18` | `Tuesday <em>Yoga</em>` | `18 August · 7 classes · 3 teachers · 3 studios · 4 suburbs` |
| `--mode today --date 2026-08-20` | `Thursday <em>Yoga</em>` | `20 August · still to come · 4 classes · 2 teachers · 2 studios · 2 suburbs` |
| `--date 2026-08-19 --force` | `Wednesday <em>Yoga</em>` | `19 August · 6 classes · 1 teacher · 2 studios · 2 suburbs` |

Frame counts unchanged: 5 / 4 / 3 respectively. `story/` not committed.

Two behaviours confirmed incidentally rather than assumed:

- The forced thin day renders **"1 teacher"**, not "1 teachers" — the pluraliser handles the
  singular. Worth knowing, because thin days are exactly when a card is most likely to be
  looked at closely and least likely to have been checked.
- Today mode still fires the five-teacher warning on 20 Aug. That guard survives the edit.

---

## One thing left as a decision, not a bug

At 7 classes and 4 suburbs the fact line **wraps to two lines**, leaving "suburbs" alone on the
second. It is legible and well inside the story safe zone, so it ships as is — but that line
only grows with the roster, and this format is explicitly designed to get denser.

Two fixes when it stops looking right, neither urgent:

1. Drop the suburb count. It is the least informative of the four and the first thing a reader
   skips.
2. Let `--k` scale `.count` as it already scales the row metrics, so the fact line shrinks with
   everything else.

**Check:** look at the opener on the first day the roster passes about ten classes.

---

## Unchanged

Nothing about what the frame is *for*. It still names every teacher, because that is what makes
it taggable, and the untagged-opener lesson from 15 Aug — the best card taking the fewest views
at roughly 90 lost — is still the reason `captions.md` exists.
