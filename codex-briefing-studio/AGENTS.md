# Briefing Studio for Codex

This is an independent video composition project. Its outputs do not use the
parent application's Tasks or pipeline. Read `STUDIO.md`, `FACTS.md`, and
`CREDITS.md` before changing the film.

## Start another film

1. Write the question, audience, evidence, and ending in `content/brief.md`.
   Research numerical claims from primary sources. Keep assisted performance,
   independent performance, retention, and transfer distinct when applicable.
2. Write concise narration in `content/narration.json`. A shot must have enough
   time for speech and a readable hold. Keep qualifications in the spoken and
   visible argument.
3. Compose objects and camera keys in `src/film.mjs`. Reuse the physical
   primitives from `src/engine.mjs`: a continuous board, pinned cutouts,
   graphite facts, blue measurements, and earned red judgments.
4. Generate speech directly through `scripts/speech.py`. Preserve provider job
   IDs, request bindings, original WAVs, and all rejected candidates. Resume
   existing requests. A new seed creates a separately reviewed candidate.
5. Run independent transcription, render stills, inspect the actual images,
   and correct collisions before encoding. Never infer visual quality from
   successful rendering.
6. Render picture, then mix verified speech, timed captions, original music,
   and material sounds. `captions.mjs` refuses a picture whose timing changed.
7. Decode the final film, compare every frame, and visually inspect the
   resulting consecutive-frame sheets. Record the actual inspected ranges,
   image scale, full-resolution checks, defects, and revisions. Metrics do not
   establish subjective identity.
8. Verify encoded frame count, timestamp cadence, duration, audio levels, and
   browser playback. Check the local showcase and package the result.

The commands are in `README.md`. Keep generated media in ignored directories,
and keep credentials outside the project. Stage only this work and follow the
parent repository's commit rules.

## Acceptance and publication

Use source-bound evidence. A generated atlas is not an inspected atlas; a
successful decode is not a listening review; a saved social draft is not a
public post. Record these separately.

Publish only within the user's authorized destination and scope. Verify the
public account, exact article or post, final media, and advancing playback.
Keep publishing state in `article/publication.json`.
