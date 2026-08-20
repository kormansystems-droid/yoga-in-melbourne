# Names and spellings — corrected 19 August 2026

The 14 August handover listed four spellings in the Shelley Armstrong draft that
Mark had to verify. Three are now settled by him. This note exists because the
draft they came from was **delivered to Mark in chat and never committed**, so
when the container was reclaimed the only surviving record of the corrections was
a four-item list with no sentences around it. Corrections belong in the repo.

## Settled

| Was written | Correct | Notes |
|---|---|---|
| Tattva Yoga, Rishikesh | **Tattvaa Yoga** | double A |
| — | **Sattva Yoga Academy** | Mark added this on 19 Aug; it was not in the original list, so it is either a second school in her story or a correction of the first. **Confirm which before publishing** — they are two different institutions and conflating them would put her in the wrong place. |
| Kat Kabira | **Cat Kabira** | C, not K |

## RESOLVED 20 August: "Yoga Haven"

Her interview was transcribed on 20 Aug and the answer is at **[02:15–02:28]**:

> "I saw a flyer for a teacher training that was a London based training. It was a
> Vinyasa school... So I decided to go and train with that school, **Yoga Haven**."

**Yoga Haven is the London vinyasa school where she did her first teacher training
in 2009** — her original qualification, before the Ashtanga 200-hour in Rishikesh.
Not Bali, not India. The Bali hypothesis below was wrong, and the reasoning that
produced it was the kind that sounds convincing and is worth nothing next to
nineteen minutes of the person's own voice.

The transcript is now at `transcripts/shelley-armstrong-interview.md`.

## What the guess was, and why it stayed a guess (kept as the record)

Mark cannot place it, and neither can I. The handover records it flat, in a list
of four, with no sentence around it. The draft that used it is gone. **This is
the "delivered as a file, not committed" rule producing exactly the loss it warns
about** — a fact was checked, the check was recorded, and the thing being checked
was not.

Do NOT guess it. The adjacent names in the same paragraph are Rishikesh schools
and Cat Kabira, who teaches in Bali, and Sally's account has Shelley arriving from
Bali — so a Bali studio is the *hypothesis*. It is only that. Searching for a
plausible "Yoga Haven" and fitting it to her would be inventing biography.

**How it was settled:** transcribed in the container on 20 Aug using the Whisper
model already sitting on Mark's own disk. The container's proxy blocks HuggingFace,
so downloading a model was never possible — his `_transcribe/` folder had one,
split into 62 MB chunks, which staged inside the per-call limit and reassembled
byte-exact. Two fixes were needed: CTranslate2 wants a `vocabulary.json` that
MacWhisper does not ship, and a vocabulary rebuilt from `tokenizer.json` alone is
short by exactly the 1,501 timestamp tokens (50,363 instead of 51,864), so the
model rejects the first timestamp it tries to emit.

## Probably settled by the events feed: Phoebe's surname

The same handover asked for **Phoebe's surname for the Grass Roots piece**. The
Momence feed for Grass Roots St Kilda returned, on 19 Aug:

> 75min Energy Balancing Sound Bath with **Phoebe Dubar** (IKSRE) — 11 Sep,
> Grass Roots St Kilda, $45

Same studio, and IKSRE also appears in Warrior One's programme. **Likely the same
Phoebe, not certain** — confirm with Grass Roots before it goes in an article.
Worth noting the mechanism: a booking feed built for timetables answered an
editorial fact-check. Worth checking the feeds first for any name question.

## The standing rule this is an instance of

A transcript, a draft and a fact-check are all source material. Delivering them
as files puts them on Mark's disk and nowhere a future session can reach. Four
interview transcripts and two article drafts were lost this way on 14 August.
**Transcripts belong in the repo**, under `transcripts/`, alongside the notes.

## Also resolved 20 August: where she emailed from

The transcript settles the Sally-versus-Shelley conflict. In her own words
**[06:01–07:45]**: she left London in 2013, went to India, travelled, contacted
Melbourne studios *"from a little room I was staying in in **Thailand**"*, landed in
December 2013, and was teaching at Grass Roots *"about four days after I got off
the plane."*

So: **Thailand, not Bali.** Sally's recollection is wrong on the country. Both
drafts were written to avoid contradicting each other; they can now simply be
correct. Mark may still want to check with Sally rather than silently overruling
her, since it is her memory of a friend's arrival.

## Still open: Sattva Yoga Academy

Mark supplied this name on 19 Aug. **It does not appear anywhere in the
interview** — the only Rishikesh school she names is Tattvaa. So either it is a
training she did not mention on tape, or it was offered as a correction to
Tattvaa. Do not put both in an article on the assumption that she did two.
