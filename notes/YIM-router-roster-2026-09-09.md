# Zoe Kanat in the homepage router, and the roster's source of truth

**9 September 2026.** Built and verified. Not yet committed: Chrome was not
connected to the session, so the four files are delivered for you to upload.

---

## Conclusion

**The homepage router now lists every teacher with a published page, because it
reads the roster from the templates rather than from `schedule.json`.** Zoe Kanat
appears for the first time. Her vignette was also recropped, because the default
crop reduced her to a smudge at the size the router actually renders.

The one-line version: the router was answering "who has classes we pull?" when
the question is "who has a page?"

---

## What was actually wrong

`build_index()` built the teacher column from `data["teachers"]` in
`data/schedule.json`. That list is produced by the nightly pull from studio
feeds, so it contains exactly the teachers who have studio classes.

**Zoe is the first published teacher who has none.** She teaches online and on
Insight Timer, so there is no studio timetable to pull and she correctly appears
nowhere in `schedule.json`. Her page is generated, approved and live, and it is
linked from the Teachers grid and the podcast feature, but there was no line for
her in the router.

This is the same failure the function was written to prevent. The docstring
already records it: Steph Philip and Ryan Mannix both went live with working
pages and no route from the homepage, because a human had to remember to add a
line. The fix at the time was to generate the list. The generated list just had
the wrong source.

**`build_one()` already knew about this case.** It has handled online-only
teachers since Zoe's page was built: a template whose `data-teacher` is absent
from `schedule.json` gets an empty schedule slot rather than a crash. So one half
of the script understood that a teacher can exist without a timetable and the
other half did not. They now read the same source.

| | Before | After |
|---|---|---|
| Roster source | `schedule.json` teachers | `templates/*.template.html` |
| Name from | the JSON key | the template's `data-teacher` |
| Href from | slug of the name | the template filename |
| Teachers listed | 10 | 11 |

Taking the name from `data-teacher` rather than title-casing the filename
matters for the standing rule that the person decides how her name is spelled: a
slug cannot carry an apostrophe, an interior capital or a lowercase particle.
Taking the href from the filename guarantees every link points at a page the
script actually generates.

**This fixes the class of bug, not the instance.** The next teacher who teaches
only online appears in the router the day her page does, with no one having to
remember anything.

---

## The vignette

Her photograph is a full seated shot, head to feet, taken well back. The default
crop is a square the full width of the source, anchored 6% down, which for her
takes in the sofa, the planting and the fence and lands her face at roughly 15%
of the frame.

That is legible in a 160px contact sheet and a smudge at the **44px the router
renders**, beside ten faces that read clearly. In a column deliberately designed
to give every teacher identical prominence, one unreadable circle is not a
neutral defect.

Added a `CROP` override: `(0.534, 0.215, 0.46)`. Tested four boxes; 0.36 and 0.42
clipped the top of her head, 0.55 read as another wide shot.

**This is a different failure from Janita's, and the comment in the file now says
so.** Janita's problem was horizontal: her face sits 58% across a wide frame and
no vertical anchor could reach it. Zoe's is scale. They look alike in a contact
sheet and want different fixes.

---

## Verification

Against the artefact, not the success message.

| Check | Result |
|---|---|
| Pulled fresh `main` first | At `28d4643`, this morning's nightly |
| Router block diff | **Exactly one line added.** Nothing else moved |
| Repo diff | Only `build_profiles.py`, `build_vignettes.py`, `index.html`, `img/vig/zoe-kanat.jpg` |
| All 11 teacher pages | Regenerated **byte-identical**. No page regressed |
| Second build run | `index.html` md5 unchanged. **Idempotent**, so the nightly will not churn it |
| Other 10 vignettes | Regenerated **byte-identical** after the `CROP` edit |
| Rendered at 390px and 1440px | Zoe's link present, face legible, matches the other ten |
| Zoe's page | Still builds with an empty schedule slot, unchanged |

**The byte-identical checks are the point.** The last vignette change put ten
broken images live because a change that needed twelve files was described as
needing two. Regenerating everything and proving only the intended file moved is
the guard against repeating that.

---

## The nightly constraint holds

`pull.yml` installs playwright and nothing else, and `pull.py` runs
`build_profiles.py` with `check=True`. **`build_profiles.py` still imports no
image library.** It reads template text and checks whether a file exists on disk.
`build_vignettes.py` was run by hand, as it must be.

One thing worth naming: `build_index()` now raises if a template lacks a
`data-teacher`, and it runs before the template loop. `build_one()` raises on the
same condition for the same templates, so this is not a new way for the nightly
to fail; it just fails a few lines earlier.

---

## What has not changed

**The Teachers grid stays hand-curated.** The router is navigation and lists
everyone with a page; the grid is a showcase and carries a portrait and a
standfirst only for a teacher who has said yes to a profile. Generating the
router does not generate the grid, and should not.

**The editorial firewall is untouched.** Nothing here is a coverage decision. The
router lists people who already have approved profiles; it changes how they are
found, not who gets published.

**No league table.** The sort is still alphabetical by given name. Zoe is last
because of the letter Z, not because of anything about her.

---

## Assumptions, flagged

1. **That Zoe belongs in the router at all.** The original docstring justified a
   listing as "a reader looking for her timetable should find it", and she has no
   timetable. I have taken your instruction as settling this and rewritten the
   rationale to "a reader looking for a teacher should find her", which I think is
   what the router became when it grew faces and moved to one name per line.
   Challenge this if you meant something narrower.
2. **That the templates directory is the roster of published pages.** True today:
   11 templates, 11 generated pages. It stops being true if a page is ever
   hand-written without a template, which nothing currently does.
3. **That 0.46 is the right crop.** Judged at 56px against the other ten, which is
   the instruction in the file. It is a taste call and easy to change.

---

## Open questions

| Question | How to check | When |
|---|---|---|
| Does Zoe's row get clicks? | GSC and any click tracking on `/zoe-kanat.html` referred from `/` | 30 days after commit |
| Does an online-only teacher's page convert without a timetable? | Compare her page's engagement to Shelley's, who has four classes | Once there is traffic |

---

## Still outstanding from yesterday

- The three notes from 8 Sep are still uncommitted: search baseline, retreat
  brokerage, Instagram handles
- Emma's studio handle, so her caption stops shipping with a blank: Within,
  Happy Melon or Kozen Yoga
- Rayne's high-resolution selfie, if she finds it
- Instagram safe margins into `build_solo_reel.py` and `build_podcast_reel.py`:
  offered, not yet authorised
