# Yoga in Melbourne — site & pipeline working session

**Date:** 17 August 2026
**Follows:** `YIM-instagram-formats-2026-08-16.md`, `YIM-teacher-roster-2026-08-16.md`,
`YIM-growth-model-2026-08-15.md`
**Status:** Repo access working. Five of the eight open items from 16 Aug are closed in code.

---

## The conclusion first

**Push access works** — the 403 that blocked every prior session is gone, and the three
existing notes are now committed to `notes/` rather than living only as conversation files.
All four queued site/pipeline jobs shipped on branch `claude/new-session-0hfaor`.

**The single most useful finding is diagnostic, not code:** the three "dark feeds" are not
three broken studios. They are one broken adapter.

---

## 1. The dark feeds are one bug, not three

| Studio | Adapter | State |
|---|---|---|
| Warrior One Brighton | `gomindbody` | dark |
| Warrior One Mordialloc | `gomindbody` | dark |
| Happy Melon Armadale | `gomindbody` | dark |
| Within South Yarra | `healcode` | healthy |
| Grass Roots St Kilda | `momence` | healthy |
| (Here) Yoga ×2, Kozen | `momence` | healthy |
| Inndriya Highett | `squarespace` | healthy |

**Every dark feed is `gomindbody`. Every `gomindbody` feed is dark. Nothing else is
affected.** That is not a coincidence at n=3 — it is the Playwright-rendered Mindbody V2
widget path failing as a unit, most likely because Mindbody changed the widget markup.

**Correction to the 16 Aug note:** it recorded 23 dark runs. `pull/_feed_state.json` says
**25** — two further failed runs since.

**What this changes.** Chasing Happy Melon or Warrior One individually will find nothing.
It also sharpens the reframing already made on 16 Aug: **Mindbody API activation is not
plumbing awaiting its turn, it is the fix.** `normalizers.mindbody_rows` (Public API v6)
is already written and waiting on `MINDBODY_API_KEY` plus per-studio activation. Switching
those three studios from `gomindbody` to `mindbody` deletes the broken path rather than
repairing it.

**I could not reproduce it.** This session's egress policy blocks the studio hosts
(403 on CONNECT to `readonly-api.momence.com` and the Mindbody hosts), so no live fetch was
possible. Instead of guessing at a fix, `pull.py` now *reports* the pattern: when every
failing feed shares one adapter and none of that adapter's feeds succeeded, the anomaly
issue says so in one line at the top.

---

## 2. What shipped

Branch `claude/new-session-0hfaor`, six commits.

| Commit | What |
|---|---|
| `f9f0875` | The three prior notes into `notes/` |
| `7b85ce2` | Opt-out list, 14-day pull window, empty-timetable flag, adapter diagnosis |
| `adab7b3` | Every class row books |
| `99aca94` | Story card generation + nightly workflow |
| `9081531` | Homepage router |
| `42e54c7` | Pipeline README brought back in line with the code |

### 2a. The opt-out list — built before the first no

Top-level `suppressed` in `schedule.json`. A declining teacher is dropped **before** alias
matching, so no future pull can re-add her and nothing downstream can leak her by
forgetting to check.

```json
"suppressed": [{"name": "Jane Smith", "note": "declined 12 Sep", "date": "2026-09-12"}]
```

A guard refuses to merge if a name is both registered and suppressed — that combination
would silently empty a live profile.

### 2b. Pull window 7 → 14 days

Emma Strembickyj's only two classes were 24 and 26 Aug — outside a 7-day window, so her
page published an empty timetable that read as "no classes" rather than "beyond our
window". merge dedups on (studio, day, start, class), so weekly classes seen twice in a
fortnight still collapse to one row.

Added a matching anomaly: **registered teachers whose timetable is empty at every studio.**
The existing check only caught teachers who *lost* classes, so anyone who never had any
was invisible.

### 2c. Every class row books

The product gap named in §11a.3, and it was worse than "most rows": **no** class row had a
booking link. The only outbound link on a profile was the studio-level `Book ↗`.

| Page | Outbound links before | After |
|---|---|---|
| Alessia Frisina | 4 | **17** |
| Janita Doelken | 2 | **8** |
| Rayne Watkin | 3 | **10** |

Class identity comes from GA4 `link_text` (`Wed 5:00–6:00 PM Slow Flow Yoga`) rather than
UTM parameters appended to studio booking URLs we do not control and could break. An
optional per-class `url` now flows normalizer → merge → template, so true per-session deep
links drop in later with no template change; no normalizer sets it yet.

### 2d. Story cards

`build_story_cards.py` renders `schedule.json` into 1080×1920 frames. Frames: opener,
line-up, one per teacher. **No closer** — on 15 Aug it took 30 views, fewest of any frame,
because nobody could be tagged on it.

`captions.md` ships beside the images with the mention list and link sticker for every
frame. The 15 Aug story priced an untagged opener at roughly 90 lost views; this exists so
that is never left to memory.

- Thin-day guard at 3 classes, and it **exits rather than warns** — silence is the correct
  output on a thin day.
- `--mode today` hides anything before 14:00 and warns below five teachers.
- Cards auto-fit: metrics scale until the frame fits, and a card that cannot fit even at
  the floor **fails the build** rather than quietly cutting a class off the bottom. Tested
  at 12 classes / 8 teachers — fits at 0.66 and stays legible. Fixed breakpoints would have
  started clipping on the day the roster outgrew them.

