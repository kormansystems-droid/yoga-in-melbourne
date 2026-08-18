# Teacher roster — five studios

**Harvested 16 August 2026** from the live studio feeds (Momence API, Mindbody/healcode widget)
plus Mark's Warrior One screenshots. **68 distinct teachers; 64 not yet on YiM.**

Spelling is exactly as each feed gives it. Where one person appears under two spellings the
variants are noted — those need `aliases` entries in `schedule.json` before merge will match them.

---

## ⚠ Correction (16 Aug): the tiering below is a coverage artifact, not a fact about teachers

An earlier version of this note split the roster into "multi-studio" and "single-studio" and
told Mark to approach the first group first. **That is selection bias, and Mark caught it.**

These five studios are a tiny, geographically clustered sample of Melbourne. A teacher only
shows as "multi-studio" if *two or more* of her studios happen to be among the five. If random
sampling applied, the detection rate for a teacher working at 3 studios out of a pool of ~80
would be under 1%. Clustering means the real rate is far higher than that — 13 of 68 were
detected — but the direction is unambiguous:

> **"Single-studio" almost always means "only one of her studios is visible to us."**
> Most of the 55 in Tier 2 probably teach elsewhere too. We simply cannot see it.

**What follows:**

1. **The cross-studio pitch applies to nearly everyone**, not to thirteen people. It is the
   strongest line in the DM regardless of tier.
2. **But delivery may fall short of the pitch.** If a teacher works at four studios and YiM
   ingests two, her page shows a partial schedule presented as complete. That is the same trust
   failure as stale data, only structural — and it is worse, because her own students will
   notice first.
3. **So ask her.** One line — *"where else do you teach?"* — gives her true studio list, tells
   YiM which feed to add next, and lets the page state its coverage honestly. **Teachers reveal
   the studio graph.** Onboarding stops being just recruitment and becomes the mapping layer for
   the pipeline: every teacher onboarded points at the next studio worth ingesting.
4. **Listing pages should name their coverage** — "her classes at Within and Grass Roots" — not
   imply completeness. The gap then prompts the correction: she sees what's missing and tells you.

Use the tiers below as *known* studio overlaps, not as a ranking of who matters.

---

## Tier 1 — teachers with two or more studios **visible to YiM** (13)

Not "the multi-studio teachers" — the ones whose overlap we can already see. They're worth
approaching early only because YiM can deliver the full cross-studio schedule for them
immediately, with no new feeds required.

| Teacher | Studios | Notes |
|---|---|---|
| **Rachel Goldenberg** | Grass Roots · Here Yoga Malvern · Warrior One Brighton | **3 studios** — highest-value single approach in the list |
| **Tommy Kende** | Grass Roots · Here Yoga Port Melbourne · Within | **3 studios** (covers at Within) |
| Alec Snow | Grass Roots · Here Yoga Malvern | Hot Flow, Vinyasa, Yin |
| Alyssa Lynikas | Here Yoga (both) · Warrior One Brighton | Slow/Dynamic Flow |
| Brenton Alexander | Grass Roots · Warrior One Brighton | Hot Flow, Vinyasa, Slow, Yin |
| Dhini Pararajasingham | Grass Roots · Warrior One Brighton | Vinyasa, Slow, Yin |
| Liz Wells | Grass Roots · Here Yoga Port Melbourne | Vinyasa / Dynamic Flow |
| Nickie Hanley | Grass Roots · Here Yoga Port Melbourne | Slow Flow + Restorative |
| **Rach Mellican** | Here Yoga Malvern · Warrior One Brighton | She is called **Rach** (Mark, 18 Aug). (Here) Yoga's "Rachael" is the alias, not the other way round |
| Sarah Metzger | Here Yoga (both) · Warrior One Brighton | Dynamic, Slow, Candlelit Yin |
| Steph Phillip | Here Yoga Malvern · Warrior One Brighton | ⚠ spelled **"Steph Philip"** at Warrior One |
| *Alessia Frisina* | Grass Roots · Warrior One (both) · Within | already registered — **3 studios** |
| *Emma Strembickyj* | Kozen Hawthorn · Within | already registered — see note below |

---

## Tier 2 — teachers seen at one studio so far (55)

Not single-studio teachers. Teachers whose other studios YiM cannot yet see.

