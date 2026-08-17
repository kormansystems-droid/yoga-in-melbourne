# The listing rung works — and it changes what On the Mat is for

**Date:** 17 August 2026 (evening)
**Repo state:** `origin/main` at `5923d1f`. Ryan Mannix + Good Vibes not yet pushed — files
delivered to Mark, awaiting a Code session.

---

## The conclusion first

**Mark onboarded two teachers today. It was the easiest ask to date, and both, unprompted, then
expressed interest in a profile.** Six days after the listing rung was designed and one day after
the first listing shipped, the mechanism is validated: a smaller door opens more often, *and* it
sells the room behind it.

**But On the Mat is not the growth engine, and this note exists partly to correct that.** Mark's
position, and the evidence supports him:

> The reshares and the mentions are not the true measure. What drove the followers and the likes
> was **the five-teacher collab reel**. When we have five new teachers to run a new version of
> that reel, that is where we will see the effect.

That reframes the whole machine. **On the Mat is a recruitment instrument whose output is
teachers, not users.** Teachers then become collab slots on reels, and the reel is what buys
audience. Judging On the Mat by its own view counts is measuring the wrong end of the pipe.

---

## The evidence for the correction

| Format | Date | Result |
|---|---|---|
| **Reel — "The real teachers of Yoga in Melbourne", 5 collaborators** | ~10–15 Aug | **3,200 views · 50 followers · 100 likes** — the busiest day on the site |
| IG post, portraits, no collab | ~10–15 Aug | 3 followers · 16 likes |
| Story — daily line-up, mentions + reshares | 15 Aug | Tagged frames avg **123 views**, untagged **36**. Reshared by every mentioned teacher *and* by Grass Roots unsolicited. Likes ≈ 0 |
| Story link stickers → site | 15 Aug | **7 clicks** (GA `instagram / story`) |

Reshares and mentions were *high* on the story and the traffic was *low*. Views and likes were
high on the reel and the traffic followed. The story's reach is real but shallow; the reel's is
the one that converts.

**The story's actual product is a teacher who said yes.** Two today.

---

## The onboarding finding

**Why the ask is easy — and what to protect.** A listing asks for nothing. No interview, no
photo, no bio, no time, no approval of anything about who they are. It offers to promote their
classes. The only sensible answer is yes.

> Every gram of friction added to that ask costs conversion, and none of it is needed for a
> listing. Do not add a photo request, a bio field, or a form.

**The escalation was not designed and is the more interesting half.** Both teachers raised
profiles themselves after agreeing to be listed. The listing turned out to be a sales pitch for
the rung above, delivered by the product rather than by Mark. This is §14a's loop working, but
faster and in a direction the note did not predict.

**Roster: 5 → 8 in one day.** Steph Philip (Warrior One Brighton + (Here) Yoga Malvern), Ryan
Mannix (Good Vibes Collingwood + Northcote), and two more onboarded today. Good Vibes is YiM's
first coverage north of the river.

---

## What this means for the next move

**The five-teacher reel is now the milestone that matters.** Not "more listings" — five *new*
teachers, then a new version of the collab reel. That is the testable claim, and it is Mark's,
not an inference from the data.

Note the constraint this implies: **Instagram allows 5 Collab collaborators per post.** The reel
format is capped at five whatever the roster size, so a growing roster means *more reels*, not
bigger ones — which is fine, and arguably better, since each one is a fresh five-way distribution
event rather than a diluted one.

---

## What breaks first, in order

| # | Bottleneck | Why now | Fix |
|---|---|---|---|
| 1 | **Mark's time per listing** | Each listing is a hand-authored template file + a `schedule.json` edit + a Code session. Fine at 2/week, impossible at 2/day | Generate the listing page from `schedule.json` instead of authoring one per teacher |
| 2 | **Hardcoded homepage lists** | Router row and Teachers grid are both hardcoded. The 17 Aug note said "do it before fifteen teachers" — the roster went 5 → 8 in a day | Same fix, same job |
| 3 | **The profile queue** | If listing reliably produces profile interest, willing subjects will accumulate far faster than Mark can interview, write, get approved and record | State a cadence: "one profile a fortnight, I'll come to you." Converts a backlog into a waiting list |
| 4 | **Story length** | Already anticipated: 20 teachers ≈ 22 frames. At 8 teachers this is now near, not theoretical | The designed answer — YiM Select on the story, full schedule on the site — is still unbuilt |
| 5 | **Studio coverage** | Each new teacher may bring an un-ingested studio. Good Vibes today. Some will have no feed at all | Ask where else they teach *before* the page publishes, so the coverage line is honest on day one |

