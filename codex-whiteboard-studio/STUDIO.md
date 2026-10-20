# Working in Codex Whiteboard Studio

This project is a complete local production, not a frontend for the
FrontierTechSN task pipeline. Keep its scene code, audio jobs and review
artifacts inside this directory. The only optional parent-app integration
reads the existing Chatterbox URL and key.

## Making a new film

Start with a question the audience can answer differently after watching.
Write the argument, primary-source claims and an explicit limitation before
drawing. Put finalized narration into `content/narration.json`. Each row has a
stable ID, a board region, text and a claim reference.

Keep lines below the provider's reported character limit. Generate speech
at natural speed. Preserve the exact request, provider job, voice fingerprint
and original WAV. A changed line gets a new request identity; it must never
silently reuse the old audio. Use `--only` for a bounded repair.

`src/board.mjs` is the reusable drawing engine. It provides single-line
lettering, pressure ribbons, dry ink, primitive shapes, physical props,
single-pen stroke queues, erasing, inverse-scale camera interpolation and
caption rendering. `src/film.mjs` is this film's editable composition.

Place the entire argument on one board. Every drawing has a unique ID.
Use black for explanation, blue for support and terracotta for independent
work. Give each physical pen one chronological queue. `Score.compile()`
serializes overlaps, but the director must check whether the resulting
delay still fits the spoken idea.

Direct the camera to the current relationship. Revisit earlier drawings
when the argument depends on them. Readable holds matter as much as writing.
Use the final wide view to reveal how the ideas connect.

The timeline is derived from actual provider durations. Captions preserve the
finalized source wording and use independent ASR observations for their timing.
Rendering and sound use the same serialized timeline and event list. The mux
rejects a picture whose hashes no longer match those inputs.

## Reviewing a film

First inspect selected full-resolution stills. Fix layout and drawing
mechanics before spending time on the final render.

Then inspect motion. Decode the complete video with `analyze_frames.py`.
It writes one metric row for every frame and consecutive-frame atlases.
`compare_frames.py` pairs every candidate frame with a reference frame using
the declared visual-function mapping in `content/comparison.json`.

For every atlas actually inspected, record the exact sheet name and frame
range. Record original tile size and displayed size. An overview image does
not count as complete-frame inspection. Generating a report does not count
as reviewing it. Open suspect frames at full resolution and review the
surrounding frames again after a repair.

Inspect pen contact, lifts, arrivals and departures; stable ink coordinates;
eraser footprint and continuity; camera acceleration and blur; text margins,
reading time and subtitle placement. Reference and candidate have different
stories, so a pixel-difference score cannot establish stylistic equivalence.

Check the final encoded artifact, not only its picture intermediate.
`verify_delivery.py` checks every timestamp, full decode, loudness, peaks and
the placement of every voice line. Independent ASR and waveform checks do
not establish subjective listening quality. Record actual playback and
listening coverage separately.

## Reproducibility and handoff

Keep source, dependencies and curated review notes in Git. Keep provider
audio, videos, measurement CSVs and atlases in the local delivery package.
Do not include credentials or session data in either package.

The local showcase provides the film, chapters, frame stepping, functional
reference comparison and source links. Its comparison function is shared
with the production mapping. The film remains an ordinary MP4 that plays
without the showcase.

When a user asks to approve a short edition before a long one, finish and
review the short edition first. Keep the long edition and public process
article as separate remaining deliverables until that checkpoint is approved.
