# Shelley's portrait and the listing portrait default — 2026-08-18, evening

## Conclusion

Both commits the evening handoff listed as "owed to main" are built and delivered as files.
They were never on `main`; the handoff was right. One correction: a listing may now carry a
portrait, which **reverses** a line in `YIM-standing-decisions.md`, so that note is amended
in the same drop rather than left contradicting the code.

## What shipped

Applied to a clean clone of `origin/main` at **`757ea6d`** and rebuilt with
`python3 build_profiles.py`. Only `shelley-armstrong.html` changed — Steph, Ryan and Sarah's
pages are byte-identical, because per-teacher templates are not regenerated from `_listing`.

| File | Destination | Note |
|---|---|---|
| `shelley-armstrong.template.html` | `templates/` | 148 KB — the portrait is embedded as base64, not a separate asset |
| `_listing.template.html` | `templates/` | Now ships **with** the portrait head; comments say how to strip it |
| `crop-portrait.py` | repo root | Face-anchored crop, three outputs |
| `shelley-armstrong.jpg` | `img/` | 1200×630 Open Graph. Verified: face intact, not a decapitated centre crop |
| `shelley-armstrong.html` | repo root | Generated, delivered so no local Python run is needed |

## Repo state as found

`origin/main` was at `757ea6d`, not `193df6b` — the 7pm `story.yml` run committed
`story/2026-08-19-tomorrow/` (nine frames + captions) after the handoff was written. Per the
handoff, ignore that set; Mark posts the hand-built nine.

## Correction to the handoff

**Missing Open Graph images are four, not three.** `img/` held only Alessia, Emma, Janita,
Rayne and Zoe. Steph Philip, Ryan Mannix, Sarah Metzger *and* Shelley Armstrong all served a
404 to link previews. Shelley is fixed by this drop. **Three remain: Steph, Ryan, Sarah** —
each needs one supplied photograph and one `crop-portrait.py` run.

## What changed from the previous position

`YIM-standing-decisions.md` listed "no portrait" among the things a rung-0 listing may not
carry, alongside the essence line and pull quote. That conflated two different permissions.
A photograph she supplies is hers to publish; a story about her is not. The amendment is
written into the Editorial section of the standing-decisions note.

Unchanged: the firewall itself. A profile still requires an interview and her approval of the
words, coverage is still never for sale, and a portrait does not promote a listing to a profile.

## Open questions

- **Shelley's frame posts 7pm Wed 19 Aug showing two classes; she teaches about five.** The
  substitution bias in `normalizers.momence_rows` is still unfixed and still Mark's call. If
  she asks, the honest answer is that the feed attributes a class to whoever is teaching it,
  and four of hers sit under a covering teacher the week of 26 August.
- **Three OG 404s** — check `img/steph-philip.jpg`, `img/ryan-mannix.jpg`,
  `img/sarah-metzger.jpg` exist before any of those pages is shared in a DM or story.
- **Sarah's Mordialloc rows** — one-minute add once Mark supplies the days.

## Assumptions flagged

- **Inferred, not verified:** that the files in `~/Downloads` dated 18 Aug 21:27–21:28 are the
  same artefacts the previous session produced. They match the handoff's description exactly
  (filenames, the base64 placeholder, the 1200×630 OG size), but I did not see that session.
- **Inferred:** that delivering the generated `shelley-armstrong.html` is safe. Basis — the
  5am `pull.yml` run executes `pull/pull.py` and commits `*.html`, so it would regenerate the
  page anyway; shipping it just makes the site correct on commit instead of at 5am.
- **Measured:** the OG crop was inspected once at 480×252. Face centred, intact.

## Working note

This session has device-bridge tools and used them (`~/Downloads` granted, four files staged).
It has **no push access** — no `gh`, no credentials — so everything goes to Mark as files for
the GitHub web UI.