**On #3, the reasoning matters more than the mechanic.** A broken promise to a teacher damages
exactly the trust the firewall exists to protect. A stated cadence also makes the profile
scarcer, which is the correct signal given coverage is never for sale.

---

## Also shipped today

Recorded briefly; each has its own note.

| Change | Note |
|---|---|
| Zoe Kanat in the homepage hero; player commented out until her episode publishes | `YIM-shipped-to-main-2026-08-17.md` |
| Pipeline fixes, booking links on every class row, story-card generation, homepage router | same |
| Steph Philip listing + the `_listing` rung-0 template | `YIM-steph-phillip-listing-2026-08-17.md` |
| Spelling corrected to Philip, one L, with a 301 | `YIM-steph-philip-spelling-2026-08-17.md` |
| Story opener now leads `<Day> Yoga`, date moved to the fact line | `YIM-story-opener-2026-08-17.md` |
| **The nightly story workflow fired at 7pm and committed five frames unaided** (`5923d1f`) | first confirmed end-to-end automated run |

**Undelivered, awaiting a Code session:** Ryan Mannix, Good Vibes Collingwood + Northcote, and
the pronoun-free listing copy. Files are in the conversation.

### Two hazards found while onboarding

**Feeds are confidently wrong about names.** (Here) Yoga publishes Steph as "Phillip"; she spells
it "Philip". Only asking her caught it — no amount of cross-feed reconciliation would have. Good
Vibes is worse: it publishes **first names only**, returning `"Ryan ."` with a literal full stop
for the surname. A second Ryan there would land silently on Mannix's page and the feed could not
tell them apart. **Add "and how do you spell your name / what's your surname?" to the DM.**

**The listing template said "she" in two places.** Every teacher to date has been a woman, so it
had never been wrong; Ryan is the first man and it would have shipped wrong on his page. Fixed by
removing the pronoun rather than adding a gender field — a field means classifying every future
teacher to render a sentence, and that step gets forgotten on exactly the detail a teacher
notices first.

---

## Assumptions, flagged

1. **The onboarding rate will keep rising.** Mark's read, and reasonable. But **n = 2**, both
   possibly warm contacts. The *mechanism* is validated; the *rate* is not.
2. **Listed teachers transfer followers, progressively, not just at profile stage.** Mark's
   hypothesis from 16 Aug. Untested. Steph and today's two are listed but not profiled — the
   clean test case.
3. **A second five-teacher collab reel will replicate the first.** The single most important
   assumption in the plan. One observation, novel format, possible novelty effect. If reel #2
   returns materially less, the acquisition model needs rethinking before the roster is scaled
   against it.
4. **Warrior One rows on Alessia, Rayne and Steph are a hand-entered snapshot**, that feed dark
   since 27 July (25 runs). They now carry live booking links, so staleness is actionable rather
   than merely wrong.
5. **Ryan's Sunday classes** came from a lossy paged read. His Wednesday classes came from a clean
   single-day query. The 05:00 pull corrects both.

---

## Open, with the check that settles it

| Item | Check |
|---|---|
| **Does the second five-teacher collab reel replicate the first?** The decisive test | Views, followers and site sessions in the 48h after posting, vs 3,200 / 50 / the 15 Aug spike |
| **Do *listed* teachers transfer followers?** | Steph + today's two: reshare reach and `instagram / story` sessions over the next fortnight, vs the profiled five |
| **Does the onboarding rate hold?** | Teachers onboarded in the week to 24 Aug. Two in a day is a rate only if it repeats |
| **Generated listings before the roster passes ~12** | Time spent per new teacher. If it is still ~30 min of Mark's time at teacher 12, this is overdue |
| **Booking links move outbound clicks?** | GA `click` on teacher pages, week of 24 Aug vs 17 Aug |
| **Router moves pages/session?** 1.42 now, 1.9 baseline | After the next reel. Above ~2.2 means arrivals are routed rather than stopped |
| **gomindbody adapter** — one job, not three; best path is Mindbody API activation, currently shelved by Mark | Any Warrior One or Happy Melon class reappears on a profile |
| **AEDT** — Melbourne shifts in October; `story.yml` at 09:00 UTC becomes 8pm | Change to `0 8 * * *` or accept the drift |

---

## What has not changed

**The editorial firewall is absolute.** Nothing in today's growth result bends it. Listings are
factual and public and need no approval; profiles are editorial and never publish without the
subject's yes; coverage is never for sale. The escalation from listing to profile is an
*invitation being accepted*, not a transaction — and the cadence proposed above exists precisely
so that a promise made under that invitation is one YiM can keep.

Aggregated cross-studio schedules remain the moat. Rung 0 still involves asking, because the ask
is the mechanism — and today it turned out to be the mechanism twice over.
