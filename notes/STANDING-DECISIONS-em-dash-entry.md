---

## House style

**Em dashes are forbidden. Anywhere in the project.**
*Decided 1 Sep 2026.*

Not a preference to weigh against a sentence that reads better with one. Use a comma,
a colon, a semicolon, a full stop, or brackets, and if none of those work, rewrite the
sentence.

Swept to zero on 1 Sep across every page, template, `partials/base.css`, `community.js`,
the Netlify functions and `data/handoffs.json`. Because base.css and the shared
templates are injected into every page, that sweep regenerated all eleven profile and
listing pages.

**The exception, and it is a real one: studio-supplied event titles.** Three sit in
`data/schedule.json` ("Flight School", "Strong Asana", "Go WITH/N to WIN"). They are
another organisation's name for its own event, which is the same principle as the
name-spelling decision: the owner decides. They also arrive from the feeds, so a manual
edit is overwritten on the next pull. If the ban is meant to cover them, it belongs in
`pull/normalizers.py` as a transform on ingest, and restyling other people's titles
should be a conscious choice rather than a side effect.

**Not yet swept:** the Python pipeline, the markdown docs and the older notes. Roughly
250 occurrences, none of which render.