**`.github/workflows/story.yml` runs it nightly at 09:00 UTC (7pm AEST)**, commits the PNGs,
and opens an issue holding the captions. That is the part that matters: the ritual is now
reachable from a phone with no terminal.

### 2e. Homepage router

Named teachers are the first row after the nav — a visitor arriving from a reel is looking
for a person, and each name is one tap from her cross-studio timetable.

Placed *below* the hero it measured at **y=1075px on a 390×844 phone** — past the fold,
which defeats the purpose. It sits above the hero instead: y=215px mobile, y=148px desktop.

### 2f. Two bugs found while testing

- **Name matching folded leading/trailing whitespace but not internal.** `"Janita  Doelken"`
  was reported as an unmatched stranger — which looks like it needs a new alias when it does
  not. Given the roster note calls aliasing "the main hidden cost of onboarding", this would
  have generated phantom alias work at scale. Both alias lookup and the opt-out list now
  fold through one function.
- **`esc()` is `quote=False`.** Fine for text, not for an `href` — and per-class URLs arrive
  from studio feeds. Added `esc_attr()` for quoted attributes.

---

## 3. Corrections to earlier notes

| Earlier note said | Actually |
|---|---|
| Feeds dark 23 runs | **25 runs** |
| Normalizers "not built yet" (`pull/README.md`) | All five exist and are written. README was stale; now fixed |
| "Most schedule rows have no booking link" | **None** did |
| Three separate dark studios | One dead adapter — see §1 |

I also flagged the homepage `#conversations` / `#journal` anchors as possibly broken early
in the session. **They are not** — the IDs sit on inner `<div>`s, which anchors resolve to
perfectly well. No change made.

---

## 4. What has *not* changed

- **The editorial firewall is absolute.** Nothing here touches it. The opt-out list
  strengthens it: it makes a teacher's no structurally durable rather than dependent on
  someone remembering. Aggregated schedule data remains factual/public; teacher pages remain
  editorial and require approval.
- Profiles and podcasts continue. Aggregated cross-studio schedules remain the moat — every
  change above deepens it rather than trading it for reach.
- Rung 0 still involves asking. Nothing was automated that removes the human contact; the
  ask *is* the mechanism.

---

## 5. Open items

Carried forward, with what changed:

1. ~~Repo push blocked (403)~~ — **closed.**
2. ~~Opt-out list in `merge.py`~~ — **closed.**
3. ~~Automate story-card generation~~ — **closed**, including the nightly workflow.
4. ~~Schedule rows not clickable to booking~~ — **closed.**
5. ~~Homepage is not a router~~ — **closed.**
6. **Fix the gomindbody adapter** — now correctly scoped as *one* job, not three. Best path
   is Mindbody API activation, which deletes the adapter rather than repairing it.
7. **Mindbody API activation** — unchanged in priority, sharper in justification (§1).
8. **Post the Sunday Line-Up reel** — still outstanding, still a Mark job.
9. **Read the 15 Aug story's final numbers** and log them in the rotation ledger.
10. **Check GA `instagram / story`** — pages/session for those 7 clicks, and whether any
    reached a studio booking link. Worth re-checking *after* this ships: until today there
    were almost no class-level outbound links to click.
11. **Aliases for `Steph Philip`/`Phillip` and `Rach`/`Rachael Mellican`** — not yet
    actionable; neither is a registered teacher. Needed at onboarding, not before.
12. **Generate the homepage teacher lists from `schedule.json`.** Both the router row and the
    Teachers grid are hardcoded. Fine at 5, a maintenance trap at 15 — and 15 is the stated
    Tier 1 target.

### Things to check, with the metric and the date

- **Does the booking-link change move outbound clicks?** GA `click` event count on teacher
  pages, week of 24 Aug vs week of 17 Aug. The link count roughly quadrupled; if clicks do
  not move at all, the constraint is traffic, not affordance.
- **Does the router move pages/session?** Currently 1.42 on spike traffic, 1.9 baseline.
  Check after the next reel. Above ~2.2 means arrivals are being routed rather than stopping.
- **Does the nightly story workflow actually fire at 7pm?** Check the first run. Melbourne
  moves to AEDT in October, when 09:00 UTC becomes 8pm — the cron needs changing then, and
  the fixed hour is functional, not ceremonial.

---

## Assumptions flagged

- **The gomindbody diagnosis is inference from the failure pattern, not a reproduced bug.**
  Egress policy blocked live fetches this session. The correlation is total (3 of 3 dark,
  0 of 6 others) which makes coincidence very unlikely, but the actual breakage — markup
  change, bot challenge, something else — is unconfirmed.
- **The GA4 `link_text` attribution approach is untested in YiM's property.** Enhanced
  measurement records it; that it will be usefully queryable per class is expected, not
  verified.
- **Instagram's story safe zones are taken as ~220px top / ~250px bottom.** Standard figures,
  not measured against the current app version. The cards clear them with margin.
- **The 12-class auto-fit test used a synthetic roster** built from Tier 1 names in the
  roster note. It proves the layout, not the data.
- Story-card posting times (7pm / 12pm) are inherited from the 16 Aug note and remain
  reasoning from decision windows, not from YiM's own measurement.
- **Profile pages were verified byte-identical** after the pipeline changes and before the
  booking-link change, so the schedule/merge work provably changed no output. The
  booking-link diff was reviewed by rendering, not by a golden-file test — there is no test
  suite in this repo.