### Kozen Yoga, Hawthorn (15) — *no YiM teacher here yet; feed healthy*
Amanda Cochrane · Amy Auge · Barbara Fitzpatrick-Haddy · Chantal Doesburg · Danny McGrane ·
Fai Mos · Hilary Davis · Jennifer Chen · Jill Devine · Meg O'Hanlon · Mike McGregor ·
Nat Jefferis · Rob McMillan · Ryan Chhajed · Thana Buathong

### Warrior One, Brighton & Mordialloc (14) — *feed currently dark*
Alisa L · Divyani Nag · Fiona Rigg · Franks Martin · Heidi Mellican · Jenni Morrison-Jack ·
Jori Sandler · Kristian Crowe · Melody Yeung · Nat Commons · Natasha Tropeano · Sarah Hammond ·
Sary Davis · *Rayne Watkin (registered)*

### Grass Roots, St Kilda (13)
Amber Lee · Angelica Di Camillo · Cecilia Low · Imogen Sist · Josh Piterman · Lauren Fazlic ·
Lily Boston · Pam Morris · Polly Schaverien · Rajbinder Kaur · Susie Nicholson · Tailem Tynan ·
*Janita Doelken (registered)*
> Several of these teach Pilates or Breathwork rather than yoga — Rajbinder Kaur, Angelica Di
> Camillo, Polly Schaverien, Susie Nicholson, Lauren Fazlic, Pam Morris, Lily Boston, Amber Lee
> (Pilates); Imogen Sist, Josh Piterman (Breathwork). Decide whether YiM's remit includes them
> before approaching.

### Here Yoga, Port Melbourne & Malvern (9) — *no YiM teacher here yet; feed healthy*
Amelia James · Candice Towson · Cassie Karro · Georgia Hunter · Jodie Burton · Kelvin Wong ·
Melissa Thomas · Rachel Ramsland · Sacha Flanagan

### Within, South Yarra (4)
Eliza Hilmer · Gisele Cabasa · Masha Gorodilova · Ryan Mannix (covers)

---

## Findings worth acting on

**1. Emma Strembickyj's page has no schedule, and now we know why.** She's registered but holds
zero classes in `schedule.json`. The feeds show her teaching at **Within on Mon 24 Aug** and
**Kozen on 26 Aug** — both *outside* the 7-day pull window. Any teacher who works irregularly or
rotates fortnightly will silently show an empty schedule. Worth extending the pull window, or
flagging registered teachers who return zero rows.

**2. Two teachers are spelled differently across feeds — and in both cases the feed that looked
canonical was wrong.** Steph is **Philip**, one L (confirmed 17 Aug); (Here) Yoga's "Phillip" is the
alias. Rach is **Rach** (confirmed 18 Aug); (Here) Yoga's "Rachael" is the alias. Two for two: the
person, not the feed, decides. Ask at onboarding, before a URL is minted. Both need
`aliases` entries or they'll appear as two people and their cross-studio schedule — the whole
point — won't merge. Expect more of this at scale; it is the main hidden cost of onboarding.

**3. Kozen and Here Yoga have healthy feeds and no YiM teacher at all.** 24 teachers between them,
zero pipeline work required. Kozen also broadens the map north-east into Hawthorn, away from the
bayside/inner-south cluster.

**4. Coverage projection.** Tier 1 alone (11 new teachers) would take the roster from 4 active
teachers to 15, across 6 studios and 8 suburbs — comfortably past the density needed for a daily
"On the Mat" that never looks thin, and past the five-teacher threshold for a localised card.

**5. Ask every teacher where else she teaches.** It is the cheapest possible way to map the
studio graph, it makes her page honest, and each answer points at the next feed worth building.

---

## Sources

Grass Roots (Momence host 34431), Here Yoga Port Melbourne + Malvern (Momence host 40780),
Kozen Hawthorn (Momence host 44752), Within South Yarra (Mindbody healcode widget 188058,
weeks of 16 / 19 / 22 Aug), Warrior One Brighton + Mordialloc (Mark's app screenshots, 16 Aug —
the gomindbody feeds have been dark since 27 July).

