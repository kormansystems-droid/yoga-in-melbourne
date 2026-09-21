# Yoga in Melbourne: search baseline and the query split

**Date:** 6 September 2026
**Status:** First SEO note. Establishes the Google Search Console baseline to measure against.
**Source:** GSC Performance report, property `https://yogainmelbourne.com.au/`, 28 days to
3 September 2026, pulled live 6 Sep. Cross-referenced against `main` at commit `4733f6d`.

---

## 1. The conclusion

**Average position 45.1 is a meaningless number and should not be tracked.** It averages two
populations that behave nothing alike: brand and teacher-name queries that convert at 11 to 21
percent, and generic head terms that have produced **zero clicks from 177 impressions**.

**Teacher-name search is the beachhead.** It already works, it is barely contested, and it is
the search expression of the same moat the site is built on. Generic "yoga melbourne" is not
winnable this year and should not be a target.

**It does not follow that YiM should make more profiles for SEO reasons.** See section 6. The
returns are too small and too slow to justify profile throughput on their own. This note
*supports* the 15 Aug growth model rather than reversing it.

---

## 2. The baseline

28 days to 3 Sep 2026, Web search:

| Metric | Value |
|---|---|
| Total clicks | 25 |
| Total impressions | 703 |
| Average CTR | 3.6% |
| Average position | 45.1 |
| Clicks per day | 0.89 |
| Impressions per day | 25.1 |
| Distinct queries | 76 |

Impressions trend upward across the period: roughly 20 per day early, roughly 40 per day over
the last ten days. Consistent with new pages entering the index.

---

## 3. The split, which is the whole finding

Top ten queries by impressions:

| Query | Clicks | Impressions | CTR |
|---|---|---|---|
| yogainmelbourne | 8 | 31 | 25.8% |
| ryan mannix yoga | 1 | 16 | 6.3% |
| yoga in melbourne | 1 | 11 | 9.1% |
| ryan mannix | 1 | 9 | 11.1% |
| masha gorodilova | 1 | 6 | 16.7% |
| alessia frisina | 1 | 6 | 16.7% |
| yoga melbourne | 0 | 91 | 0.0% |
| yoga classes melbourne | 0 | 45 | 0.0% |
| yoga victoria | 0 | 24 | 0.0% |
| yin yoga retreat | 0 | 17 | 0.0% |

Grouped:

| Segment | Clicks | Impressions | CTR |
|---|---|---|---|
| Brand | 9 | 42 | 21.4% |
| Teacher names | 4 | 37 | 10.8% |
| Generic head terms | 0 | 177 | **0.0%** |
| Remaining 66 queries | 12 | 447 | 2.7% |

**Four generic queries account for 25% of all impressions and have never been clicked.** They
are what drags average position to 45.

The arithmetic that proves the distribution is bimodal: at a genuine average position of 45, a
site would expect roughly 0.2 to 0.4 percent CTR, so **1 to 3 clicks** from 703 impressions.
The site got **25**. The excess is entirely brand and teacher names, which must therefore be
ranking far better than 45.

---

## 4. Search demand and editorial investment are pointing at different people

Query data cross-referenced against page depth on `main`:

| Teacher | Impressions | Clicks | Page | Words |
|---|---|---|---|---|
| Ryan Mannix | 25 (two queries) | 2 | **Listing** | 238 |
| Masha Gorodilova | 6 | 1 | **Listing** | 194 |
| Alessia Frisina | 6 | 1 | Full profile | 1,214 |

Ryan Mannix is the largest teacher-name driver on the site and sits on a 238-word stub. A stub
already surfaces for his name, which indicates competition for that query is weak and a full
profile would likely take the top result.

None of the launch five appear in the top ten. Their profiles are days old and may sit in the
other 66 queries, which were not paged through.

**This is a hint, not a result.** 25 impressions over 28 days is a tiny sample. The defensible
action is to *ask* Ryan and Masha whether they would like a full profile, not to reorder the
editorial plan. Full page depth for reference: Emma 1,227, Zoe 1,296, Janita 1,176, Rayne 1,420,
Shelley 1,514. Listings: Sarah Metzger 195, Franks Martin 205, Steph Philip 192.

---

## 5. What to stop doing

**Stop tracking average position.** It is noise across a bimodal distribution and it will look
worse as more generic impressions accumulate, which is the opposite of the truth.

