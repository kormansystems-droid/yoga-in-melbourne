# Masha's profile built, Zoe in the router, Spring confirmed deployed

**Monday 21 September 2026, 3:30pm AEST.** Session picking up the 21 Sep handoff.

---

## Conclusion

**Three things are built, verified and pushed to branch `claude/new-session-7jet1a`. None is live.**
Making them live means pushing that branch to `main`, which this session can do on your word
(push access confirmed by dry run against `main`).

| Commit | What | Files |
|---|---|---|
| `db52b14` | Zoe Kanat in the homepage router, from the published pages | `build_profiles.py`, `build_vignettes.py`, `img/vig/zoe-kanat.jpg`, `index.html` |
| `9dc778c` | Masha Gorodilova profile, from her approved copy | `templates/masha-gorodilova.template.html`, `masha-gorodilova.html` |
| `1744b2c` | Five carried-over notes into `notes/` | handles, reel safe zones, router roster, search baseline, retreat brokerage |

**Spring is deployed.** Netlify's production deploy `6ab0bb10` is `ready`, built from `8d350a0`
(your third upload), published 3:05pm AEST. Neither the sandbox nor WebFetch can reach the site
itself (egress policy blocks the domain and the Netlify preview hosts), so this is deploy-level
confirmation, not a render check. If you open the homepage on your phone and see the blossom
hero, it is all there.

---

## Masha

- **Source is the approved artifact (v7)**, not `masha/build.py`, which is an older draft with a
  different headline and the money figures still in it. The story, hero and thesis markup are
  lifted from the preview unchanged; the head, masthead, schedule, coverage note, follow and
  footer are the site chrome every profile carries.
- **Quote check: 30 of 30 passages verbatim and contiguous** against
  `masha/transcript-mark-edited.txt`. Punctuation and Australian spelling inside quotes differ
  as house style allows; no word inside a quotation changed. One passage straddles a timestamp
  marker in the transcript and is contiguous in speech.
- **Photos**: `hero.jpg` (blue portrait) in the portrait frame, `stool.jpg` narrow mid-story,
  `bowl.jpg` full width. Same bytes as the preview.
- **Schedule** renders from the nightly: eight classes at Within, "across one studio". The old
  listing's "Every class Masha teaches, in one place" line is gone with the listing template.
- Page is 771 KB, no em dashes, no leftover tokens, no `noindex`. Rebuilt twice: byte-identical.
- **Her Instagram handle is still not recorded.** Ask her. Do not guess.
- **The eyebrow reads "Masha Gorodilova · Conversations"**, as approved. There is no podcast
  episode on the page. Kept as she saw it; your call whether "Teacher" fits better.
- **She is not in the Teachers grid** on the homepage. The grid is hand-curated for approved
  profiles, so she now qualifies. Not done: it needs a portrait crop, a category line and a
  one-line standfirst, and I did not want to write a standfirst she has not seen.

## Zoe

- Re-applied against fresh `main`, not the stale bundle. The two scripts from the bundle were
  a clean diff against the repo, so they were copied over; `build_vignettes.py` was then run
  here with Pillow, and the only vignette that changed is Zoe's, byte-identical to the previous
  session's build.
- `index.html` diff is exactly one router row. The other ten pages rebuilt byte-identical.
- Router rendered over HTTP at 390px: eleven faces, all load, Zoe legible.
- `build_profiles.py` still imports no image library, so the nightly is unaffected.

---

## Decisions for you

1. **Push to `main`?** Everything above goes live in one push. Say "make it live" and I will.
2. **Masha in the Teachers grid**: yes or no, and if yes, whether you want to write the
   standfirst or have me draft one for her to approve.
3. **Homepage copy**: "Find a teacher: every class they teach" is close to the forbidden phrasing.
   Not changed. Your call.
4. **Reel tools**: the bundle's `build_reel_video.py` and `build_solo_reel.py` are newer than the
   repo's, and `build_podcast_reel.py` and `build_article_reel.py` are not in the repo at all.
   Not committed. They are outside the nightly, so no workflow risk. Offer stands.
5. **Warrior One reply** to Kim (`notes/warrior-one-mindbody-reply.md` in the bundle) was not
   committed: it is a draft email, and the repo is public.
6. Offered, still not authorised: nightly refill of Journal teacher panels; a dated availability
   mechanism for retreat spots (Masha's Sri Lanka guest spot would be the first use).

---

## Assumptions, flagged

- **That the v7 preview in the bundle is the version Masha approved.** The handoff says so and
  the file matches the headline it records. Not independently verified against the artifact
  URL, which this sandbox cannot open.
- **That the session branch is the right holding place.** The handoff says commit straight to
  `main`; the harness for this session says develop on the named branch. I took the branch as the
  safe default until you say go, because nothing on it is a live change.
- **That Netlify's `ready` deploy at `8d350a0` means the pages are serving.** Deploy state is a
  strong signal, not a render.

## What has not changed

The editorial firewall. Masha's profile publishes because she approved the words; her retreat
spot stays off the profile until there is a dated mechanism for it. Schedule data needed no
approval and got none. Nothing here ranks anyone.