Momence and healcode feeds return a rolling window, so this is a snapshot of teachers scheduled
in mid-to-late August. Teachers on leave, or rostered further out, will be missing. Re-run
`pull/roster.py` for a current list once the pipeline harvests it automatically.

---

## Warrior One, verified in full — 18 August 2026

All three studios read off the studio app for a complete week. **Warrior One has three
locations, not two:** Brighton, Mordialloc and **Mornington**, the last of which had never been
registered. Sixteen YiM rows checked; fifteen correct after three weeks of a dark feed, one
wrong only on duration.

**Brighton and Mordialloc are different catchments and their timetables are independent.**
Do not infer one studio's slot structure from another's — an earlier attempt to do exactly that
called a correct Mordialloc row suspicious because 10:45 AM is not a Brighton-style Mordialloc
slot on other days. It is: Tuesdays differ. (Mark, 18 Aug.)

**Class counts on the app overstate a teacher's regular load, because they include
substitutions.** Franks Martin appeared with ten Brighton classes in the week to 23 Aug and
reads as the studio's busiest teacher; most of that is covering. Do not rank recruitment targets
by observed class count without checking. (Mark, 18 Aug.)

### Warrior One teachers not yet on YiM

| Studio | Teachers |
|---|---|
| Brighton | Franks Martin · Kristian Crowe · Dhini Pararajasingham · Sarah Metzger · Nat Commons · Brenton Alexander · Alyssa Lynikas · Rachel Goldenberg · Sary Davis · Rach Mellican · Heidi Mellican |
| Mordialloc | Jori Sandler · Melody Yeung · Natasha Tropeano · Divyani Nag · Sarah Hammond · Nat Commons · Jenni Morrison-Jack · Fiona Rigg |
| Mornington | Shell Douglas · Katie Mellican · Jess Harrison · Rachel Turnbull · Sarah Hammond · Jess Goozee · Kaela Raku · Elinor Hagelin · Natasha Tropeano · Heidi Mellican |

**Cross-studio within Warrior One:** Sarah Hammond and Natasha Tropeano (Mordialloc +
Mornington), Heidi Mellican (Brighton + Mornington), Nat Commons (Brighton + Mordialloc).

**Three different Mellicans — Katie, Heidi and Rach.** Distinct people. Never alias them together.

---

## The substitution bias runs both ways — 18 August 2026

Adding Shelley Armstrong (Grass Roots) exposed the other half of the substitution
problem Mark named about Franks Martin.

`normalizers.momence_rows` attributes a class to `teacher` and flags it `sub` when
`originalTeacher` differs. So a covering teacher gains rows and **the teacher whose
class it actually is loses them entirely.**

Shelley in the 14-day window to 1 Sep:

| Melbourne | Class | Feed attributes it to |
|---|---|---|
| Tue 6:15–7:15 AM | Hot Flow | **Shelley** |
| Wed 6:15–7:30 PM | Vinyasa flow | **Shelley** |
| Wed 5:00–6:00 PM | Vinyasa flow | Tailem Tynan (covering) |
| Wed 6:15–7:30 PM | Slow Flow + Restorative | Tania Perry (covering) |
| Fri 7:30–8:30 AM | Slow Flow | Brenton Alexander (covering) |
| Fri 9:30–10:30 AM | Vinyasa flow | Brenton Alexander (covering) |

**Her page shows two classes. She teaches about five.** Four are covered because she
is away the week of 26 August — a temporary absence, not a schedule change, and the
pipeline cannot tell the difference.

Two consequences:

1. **Observed counts overstate the coverer and understate the covered.** Ranking
   recruitment targets by class count is wrong in both directions. Franks Martin
   looks bigger than she is; Shelley looks smaller.
2. **A new teacher's first impression of her own page may be that YiM has half her
   week.** That is the trust failure the aggregation is supposed to prevent, and it
   lands hardest on exactly the teachers being onboarded.

**Proposed fix, needs Mark's call.** `momence_rows` already knows `originalTeacher`.
Emit a second row for her, flagged `covered`, and render it with a tag beside the
class — *"covered this week"* — the same mechanism as the existing `substitute` tag.
Her page then shows her real week and tells the truth about who is on the mat. The
alternative, showing nothing, is what happens today.

Until then, seed a covered teacher's missing rows by hand and expect the 05:00 pull
to strip them back on any studio with a live feed.
