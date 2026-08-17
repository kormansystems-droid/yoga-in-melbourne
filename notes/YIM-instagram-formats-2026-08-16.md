# Yoga in Melbourne — Instagram Formats & Onboarding

**Date:** 16 August 2026
**Companion to:** `YIM-growth-model-2026-08-15.md` (strategy, evidence, the loop, the rotation ledger)
**Status:** First real performance data on the utility format. Format system settled.

---

## 1. First Sunday Line-Up — measured result

Posted as a six-frame story ~7pm Sat 15 Aug (the reel version was **not** posted — that half of
the plan is still outstanding). Frames: opener with three portraits → full line-up → Alessia →
Rayne → Janita → dark closer. Each frame carried a link sticker; the three teacher frames each
carried a mention.

| Frame | Mentioned? | Views |
|---|---|---|
| Opener (3 portraits) | no | 37 |
| Line-up | no | 41 |
| Alessia | yes | 134 |
| Rayne | yes | 107 |
| Janita | yes | 128 |
| Closer | no | 30 |

**Mentioned frames averaged 123. Un-mentioned averaged 36. A 3.4x multiple.**

This cannot be ordinary story decay — views should fall monotonically from frame one, yet the
middle frames beat the opener threefold. The only mechanism that produces that shape is
reshares pulling the resharers' audiences back into the story. *(Inference from the pattern,
not a measured attribution.)*

**Reshares:** all three mentioned teachers reshared. **Grass Roots (a studio) reshared
unsolicited** — the single most significant signal of the night. Studio demand, day one,
unasked, before any commercial conversation.

**Link clicks: 7.** That is **3.5–5.2%** of unique reach — the healthy end of the normal band
for story link stickers. Nothing to fix in the copy or the card; the constraint is audience
size, not conversion.

**Quality note:** compare with the 11 Aug reel spike — ~300 sessions, 61% stuck on the
homepage, 1.42 pages/session, 78 seconds. Those were browsers. These seven opened a named
teacher's schedule at 7pm on a Saturday. Deep-linked, decision-stage traffic.

### Lessons taken

1. **Tag every frame that can be tagged.** The opener is the best card and got the least reach
   (37) purely because nobody was mentioned on it. Prior advice to skip it "to save fiddle" was
   wrong — the data prices that omission at roughly 90 views.
2. **Story likes ≈ 0 is normal**, not failure. Stories are measured in taps, exits, link taps
   and reshares — not hearts. Judging a story by reel metrics is a category error.
3. **Read final numbers after expiry, and log them.** Comparing next week's complete figure
   against tonight's partial would repeat the Janita page-views misread in a new dress.

### Scaling arithmetic (same click rate)

| Teachers | Est. frame views | Est. clicks |
|---|---|---|
| 3 (15 Aug) | 369 | 7 |
| 5 | ~615 | ~12 |
| 8 | ~984 | ~19 |
| 12 | ~1,476 | ~28 |

Nothing about the format needs changing. It needs **more faces, the opener tagged, and the reel
actually posted.**

---

## 2. The format system

Three formats, three jobs. Do not judge one by another's metrics.

| Format | Job | Reaches | Links? | Cadence |
|---|---|---|---|---|
| **Collab reel** | Acquisition — new audiences | non-followers | no (bio only) | per season / weekly tentpole |
| **Solo reel** | Relationship + deep traffic | non-followers | no | ~2/week within a season |
| **Story** | Utility, clicks, habit | followers + reshare audiences | **yes, one per frame** | daily |

**Reels carry no link stickers** — that's why the story exists. Reel for reach, story for
clicks, same cards. Posting only one of them leaves half the value on the table.

**Carousels:** save for editorial, not timetables. Format-to-content fit — a timetable dated
16 August is clutter on a permanent grid by Monday; perishable content belongs in an ephemeral
format. A carousel's real advantage is Instagram Collab placing it permanently on up to five
teachers' grids, which suits evergreen editorial.

**Collab is feed-only.** Instagram Collab (dual-author, up to 5 collaborators) works on feed
posts and reels, **not stories**. The story equivalent is the mention → "Add to your story"
reshare loop — which is why every taggable frame must be tagged.

