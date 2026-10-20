# Codex Whiteboard Studio

An independent, editable whiteboard film studio built for Codex.

First production: **Does AI Help You Learn—or Just Finish?**

The visual reference is LemoLab's *Einstein in Your Pocket* from
[lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar), revision
`b5e8ef93930b6d828f352055a689320f138237b1`. Reference film and stills are
CC BY 4.0. This project uses an independently written renderer and story.
Third-party fonts retain their own licenses. Production status and review
coverage are recorded explicitly; a technical check is not a quality verdict.

No FrontierTechSN task is created or modified. Chatterbox is accessed as an
audio service with resumable, source-bound requests.

## Layout

- `src/`: deterministic whiteboard renderer and film composition
- `src/illustrations.mjs`: reusable learners at a desk, thinking learners and
  a hand-drawn Turkish flag; every contour uses the timed pen engine
- `scripts/`: rendering, speech, sound design, and complete-frame analysis
- `content/`: director brief, narration, source claims, shot plan
- `fonts/`: licensed stroke lettering and subtitle type
- `assets/`: licensed instrument recordings and their source hashes
- `media/`: local audio, previews, and delivery videos (ignored by Git)
- `reference/`: original reference media (ignored by Git)
- `review/`: measurements, comparison evidence, and revision log
- `article/`: the process article and publication receipt
- `editions/long/`: full-length narration, source ledger, media and review
- `src/long-film.mjs`: the full-length composition on the shared drawing engine

## Run the showcase

From this directory:

```sh
python3 scripts/serve.py
```

Open <http://127.0.0.1:8246/>. The ordinary MP4 in `media/` also plays without
the showcase. The frame lab pairs moments by visual function; its mapping
is declared in `content/comparison.json`. It does not compare unrelated
images as if they should be pixel-identical.

## Rebuild locally

The production environment is Apple Silicon macOS, Python 3.11, Node 24 and FFmpeg 8.
The renderer uses Node Canvas and FFmpeg. Speech review uses MLX Whisper
on Apple Silicon. Install FFmpeg separately if it is not on PATH.

