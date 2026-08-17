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
| Rachael Mellican | Here Yoga Malvern · Warrior One Brighton | ⚠ spelled **"Rach Mellican"** at Warrior One |
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

**2. Two teachers are spelled differently across feeds.** "Steph Philip" (Warrior One) vs "Steph
Phillip" (Here Yoga); "Rach Mellican" (Warrior One) vs "Rachael Mellican" (Here Yoga). Both need
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
