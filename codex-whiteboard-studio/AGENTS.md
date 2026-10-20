# Working in this studio

Read `STUDIO.md` before changing the film. The production source is
`content/narration.json` and `src/film.mjs`; the reusable drawing engine is
`src/board.mjs`.

Keep narration, picture, captions and sound on the same serialized timeline.
Retain provider requests and original WAVs when repairing speech. Do not
silently replace a failed line with another voice or alter its playback speed.

Use `scripts/build.py` to produce the encoded film and technical evidence.
Inspect every consecutive-frame comparison atlas, record its exact range,
and reopen questionable frames at full resolution. Generated atlases are
evidence to inspect, not proof that inspection happened. Never represent
ASR or waveform checks as subjective listening.

The reference is licensed material for style study and comparison. Its
credits must accompany the reference video and extracted frames. New films
use the independent renderer here; do not import the reference engine.

The current short edition is the review checkpoint requested by the user.
The twelve-minute edition starts after their approval. A prepared X article
is not a published article; retain publication state and a verified URL.

Generated media and review atlases stay out of Git. Commit only scoped
source, licensed reusable assets, documentation and compact review records.
