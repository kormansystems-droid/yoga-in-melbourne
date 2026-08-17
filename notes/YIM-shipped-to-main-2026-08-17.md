# Yoga in Melbourne — what shipped, 17 August 2026

**Status:** Live on `main` at `ed8d9a5`. Previously `4d27f74`.
**Supersedes on one point:** `YIM-site-and-pipeline-work-2026-08-17.md` was written while the
work sat on a feature branch and describes it that way. It is merged now.

---

## In one paragraph

Repo push access works, closing the item that had blocked every prior session. Four queued
jobs shipped — pipeline repairs, booking links on class rows, story-card generation, the
homepage router — plus the homepage hero switch to Zoe Kanat. All of it is merged to `main`
and live. The most useful finding was not code: the three dark studio feeds are one broken
adapter, not three broken studios. **No feed was actually repaired** — see Limits.

---

## 1. The finding: three dark feeds are one broken adapter

| Studio | Adapter | State |
|---|---|---|
| Warrior One Brighton | `gomindbody` | **dark** |
| Warrior One Mordialloc | `gomindbody` | **dark** |
| Happy Melon Armadale | `gomindbody` | **dark** |
| Within South Yarra | `healcode` | healthy |
| Grass Roots St Kilda | `momence` | healthy |
| (Here) Yoga ×2, Kozen | `momence` | healthy |
| Inndriya Highett | `squarespace` | healthy |

**3 of 3 dark on one adapter. 0 of 6 dark on every other.**

This is the Playwright-rendered Mindbody V2 widget path failing as a unit, not three studios
independently breaking on the same day.

Two consequences:

- **Chasing the studios individually will find nothing.** There is one job here, not three.
- It sharpens the 16 Aug reframing: **Mindbody API activation is not plumbing awaiting its
  turn, it is the fix.** `normalizers.mindbody_rows` is already written and waiting on the key.
  Switching those three studios deletes the broken adapter rather than repairing it.

The 16 Aug note recorded 23 dark runs. `pull/_feed_state.json` says **25**.

---

## 2. What shipped

| SHA | Change |
|---|---|
| `f9f0875` | Push access verified; three strategy notes committed to `notes/` |
| `7b85ce2` | Teacher opt-out list, 14-day pull window, empty-timetable flag, adapter diagnosis |
| `adab7b3` | Every class row books |
| `99aca94` | Story cards + nightly workflow |
| `9081531` | Homepage router |
| `42e54c7` | Pipeline README brought back in line with the code |
| `4cb87d0` | Session note |
| `60322db` + 1 | Removed committed `__pycache__`, added `.gitignore` |
| `ed8d9a5` | **Zoe Kanat in the homepage hero** |

### Teacher opt-out — built before the first no

A `suppressed` list in `schedule.json` drops a declining teacher **before** alias matching, so
no future pull can re-add her and nothing downstream can leak her by forgetting to check. A
guard refuses to merge if a name is both registered and suppressed — that combination would
silently empty a live profile.

### Pull window 7 → 14 days

Emma Strembickyj's only two classes were 24 and 26 August, outside a weekly window, so her page
published an empty timetable that read as "no classes" rather than "beyond our window". A new
anomaly flags registered teachers empty at *every* studio; the existing check only caught
teachers who *lost* classes, so anyone who never had any was invisible.

### Every class row books

The gap named in §11a.3, and worse than "most rows" — **none** had a link. The only outbound
link on a profile was the studio-level `Book ↗`.

| Teacher | Before | After | Class rows linked |
|---|---:|---:|---:|
| Alessia Frisina | 4 | **17** | 13 |
| Rayne Watkin | 3 | **10** | 7 |
| Janita Doelken | 2 | **8** | 6 |

Class identity comes from GA4 `link_text` — the row reads "Wed 5:00–6:00 PM Slow Flow Yoga" —
rather than UTM parameters appended to booking URLs we neither control nor can safely modify.
An optional per-class `url` flows normalizer → merge → template, ready for real deep links.

### Story cards

`build_story_cards.py` renders `schedule.json` into 1080×1920 frames: opener, line-up, one per
teacher. **No closer** — on 15 August it took 30 views, the fewest of any frame, because nobody
could be tagged on it.

`captions.md` ships beside the images with the mention list and link sticker for every frame.
The 15 August story priced an untagged opener at roughly 90 lost views.

- Thin-day guard **exits rather than warns** — silence is the correct output on a thin day.
- Cards auto-fit; one that cannot fit even at the floor **fails the build** rather than quietly
  cutting a class off the bottom. Tested at 12 classes / 8 teachers: fits at 0.66, still legible.