**Stop treating generic head terms as a target for this year.** 177 impressions at zero clicks
means ranking somewhere in the 50s to 90s against studios with years of domain authority.
Closing a 40-place gap needs backlinks, and backlinks come from publishing things worth linking
to.

**Track instead:** clicks from teacher-name queries, and the count of published full profiles.

---

## 6. Where this sits against the 15 Aug growth model, which has not changed

`YIM-growth-model-2026-08-15.md` established that YiM **does not grow by recruiting teachers to
profile**; it grows by publishing through an expanding network, with profiles as one output
rather than the engine. Nothing here reverses that, and it would be a misreading to take
"profiles are the SEO asset" as an argument for profile throughput.

The sizing is the reason. See the assumptions in section 8, but on the estimate there, a full
profile is worth perhaps **5 to 8 search clicks per month**. Eleven teachers is 60 to 90 a
month; twenty-five is 150 to 200. Against a single collaboration reel returning **3,200 views**,
search is not a channel that justifies its own production cost at this stage.

**The correct reading: SEO is a compounding by-product of work already justified on other
grounds.** Profiles remain worth making for the reasons the growth note gives, and search
returns accrue quietly on top. If profile production ever needs a business case, it is not this
one.

---

## 7. Open questions, each with a metric and a date

| Question | How to check | When |
|---|---|---|
| Do the launch five appear in search at all? | GSC Queries, filter by each surname, 28 days | 1 Oct 2026 |
| Did Emma's profile plus Episode 7 move her name query? | Impressions for "emma strembickyj", zero before 3 Sep | 1 Oct 2026 |
| Is the impressions trend real or an indexing blip? | Impressions per day, 28 days to 1 Oct vs 25.1 baseline | 1 Oct 2026 |
| Are all profile pages indexed? | GSC Pages report, indexed count vs 11 teachers plus studios | Next session |
| Does a full profile actually lift a teacher's name query? | If Ryan is promoted, his impressions and CTR before and after | 60 days after publish |
| Do generic head terms ever move? | Average position for "yoga melbourne", currently unranked in practice | 1 Dec 2026 |

---

## 8. Assumptions, flagged so they can be challenged

1. **The bimodal inference rests on ten queries.** The other 66 were not examined. If the tail
   contains a mass of mid-position teacher-name queries, the picture changes. Low risk, but
   unverified.

2. **"5 to 8 clicks per profile per month" is an extrapolation from single-digit click counts.**
   It assumes a full profile roughly doubles impressions and lifts CTR from about 8 to about 15
   percent. Both are plausible and neither is measured. Treat as an order of magnitude, not a
   forecast.

3. **Ryan Mannix's name demand may be his own brand, not category demand.** That is precisely
   what YiM would want to capture, but it means the result may not generalise to other teachers.

4. **Twenty-eight days on a young domain is early.** Position 45 for a new site is unremarkable
   and improves without intervention as authority accrues.

5. **The counter-case to section 5 is real.** 177 impressions on head terms means Google already
   considers the site relevant for them, just badly placed, and that is where the actual volume
   lives. Writing them off permanently would be a mistake; writing them off *for this year* is
   the claim being made.

6. **GSC data was read from the live property on 6 Sep for the period ending 3 Sep.** GSC lags
   by two to three days, so the final days of the window may still revise upward.

---

## 9. What has not changed

**The editorial firewall is untouched and is not negotiable.** Nothing in this note licenses
publishing a profile to capture a search query. A profile requires the subject's yes, coverage
is never for sale, and the fact that Google shows demand for a teacher's name is not a reason
to write about her. The action arising from section 4 is *to ask Ryan Mannix and Masha
Gorodilova*, and their answer settles it.

Schedule data remains the exception it has always been: factual, public, and needing nobody's
approval.

**The near-term channel is still Instagram.** 25 search clicks in 28 days against 3,200 views
from one collaboration reel. Search is the twelve-month compounding play.

**The 19 Aug acquisition finding still stands** and is the reason the reels are built as they
are: publication-led pieces converted at 2.93% follows per eligible viewer (61 from 2,082)
against 0.30% for podcast-episode promos (2 from 656), a 9.6x gap, Fisher two-tailed
p = 8.6 x 10^-6. Profile visits per viewer baselines: Alessia carousel 4.35%, Alessia podcast
reel 1.27%.
