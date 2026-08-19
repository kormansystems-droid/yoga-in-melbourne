# The events pipeline, finished — 19 August 2026

Supersedes the "what still needs building" section of
`YIM-events-pipeline-2026-08-18.md`. The gate described there is unchanged.

## What was actually broken

Mark asked on 19 Aug why events still were not updating, and whether he had to
instruct manually. The honest answer was: **yes, but that was not why nothing was
moving.** There were four links in the chain and only one of them was his
approval.

| Step | State on the morning of 19 Aug |
|---|---|
| Discovery (`pull/pull_events.py`) | Built and committed — but `events.yml` was manual-trigger only, so it never ran. |
| Mark's approval (`--publish`) | Working as instructed. |
| `data/events.json` | Never committed. No target file existed. |
| **Rendering into the homepage** | **Did not exist.** Nothing read `events.json`. |

The last row was the real blocker. The Events, Retreats and Teacher Training
cards were hand-typed `<a class="strip-card">` blocks in `index.html`, and a
one-line script at the foot of the page hid any whose `data-until` had passed. So
the sections could only ever shrink. **Events & Workshops shipped with 7 cards
and was down to 3 by 19 August**, with 15 discovered events sitting unproposed.

Approving all 15 would have changed nothing on the site.

## What was built

**`build_events.py`** — renders `data/events.json` into the three bands, between
`<!-- EVENTS:workshop -->` / `<!-- EVENTS:retreat -->` / `<!-- EVENTS:training -->`
markers in `index.html`. Wired into `pull.yml` as a **separate step with
`continue-on-error: true`**, so an events fault can never take the nightly
timetable refresh down with it — the same separation `pull_events.py` was already
built on.

It renders; it cannot fetch and it cannot publish. Getting an event *into*
`events.json` still needs a proposal Mark has read and a deliberate
`--publish`. Rendering sits downstream of his yes, never around it.

**`data/events.json`** — the 15 hand-written cards migrated verbatim as
`source: "manual"`, keeping the fields no feed will ever supply: retreat
photographs and their alt text, region captions, hand-written date lines like
"15–16 & 22–23 Aug 2026", and evergreen entries with no end date at all (Warrior
One's 200-hour training). A pull never overwrites a manual entry.

**Weekly proposal.** `events.yml` gains `cron: "0 22 * * 0"` — Monday 8am
Melbourne. It still only ever *proposes*.

**The empty-diff guard.** `pull_events.py` now writes `pull/_events_actionable`
only when something is new, changed or broken, and the workflow raises an issue
only when that file exists. A weekly notification that fires regardless would
train Mark to ignore it, and then the week that mattered would be ignored too.
Repeat runs comment on one open thread rather than stacking new issues.

## Why the schedule does not weaken the gate

Mark's instruction of 18 Aug stands: events are cross-checked with him before
publication. The schedule does not touch that. **The gate was never the problem —
nothing was prompting him to walk through it.** A weekly nudge removes the
"nobody remembered to run it" failure and leaves the decision exactly where he
put it. `--publish` still appears nowhere in any workflow.

## How the migration was de-risked

The generator was proved to reproduce the existing page *before* it was allowed
to change anything: `/tmp/verify_events.py` parses both the old and new
`index.html`, decodes every value, drops the cards a browser was already hiding,
and compares the sets. It came back identical — 3 workshop, 5 retreat (4 with
photographs), 3 training — and that was confirmed against the live site after
deploy.

Byte-identical output was **not** the goal and would have been the wrong goal:
the hand-written HTML had inconsistent indentation and three different attribute
orders. What matters is that a reader sees the same page.

Two escaping bugs were caught by that check and would otherwise have shipped:
the migration was storing already-escaped text (`&#8211;`, `&amp;`) which then
got escaped a second time; and the first verifier compared raw attribute text,
which flagged the *correct* `&amp;` encoding of `&` in image URLs as a
difference. The verifier was wrong, not the generator — worth remembering, since
the instinct is to trust the test and change the code.

## Tests

`pull/test_events_render.py`, 14 checks. The one that matters most:

> **a band with nothing live is LEFT ALONE, not emptied**

If every event in a section has expired, `build_events.py` prints a warning and
leaves the existing markup untouched rather than writing an empty band. A section
that quietly empties is the exact silent failure this pipeline exists to prevent,
and it is the failure that actually happened.

## Still open

- **The 15 events are still unpublished** and await Mark's yes. Two need a
  decision beyond keep/drop: "30 Hr Teacher Training" (15 Aug — already past, and
  a duplicate of "The Yin Path" already on the site) and "Sri Lanka Yoga & Surf
  Retreat" (the same retreat as the existing "Yoga + Surf, Sri Lanka" card, via
  its Momence booking link rather than the studio page).
- **Within's `gowithintowin` page** loaded but its date line no longer parses —
  the studio changed its wording. Needs a manual entry or a scraper fix.
- **De-duplication against manual entries** is by `id` only. It did not catch
  either duplicate above, because a Momence booking link and a studio page are
  different URLs for the same event. Matching on title similarity plus date is
  the obvious next step, and it should propose a merge rather than silently
  dropping one.

## Unchanged

The editorial firewall. Schedule and event data are factual and public and need
no one's approval to aggregate; a teacher profile is editorial and never
publishes without her yes; coverage is never for sale. This pipeline only ever
touches the factual half.