- **The nightly workflow is now on `main`, so its `schedule` trigger can actually fire.** GitHub
  only runs scheduled workflows from the default branch — on a feature branch it was inert.

### Homepage router

The homepage took 61% of views on 10–15 August at 1.42 pages/session against a 1.9 baseline.
Named teachers are now the first row after the nav. Below the hero it measured y=1075px on a
390×844 phone — past the fold; moved above, y=215px mobile and y=148px desktop.

### Homepage hero → Zoe Kanat

Headline, standfirst and CTA now point at `zoe-kanat.html`. The `hero-player` is commented out
until her episode is published — verified as **0 `<audio>` elements and 0 `.hero-player` nodes**
in the rendered DOM, so it is genuinely inert rather than a hidden player still fetching an mp3.
Masthead, tagline, router and the Apple Podcasts / Spotify buttons untouched.

---

## 3. Corrections

| Earlier note said | The repo says |
|---|---|
| Feeds dark 23 runs | **25** runs |
| Normalizers "not built yet" | All five exist; the README was stale |
| "Most schedule rows have no booking link" | **None** did |
| Three separate dark studios | One dead adapter |

Two latent bugs found while testing:

- **Name matching folded outer whitespace but not internal.** `"Janita  Doelken"` was reported
  as an unmatched stranger — which looks like it needs a new alias when it does not. The roster
  note calls aliasing "the main hidden cost of onboarding"; this would have manufactured
  phantom alias work at exactly the scale where it gets expensive.
- **`esc()` is `quote=False`.** Fine for text, not for an `href` — and per-class URLs arrive
  from studio feeds. Added `esc_attr()`.

And one correction to myself: I flagged the homepage `#conversations` / `#journal` anchors as
possibly broken. **They are not** — the IDs sit on inner `<div>`s, which anchors resolve to
fine. No change made.

---

## 4. Limits — what was not done

- **No feed was repaired.** Session egress policy blocked the studio hosts (403 on CONNECT to
  `readonly-api.momence.com` and the Mindbody hosts), so the break could not be reproduced.
  Rather than guess at a fix, the next real run now reports the pattern in one line.
- **The adapter diagnosis is inference, not a reproduced bug.** The correlation is total, which
  makes coincidence very unlikely, but the actual breakage is unconfirmed.
- **The branch `claude/new-session-0hfaor` was not deleted.** `git push --delete` was refused by
  the session's permission classifier, and the GitHub MCP server exposes no delete-branch tool.
  It is fully merged, so deleting it loses nothing — one click in the GitHub UI, or a Bash
  permission rule.
- **There is no test suite in this repo.** Pipeline changes were verified by rebuilding profile
  pages byte-identical; the rest by rendering in a real browser and measuring.
- **GA4 `link_text` attribution is expected, not verified** in your property.
- **The 12-class stress test used a synthetic roster** from Tier 1 names. It proves the layout,
  not the data.

---

## 5. Open, with the check that settles it

| Item | Check |
|---|---|
| **Fix the gomindbody adapter** — one job, not three. Best path is Mindbody API activation | Any Warrior One or Happy Melon class appears on a profile again |
| **Do booking links move outbound clicks?** Count roughly tripled | GA `click` events on teacher pages, week of 24 Aug vs 17 Aug |
| **Does the router move pages/session?** 1.42 on spike traffic, 1.9 baseline | After the next reel. Above ~2.2 means arrivals are being routed |
| **Does the nightly card workflow fire at 7pm?** | The first scheduled run. Melbourne moves to AEDT in October — 09:00 UTC becomes 8pm and the cron needs changing |
| **Generate homepage teacher lists from `schedule.json`** — router row and Teachers grid are both hardcoded | Do it before onboarding the Inner South cohort, not after |
| **Aliases for Steph Philip/Phillip, Rach/Rachael Mellican** | Needed at onboarding; neither is registered yet |
| **Add Zoe's mp3 to the hero** when her episode publishes | Uncomment the marked block, set `src` and duration |
| **Still yours:** post the Sunday Line-Up reel; log the 15 Aug story numbers in the rotation ledger; check GA `instagram / story` | — |

---

## 6. What none of this touched

**The editorial firewall is absolute**, and nothing here bends it. The opt-out list strengthens
it: a teacher's no becomes structurally durable rather than dependent on someone remembering.
Aggregated schedule data remains factual and public; teacher pages remain editorial and require
approval.

Profiles and podcasts continue. Aggregated cross-studio schedules remain the moat — every change
above deepens it rather than trading it for reach. Rung 0 still involves asking; nothing was
automated that removes the human contact, because the ask is the mechanism.
