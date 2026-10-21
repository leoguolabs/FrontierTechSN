# Briefing Studio

An independent, reproducible engineering briefing video project made with Codex.
The first film is **Does AI Help You Learn—or Just Finish?**

Delivered: 2:41, 1920 × 1080, 24 fps, 3,866 frames, fourteen Chatterbox
segments, nineteen line-drawn people, and a hand-drawn Turkish flag.
Read the [inspection result](review/RESULT.md) for exact coverage and remaining
style differences. The [English process article](https://x.com/LeoGuoLabs/article/2112736076549026024)
includes the complete film.

The current delivery is revision 2: adaptive camera exposure, matte magnets,
worn stamps, restrained ink, and a continuous closing pullback. Every encoded
frame was reviewed again; 24 frames were additionally inspected at 1080p.
The original published film and ZIP remain in the local revision archive.

Open the local gallery at **http://127.0.0.1:8249** after starting the viewer:

```sh
cd codex-briefing-studio
npm ci
python3 scripts/serve.py
```

The gallery includes the film, chapters, reference comparison, frame stepping,
complete frame atlases, live Canvas composition, and the production article.

## Re-render the delivered film

The delivery ZIP includes the accepted speech, transcription observations, and
cutout asset. After installing Node/Python dependencies and FFmpeg, run:

```sh
npm run render
python3 scripts/mix_audio.py
python3 scripts/verify_delivery.py
```

These commands use the retained audio and do not contact Chatterbox. The private
working folder retains provider request checkpoints; the portable ZIP omits
those checkpoints. Do not run the speech-generation step merely to view or
re-render an already delivered film.

## Produce the film

Requirements: Node.js, FFmpeg/ffprobe, Python 3.11 with NumPy and Pillow; MLX Whisper
for speech verification on Apple Silicon. Chatterbox credentials remain outside
this folder.

From this folder:

```sh
python3 -m pip install -r requirements.txt
python3 scripts/fetch_assets.py
python3 scripts/speech.py --frontier-config
python3 scripts/check_speech.py
npm run stills
npm run render
python3 scripts/mix_audio.py
python3 scripts/analyze_frames.py media/does-ai-help-you-learn.mp4 --name final
python3 scripts/compare_frames.py
python3 scripts/verify_delivery.py
npm run validate
```

In this checkout, the parent's `.venv/bin/python` has the required Python
dependencies. Use `../.venv/bin/python` in place of `python3` where needed.
Outside this repository, omit `--frontier-config` and set `CHATTERBOX_TTS_URL`
and `CHATTERBOX_TTS_API_KEY`.

The retained delivery folder also contains the generated cutout at
`assets/photos/notebook-cutout-v1.png`. Copy that asset with the project; Git
excludes generated media. Its prompt and hash are in `assets/notebook-cutout.json`.
Do not silently substitute a different image when reproducing an accepted film.

The final mix requires all narration WAVs. Preserve `media/audio/` when
resuming: the speech client follows existing provider jobs rather than submitting
replacement jobs.

For a mispronounced segment, use `speech.py --only 08 --seed-offset 1000`
(and the same endpoint configuration). This creates an isolated candidate.
After the initial run completes, `adopt_speech.py` verifies the candidate before
updating the manifest. Accepted repairs remain selected on later speech resumes.
Keep the original WAV, candidate WAV, provider receipts, and ASR observations.
For unwanted speech strictly after the complete script, `trim_speech.py` can
retain an exact PCM prefix as a candidate. Select the boundary from word timing
and the waveform's pause; adoption still requires fresh transcription.

## Layout

| Path | Purpose |
|---|---|
| `src/engine.mjs` | Reusable physical board renderer |
| `src/film.mjs` | Original composition, camera, and shared timeline |
| `src/exposure.mjs` | Adaptive half-frame exposure with bounded sample spacing |
| `content/narration.json` | Narration with claim boundaries |
| `scripts/` | Fetch, speech, transcription, rendering, mix, decode, validation |
| `media/` | Local film, sound, poster, and provider records; ignored |
| `reference/` | Local credited reference film; ignored |
| `review/` | Inspection ledgers and delivery measurements |
| `article/` | English production article and publication record |

Read [STUDIO.md](STUDIO.md) to build another film,
[FACTS.md](FACTS.md) for the evidence, and [CREDITS.md](CREDITS.md) for provenance.
No FrontierTechSN application task is created.