**Music:** stories have no continuous track (each frame restarts). Score the reel; leave the
story silent.

---

## 3. The daily rhythm — Yoga Today / Yoga Tomorrow

Two named rituals, one publishing action each:

- **Yoga Tomorrow — ~7pm.** The full next-day schedule. Planning view. Catches the
  alarm-setting decision, and lands while teachers are home with phones so the reshare chain
  runs overnight and through the morning.
- **Yoga Today — ~12pm.** **Only classes still ahead** (from ~2pm). Availability view. Listing
  a 6am class at noon makes the format look inattentive.

Saturday's Yoga Tomorrow becomes the weekly **Sunday Line-Up reel** — the tentpole.

**Yoga Today is the commercially valuable one.** Yoga Tomorrow is aspirational; Yoga Today is
availability — "there's still a 4pm if you want it." Filling late spots is a real studio pain
point and the thing they would pay to solve. A subscription pitch growing inside a free format.

### Current inventory (3 teachers with classes)

| | Tomorrow (all) | Today (from 2pm) |
|---|---|---|
| Mon | 6 | 2 |
| Tue | 5 | 1 |
| Wed | 6 | 3 |
| Thu | 1 | 1 |
| Fri | 2 | 0 |
| Sat | 1 | 1 |
| Sun | 5 | 3 |
| **Week** | **26** | **11** |

**Yoga Today is a five-teacher format, not a three-teacher one.** Run Yoga Tomorrow now; hold
Yoga Today until the Inner South cohort lands. Never force a thin day — silence costs nothing
in stories; a one-class card advertises smallness.

**Automate before committing.** Twice daily is fourteen manual builds a week. `build_profiles.py`
already turns schedule data into pages; teaching it to emit story cards is the same trick, and
it belongs near the top of the working-session list. Rituals dependent on a solo founder's
daily fiddling decay — usually just as they start working.

---

## 4. First cohort: Inner South (decided 16 Aug)

Chosen over Bayside. Bayside has more classes (14 vs 12) but only three studios, **12 of its 14
classes from Warrior One alone** — it would read as a Warrior One vehicle and kill the pitch to
every other Bayside studio. Inner South has **five studios** and far more headroom.

| Studio | Suburb | Feed | Classes | Teachers |
|---|---|---|---|---|
| Within | South Yarra | healcode | 5 | Alessia |
| Grass Roots | St Kilda | momence | 7 | Alessia, Janita |
| Happy Melon | Armadale | gomindbody | 0 | — none |
| (Here) Yoga | Port Melbourne | momence | 0 | — none |
| (Here) Yoga | Malvern | momence | 0 | — none |

Three of five studios are ingested with **no teacher attached** — every teacher signed there is
zero pipeline work.

### ⚠ Blocker before onboarding

**Happy Melon's feed has been dark for 23 runs since 27 July** (`pull/_feed_state.json`), as
have both Warrior One feeds. Onboarding Happy Melon teachers now would promise a listing the
pipeline cannot deliver. Momence feeds (Grass Roots, both Here Yogas) appear healthy — start
there. Also: teacher pages fed by the dark feeds may be showing stale times.

### Rules of engagement

- **Tell the studios first.** Sweeping a studio's teachers unannounced looks like going around
  them, and studios are the future paying customers. One message converts a possible irritation
  into the start of the commercial relationship — and included studios nudge their teachers to
  say yes.
- **Build the opt-out path before you need it.** If a teacher declines but her classes arrive
  via the studio feed, `merge.py` needs a suppression list. Put it in place *before* the first no.
- **Pace it.** A few a day, not twenty in an afternoon. Grass Roots and Within first — Alessia
  and Janita are already there and can be named, warming every later message.
- Target: 5–8 yeses across the five studios ≈ 30–40 classes/week — a daily card that never
  looks thin.

---

## 5. The onboarding DM (rung 0)

