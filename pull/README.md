# Schedule pipeline

Single source of truth for every teacher's timetable, fed from the studio booking
systems until the official Mindbody API replaces the pull layer.

```
  studio feeds            normalize          merge.py            build_profiles.py
 (Mindbody x2, Momence) ──────────► rows ──────────► data/schedule.json ──────────► *.html
        ▲                                                                              │
        └─ recon.py captures the real endpoints/JSON once, to write the normalizers    └─ Netlify deploys
```

## Layers

- **data/schedule.json** — the only file that changes when timetables change. Holds the
  `studios` registry (static: links, booking URLs) and each teacher's `aliases`,
  `pronoun_possessive`, and `classes`.
- **build_profiles.py** — fills each `templates/*.template.html` from schedule.json. Done & verified.
- **pull/merge.py** — folds normalized rows into schedule.json: matches each feed's raw
  teacher name via `aliases`, drops anyone on the `suppressed` opt-out list, dedups, and
  only rewrites studios passed in `--covered` (a failed feed can't wipe a studio off
  every profile). Done & verified.
- **pull/recon.py** + **.github/workflows/recon.yml** — one-time capture of what the
  widgets actually fetch, so the normalizers are written against real data.
- **pull/normalizers.py** — one function per platform, turning its captured payload into
  normalized rows. Built: `momence_rows`, `healcode_rows`, `mindbody_rows` (Public API v6),
  `gomindbody_rows`, `squarespace_rows`.
- **build_story_cards.py** — renders the same schedule data as Instagram story cards.
  Run nightly by `.github/workflows/story.yml`.

## The opt-out list

A teacher's classes arrive through her studio's feed whether or not she has heard of
YiM. If she is asked to be listed and says no, that no has to survive every future
pull. Add her to the top-level `suppressed` list in `schedule.json`:

```json
"suppressed": [
  {"name": "Jane Smith", "note": "declined 12 Sep", "date": "2026-09-12"}
]
```

Matched on the raw string as the feed spells it, case- and whitespace-insensitive.
She is dropped *before* alias matching, so nothing downstream — profiles, story cards,
line-ups — can leak her by forgetting to check. merge refuses to run if a name is both
registered and suppressed, since that would silently empty a live profile.

## Normalized row (the contract between normalize and merge)

```json
{ "studio": "warrior-one-brighton", "teacher": "Alessia Frisina",
  "day": "Tue", "start": "06:00", "time": "6:00–7:00 AM", "class": "Vinyasa Flow" }
```

`teacher` is the raw string as that feed spells it — merge resolves it via aliases.

Two optional keys: `sub` (true when the feed marks a cover) and `url` (a deep link to
that session's booking page). Where `url` is present the profile links the class row
straight at it; otherwise the row falls back to the studio's booking page. No
normalizer sets `url` yet — adding it to one is the whole change, since merge and the
templates already carry it through.

## The recon step (do this once)

1. Push this repo. GitHub → Actions → **Recon studio feeds** → **Run workflow**.
2. When it finishes, download the **recon_out** artifact.
3. Send it back. It contains, per studio: the captured JSON responses, a manifest of
   their URLs, the rendered HTML, and a screenshot — everything needed to write the
   three normalizers and pin the production endpoints (plain HTTP, no browser).

## Production run (added after recon)

A second workflow on a weekly schedule (and manual trigger): fetch each endpoint →
normalize → `merge.py` → `build_profiles.py` → commit if changed → Netlify redeploys.

## Two policy notes

- **Source of truth is the feed**: whoever's on a slot this week is what shows. Subs
  are not reconstructed (decided deliberately — see the profile work).
- **Approval**: treat the live timetable as factual data covered by the teacher's
  one-time profile approval; keep per-change sign-off for editorial (prose, hero,
  framing). State this to teachers at onboarding so auto-updating is opt-in, not a surprise.
