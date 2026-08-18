# On the Mat announced teachers into classes they were not teaching — 2026-08-18

## Conclusion

`schedule.json` held a weekly pattern with no dates in it, and On the Mat made
dated claims from it. On Wednesday 19 August it would have announced Emma
Strembickyj into three classes while she was overseas, and Shelley Armstrong into
two on her first day on the site. Emma noticed and contacted Mark. Fixed: real
dates now flow from the feeds to the story, and a class is announced only when a
feed confirms it runs that day.

**Settled in the same session: nobody owns a slot.** Rosters churn constantly.
Momence's `originalTeacher` records only that an assignment was edited — it is
bookkeeping, not a fact about the world. It is no longer read anywhere, and the
`substitute` tag it drove is gone from every page. The teacher named is the
teacher. That is the whole model.

## What was actually wrong

`build_story_cards.classes_for()` matched on a weekday string: `if c["day"] != day`.
`schedule.json` is collapsed from a rolling 14-day window, so a class Emma teaches
on Wednesday **26** August produced a row reading "Wed 6:15 PM" — and the generator
asserted it for Wednesday **19** August. No date existed anywhere in the model to
contradict it. `merge.py` had been discarding the date every normalizer already
computed.

This is **not** the "substitution bias" described in earlier notes. The pipeline
attributed those classes correctly to the people teaching them. The story asked
the wrong question of the right data.

## Verified against the live feeds, 18 Aug ~10pm

Wednesday 19 August, every Momence studio queried directly:

| Teacher | Frame claimed | Actually teaching |
|---|---|---|
| Emma Strembickyj | 3 | **0** — Kozen 6:15pm & 7:30pm taught by Fai Mos; no Grass Roots class on the 19th |
| Shelley Armstrong | 2 | **0** — Grass Roots 5:00pm & 6:15pm taught by Tailem Tynan and Nickie Hanley |
| Ryan Mannix | 4 | 4 — correct |
| Sarah Metzger | 3 | **4** — was missing her 5:00pm Port Melbourne Dynamic Flow |
| Alessia Frisina | 6 | 3 verifiable (Within); 3 at Warrior One unverifiable, feed dark |

Across Grass Roots, Kozen, (Here) and Good Vibes on the 19th, the only YiM names in
the feed were Ryan and Sarah.

## The corrected line-up

Wednesday 19 August: **11 classes, 3 teachers, 7 frames** — Sarah Metzger (4),
Ryan Mannix (4), Alessia Frisina (3, all at Within). Delivered to Mark as files.

## Decisions taken

| Decision | Ruling |
|---|---|
| Class a teacher isn't teaching that day | Does not appear. Anywhere. |
| Teacher covering someone else's class | Appears, named, untagged — it is her class that day |
| Feed can't confirm a date (dark or undated) | **Silence.** Never announced in the daily story; still shown on profile pages as a weekly timetable |
| `originalTeacher` / `substitute` tag | Dropped entirely |

## Shipped to main

| Commit | What |
|---|---|
| `e98e7f5` | `_row()` emits `date`; `merge.py` keeps `dates` per row; `originalTeacher` and `sub` removed from every normalizer; `pull/test_dates.py` added |
| `848f982` | `classes_for()` takes a date and filters on it; `substitute` tag removed from profiles and story cards |
| `2aecefb` | Auto-refresh — first `schedule.json` carrying real dates (53 dated rows, 21 undated) |

`pull/test_dates.py` is a regression test reproducing the Emma case exactly. It
asserts she is **not** announced on the 19th and **is** on the 26th. Run it before
touching the story generator.

## Numbers worth keeping

- Warrior One Brighton, Warrior One Mordialloc, Happy Melon Armadale: **26 consecutive
  failed runs since 27 July** — three weeks dark. All three are the `gomindbody` adapter.
- Undatable rows by teacher: Alessia 7, Rayne 5 + 2, Steph 4, Sarah 3. Emma, Janita,
  Ryan and Shelley have none.
- **Rayne Watkin has zero date-confirmed classes.** Every class she has is at Warrior
  One or Inndriya. She cannot appear in On the Mat at all until Mindbody activation
  lands or Inndriya starts publishing dates.

## Open questions

- **Rayne's absence from On the Mat.** Check after Mindbody activation. Until then she
  is invisible in the daily story while remaining on her profile page — she may notice
  before we tell her.
- **Stale frames in the repo.** `story/2026-08-19-tomorrow/` on `main` still holds the
  nine wrong frames from the 7pm run, including `frame-04-emma-strembickyj.png`. The
  GitHub web UI cannot delete them in bulk. Delete before anything reads that folder.
- **`captions.md` calls Ryan Mannix "she"** in the per-frame notes — the template is
  hardcoded feminine. Internal only, but wrong.
- **Sarah's Mordialloc classes** — still unresolved, unrelated to this.

## Assumptions flagged

- **Measured:** every figure above came from querying the Momence read-only API
  directly (hosts 34431 Grass Roots, 44752 Kozen, 40780 (Here), 33014 Good Vibes)
  on the evening of 18 Aug.
- **Inferred:** that Alessia's three Within classes on the 19th are correct. Within's
  healcode feed is healthy and dated, but it was not independently checked tonight.
- **Not verified:** Warrior One and Happy Melon rows. Dark for three weeks. They are
  excluded from the story by the new rule rather than judged.
- **Unchanged:** the editorial firewall. Aggregated schedule data is factual and needs
  no approval; a profile still requires an interview and her yes; coverage is never for
  sale. Nothing here touches that. What changed is that the factual claim is now
  actually factual.