```
Hi [Name] — I'm Mark, I publish Yoga in Melbourne.

We list teachers' full schedules across every studio they teach at, so students
can find all your classes in one place, not just the [Studio] ones. Here's how
Janita's looks: [link to a live teacher page]

I'd like to add yours to our daily On the Mat update. Nothing needed at your
end — would you like me to go ahead?
```

Why each part:

- **Signed with a name.** An unsigned brand DM is a marketing blast; a named one is a person,
  and the whole strategy runs on it being a person.
- **A link to a live teacher page.** "On the Mat" means nothing to a stranger — it could be a
  newsletter or a spam account. One link removes the ambiguity entirely. Personalise which page
  by studio so the example is someone she probably knows.
- **Leads with her problem, not exposure.** Her students at one studio don't know she teaches at
  two others, and Mindbody/Momence structurally cannot fix that. "All your classes in one place"
  is a benefit to *her* — the most persuasive sentence available.
- **"Would you like me to go ahead?"** puts the labour on Mark and leaves her nothing to do but
  assent.

**Have the reply ready.** On a yes, send the finished page back the same day: *"Done — here's
yours: [link]. Anything wrong or missing, just tell me."* That is the editorial firewall
demonstrated in miniature at zero stakes, it hands her something to reshare, and it is the
moment the relationship actually forms. **Speed matters here.**

**No chasing.** A non-response only stays costless if it is treated as a non-event.

---

## 6. Localisation — sequencing

Localise the **asset**, not the **feed**.

The site can carry catchment pages tomorrow at zero cost — `catchment.json` already defines
eight with full suburb lists. "Yoga in Brighton", "Yoga in St Kilda" are high-intent local
searches with little competition, and adding them fragments no audience.

The **feed** cannot be split yet. A collab reel's power is audience count; a localised reel with
two collaborators loses roughly 60% of its reach while the follower base is still small. Five
catchment reels a week also reintroduces the repetition problem that moved the daily format to
stories.

**Threshold: a catchment earns its own card at roughly five teachers.** Until then — citywide
reel, localised site.

**Cohorts are a relevance-and-sales play, not a reach play.** Teachers in one catchment have
overlapping audiences, so a cohort collab will convert a lower share than the citywide one did.
Expect it; do not misread it as format decay. Keep running citywide collabs for reach alongside.

What density buys: the studio pitch ("we cover your area, here's the traffic"), a warm referral
chain (teachers in a catchment know each other), and a **repeatable template** — the licensing
endgame is a local-density playbook, not a city.

---

## 7. Open items

1. **Post the Sunday Line-Up reel** — same six cards. Still outstanding.
2. **Read the story's final numbers after expiry (~7pm 16 Aug)** and log them in the ledger.
3. **Check GA `instagram / story`** — pages/session for those 7, and whether any clicked out to
   a studio booking link. That would be the first end-to-end run of the whole chain.
4. **Fix the three dark feeds** (Happy Melon, Warrior One ×2) before onboarding at those studios.
   Spot-check teacher pages for stale times meanwhile.
5. **Build the opt-out list in `merge.py`.**
6. **Automate story-card generation** in `build_profiles.py` before committing to twice-daily.
7. **Mindbody API activation** — reframed: this is not plumbing awaiting its turn. Since the
   binding constraint on network growth is now studio feed coverage rather than teacher
   willingness, it is the single item that most raises the onboarding ceiling. The normalizers
   the pipeline README lists as "not built yet" sit in the same position.
8. Repo push still blocked (403 — repo not in session's authorised set). Notes are delivered as
   files in-conversation; commits staged locally.

---

## Assumptions flagged

- The reshare-attribution explanation for the 3.4x gap is inference from the view pattern, not a
  measured attribution.
- Click-rate denominators are estimated (unique reach taken as 134–200); the 3.5–5.2% band
  reflects that uncertainty.
- Scaling table assumes the click rate holds as the roster grows — untested.
- Posting-time recommendations (7pm / 12pm) are reasoning from decision windows and platform
  behaviour, not from YiM's own data. Instagram's "most active times" in the professional
  dashboard would replace them with measurement.
- n=7 clicks is far too small to conclude anything about the landing thesis. It is a first
  signal, not evidence.
