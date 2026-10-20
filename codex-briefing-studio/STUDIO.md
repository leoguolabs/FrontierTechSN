# Briefing Studio production guide

This is a standalone film project. It uses Canvas for picture, Python for
speech verification and sound, and FFmpeg for encoding. The browser gallery is
a read-only viewer with chapter navigation, two-film frame stepping, complete
frame atlases, and a live composition preview.

## The physical contract

One 6400 × 3600 enamel board holds the entire argument. Screen coordinates are
1920 × 1080. Camera translation, scale, and roll expose local details; they do
not relocate the underlying objects. A final pullback reveals the complete board.

Graphite states facts. Blue measures or connects. Red marks an earned judgment.
Paper, magnets, photographs, and the metal ruler have depth and common shadows.
Ink stays flat. Erased text leaves a faint trace. People and a hand-drawn Turkish
flag carry meaning alongside the numerical evidence.

The camera moves from an object detail to a readable comparison, then holds for
the judgment. Adjacent regions should retain enough of a previous mark to make
the board's geography legible. Large movements use three temporal samples over
a 180-degree shutter interval. Subtitles are drawn after that motion integration.

## The timing contract

`src/film.mjs` creates one timeline from the narration and actual WAV durations.
The exported `content/timeline.json` is consumed by both picture and sound.
Frame zero is the first displayed frame. At 24 fps, event frame `f` starts at
sample `round(f * 48000 / 24)`.

Speech starts six frames into each primary shot. Each shot includes a minimum
visual hold so fast speech cannot erase reading time. Actual ASR word observations
time the captions; transcription differences must be examined before export.

Do not change the narration, voice files, or composition after the final render
without rebuilding the timeline, picture, sound, captions, and review evidence.

## Make another film

1. Write a new argument and source ledger. Keep the main contrast measurable.
2. Replace `content/narration.json`; keep stable IDs and meaningful regions.
3. Recompose `src/film.mjs` using the reusable primitives in `src/engine.mjs`.
   A new topic needs a new layout and camera argument, not a blind text swap.
4. Generate Chatterbox WAVs. The client retains provider job IDs and verifies
   request and audio identity. Re-running resumes the same requests.
5. Transcribe, inspect stills, then render. Inspect motion and the final encode.
6. Generate the complete atlas and update a review ledger only after observing
   its frames. Generated reports and viewed frames are separate evidence.

### A brief Codex can execute

Supply a subject, audience, one question, primary sources, and the intended
duration. Ask Codex to produce a source-backed argument, a board map, narration,
camera poses, event timing, actual audio, the encoded film, and a review ledger.
Use this repository's primitives; the new topic still needs an original layout.

For each beat, specify:

- **Object:** what the viewer can see or recognize before reading a number.
- **Measure:** what comparison the blue line or annotation actually represents.
- **Judgment:** the narrow conclusion the evidence permits.
- **Hold:** the readable interval after the important information settles.
- **Move:** where the camera goes next and what earlier mark connects the regions.

People should do something relevant: attempt, choose, explain, or guide. A flag
establishes a study's location; it does not stand in for the study's participants.
The final pullback should expose one coherent argument, not a collage of cards.

### Local delivery

After the final review, run `python3 scripts/package_studio.py`. The local ZIP
contains the source, generated cutout, accepted speech, final film, reference,
and complete reference/final and paired comparison atlases. Dependency caches, API keys, and private
provider request checkpoints are excluded. The original working directory
retains intermediate renders and all speech attempts for future revision.

## Review honestly

The atlas contains every decoded frame. At 384 × 216 per cell it is useful for
temporal continuity, missing objects, clipping, and reveal order. Full-resolution
frames are additionally needed for small text and material detail. Browser
playback checks establish actual playback, not a listening review.

Different stories cannot have pixel-identical frames. Compare visual function:
material, ink, props, motion, typography, scale, reveal sequence, and legibility.
Do not turn a similarity score or complete decode into a “100% identical” claim.
Record specific differences and revise the film when they weaken the reference
language.

## Independence

The only optional parent-project dependency is `speech.py --frontier-config`,
which reads the existing Chatterbox endpoint and key from configuration.
It does not use task storage, pipeline stages, render services, or application
generation workflows. Environment variables allow the studio to run elsewhere.