```sh
npm ci
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

The licensed fonts and sampled paths are included. To regenerate the
stroke-font data:

```sh
npm run fonts
```

For speech, configure `CHATTERBOX_TTS_URL` and `CHATTERBOX_TTS_API_KEY` in
the process environment. Do not save credentials in this directory.
The client uses the service's `/v1/capabilities`, `/v1/jobs` and
`/v1/jobs/{id}/audio` interfaces. It retains checkpoints and source hashes.

```sh
.venv/bin/python scripts/speech.py
.venv/bin/python scripts/transcribe.py
```

When this folder is inside FrontierTechSN, `--frontier-config` reads the
parent application's existing service credentials. It does not call the
task API or import the production pipeline.

A bounded narration repair preserves every other audio row:

```sh
.venv/bin/python scripts/speech.py --only 03,09
.venv/bin/python scripts/transcribe.py
```

For a confirmed synthesis fault with unchanged narration, record the line's
source SHA-256, replacement seed and reason in `content/speech-repairs.json`.
The speech client applies that source-bound override on every resumption,
retains prior provider requests and allows at most three distinct takes per
line and source. A local writer lock prevents competing manifest updates.
Before submitting any selected line, the client checks the whole selection
against the service's advertised character limit.

Build from the current, reviewed local audio:

```sh
.venv/bin/python scripts/build.py
```

The build validates source/audio bindings, independent transcription,
pen queues, captions and layout; renders the picture; composes sampled music
and foley; mixes the film; exports captions and poster; verifies the
encoded file; then generates complete-frame evidence. It stops on a failed
check. To request generation or resumption of speech as well, use
`scripts/build.py --speech`.

These commands generate evidence. They do not automatically establish
visual acceptance or subjective listening quality.

## Development and review

```sh
node scripts/render.mjs --stills
node scripts/render.mjs --draft --start 0 --end 18 --out media/opening.mp4
node scripts/validate.mjs --draft
node scripts/inspect_motion.mjs --edition long
.venv/bin/python scripts/analyze_frames.py media/opening.mp4 --out review/opening
```

Draft mode allows missing audio and estimated durations. A final render
requires current audio for every narration row. Captions in a final build
must use source-bound independent ASR timing.

The motion inspector checks conservative marker-body rectangles at every
frame and reports candidate intersections. Inspect the rendered intervals
before accepting a fix; an empty candidate list does not establish visual
quality. The long composition declares local marker handoffs in
`src/long-film.mjs`. Its scheduler preserves each pen's drawing order while
allowing time for one pen to leave before another approaches.

Keep a reference film at `reference/whiteboard.mp4` for the comparison lab
and paired atlases. The exact source is:
<https://github.com/lemomo-ai/lemo-opuscar/releases/download/films/whiteboard.mp4>

```sh
.venv/bin/python scripts/analyze_frames.py reference/whiteboard.mp4 --out review/reference
```

See [STUDIO.md](STUDIO.md) for the authoring and acceptance procedure,
[CREDITS.md](CREDITS.md) for licenses, and [review/revisions.md](review/revisions.md)
for observed failures and repairs. The process article is a local HTML
document in `article/`; its publication state is recorded in
`article/process.json`.

After actually inspecting each paired atlas, record its number and observation:

```sh
.venv/bin/python scripts/record_review.py --sheets 0-3 --note "Observed details and issues."
.venv/bin/python scripts/record_review.py --stills 1-19 --note "Full-resolution observations."
```

This command records an inspection; it does not perform one. Finalization
requires every atlas and binds the review to the exact encoded video:

```sh
.venv/bin/python scripts/record_review.py --finalize
.venv/bin/python scripts/export_project.py /absolute/path/to/empty/delivery-folder
```

## Delivery boundaries

Generated videos, provider WAVs, atlases and raw measurements remain local
and are excluded from Git. Source and curated evidence are versioned.
The final delivery is also copied into the user's lemo-opuscar clone under
`films/codex-whiteboard-studio/`, with the reference attribution retained.

The three-minute edition was accepted in principle and its illustrated
refinement has been delivered. The full-length edition is in production.
Public X delivery has a
separate publication receipt; a draft article is not a published post.

## Illustrated edition

The user accepted the first short in principle and requested people and
recognizable place cues. The revised short replaces several generic document
icons with a learner using a laptop, answering an exam and making a first
attempt. Thinking learners carry the physics and cognitive-offloading scenes.
A red-hatched Turkish flag locates the mathematics study.

Black, blue and orange remain the explanatory palette. Red is used for the
flag, with board-white crescent and star preserved between the strokes. The
people are illustrative figures, not depictions of actual study participants.
Use poses and objects to explain the script; avoid filling every empty space.

The first delivered edition, including its exact film, source and review
evidence, is retained in the export folder at `versions/01-reviewed-short/`.

## Full-length edition

Every build and review command defaults to the short edition. Add
`--edition long` to use the separate long-edition artifact directory:

```sh
.venv/bin/python scripts/speech.py --edition long
.venv/bin/python scripts/transcribe.py --edition long --follow
node scripts/validate.mjs --edition long --draft
node scripts/render.mjs --edition long --stills
.venv/bin/python scripts/build.py --edition long
.venv/bin/python scripts/record_review.py --edition long --sheets 0-3 --note "Actual inspection."
.venv/bin/python scripts/record_review.py --edition long --finalize
```

The final long movie is named `does-ai-help-you-learn-long.mp4`; its measured
duration is authoritative. Fonts, instrument samples and the reference
remain shared. Provider WAVs, captions, picture, sound and acceptance records
are edition-specific. Do not run two speech writers for the same edition.

The showcase enables its edition selector when the long edition's complete
delivery record exists. To include both reviewed editions in the export:

```sh
.venv/bin/python scripts/export_project.py /absolute/path/to/delivery-folder --include-long
```

This command rejects an edition whose current video has not passed its own
technical and complete-frame review.
