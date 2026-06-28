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
  teacher name via `aliases`, dedups, and only rewrites studios passed in `--covered`
  (a failed feed can't wipe a studio off every profile). Done & verified.
- **pull/recon.py** + **.github/workflows/recon.yml** — one-time capture of what the
  widgets actually fetch, so the normalizers are written against real data.
- **normalizers** — *not built yet*; written after recon. One small function per platform
  that turns its captured JSON into normalized rows (below).

## Normalized row (the contract between normalize and merge)

```json
{ "studio": "warrior-one-brighton", "teacher": "Alessia Frisina",
  "day": "Tue", "start": "06:00", "time": "6:00–7:00 AM", "class": "Vinyasa Flow" }
```

`teacher` is the raw string as that feed spells it — merge resolves it via aliases.

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
