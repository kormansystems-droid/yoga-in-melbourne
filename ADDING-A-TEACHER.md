# Adding a teacher

Two files change per teacher: one entry in the data, one template. Then build.

## 1. Register them — `data/schedule.json` → `teachers`

```json
"Given Family": {
  "name": { "given": "Given", "family": "Family" },
  "aliases": ["Given Family"],     // exact spelling EACH studio feed uses; add variants as found
  "classes": []                     // leave empty — the pull fills this (or hand-key for now)
}
```

The key (`"Given Family"`) is the canonical name and must match the template's `data-teacher`.
`aliases` is how the pull matches this person across studios — strip suffixes like "(substitute)";
add a new alias whenever a feed spells them differently (merge.py reports unmatched names).

## 2. Make their page — copy the skeleton

```
cp templates/_teacher.template.html templates/given-family.template.html
```

Then in that file:
- set both `data-teacher="…"` values to the canonical name (the schedule one is the identifier),
- fill every `<!-- EDITORIAL: … -->` region: essence line, portrait, pull-quote, story sections,
  figures, coming-up, social links, audio,
- swap each placeholder image (`src="data:image/svg+xml…Add photo"`) for the real photo.

Tokens fill themselves from the registry: `{{NAME_FULL}} {{NAME_GIVEN}} {{NAME_FAMILY}}` and the
schedule note. You never type the name into the chrome.

## 3. Build

```
python3 build_profiles.py
```

Produces `given-family.html` at the repo root (Netlify's publish dir). Templates beginning with
`_` are skipped. A teacher with no classes yet builds fine — the schedule reads "coming soon".

## 4. Go live

Link the new page from `index.html` when you're ready. Until then it's built but unlinked.

## Rules to remember

- **Edit the template, never the built `.html`** — the next build overwrites it.
- **`partials/base.css` is shared** — change it once to restyle every profile.
- The build is only needed when a template or `schedule.json` changes.
