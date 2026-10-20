# Revision log

## Internal layout pass 1

Observed: stroke font scaled by cap height instead of units per em. Titles,
labels and equations were too large and clipped. Repeated translucent line
segments created regular dark joints in the ink.

Changed: normalize glyphs by units per em; paint each stroke as one pressure
ribbon; retain dry streaks. Reframed the study and counterexample regions.
Replaced a large closing circle with a fitted ellipse.

## Internal layout pass 2

Observed: a reused drawing ID could substitute an unrelated cached heading.
Stroke arrays followed authoring order, so marker position could disagree with
the visible stroke. Several groups competed for the same physical pen.

Changed: reject duplicate drawing IDs; sort all strokes chronologically;
serialize each pen's queue. Move directional arrows clear of the percentages.
Keep the board's left edge outside the study camera frame.

## Reference comparison pass 1

Observed: pen bodies and shadows were smaller than the reference close-ups;
the base board was slightly too bright; two-line caption cards occupied more
space than the reference's short clauses.

Changed: enlarge pen scale by 1.27; increase cast-shadow offset/softness;
lower surface brightness; use single-line caption clauses; derive caption
timing from independent ASR observations while preserving source text.

## Audio review in progress

Two unprompted recognizers read line 03's final “changed problem” as “change
problem.” Preserve the original provider job and waveform; repair the bounded
line before accepting the final audio. No claim of listening follows from ASR.

## Continuous motion comparison

The complete development picture contained 4,346 frames. All were decoded
and paired by scene function; visual development inspection covered paired
atlases 0000, 0008, 0011, 0046, 0062 and 0080–0083, plus scene stills.
This is development coverage, not the final film's acceptance record.

Observed: the title had too little hierarchy; several long sections held
the same framing; the first magnet appeared abruptly; the eraser jumped
between rows. A closing wide shot exposed part of a neighboring box.

Changed: enlarge the first title line, narrow its ink, add small reframes
as arguments develop, animate the magnet from outside the frame, and use
one continuous serpentine eraser path. The erase mask follows the physical
eraser footprint and leaves a faint trace. Reframe the closing question.
Both consecutive-frame atlases of the 74-frame eraser revision were
visually inspected. The final full-film review must cover these changes again.

## Sound texture

Replace synthesized music instruments with three independently sourced CC0
instrument recordings: marimba, cello pizzicato and glockenspiel. Keep the
original composition, low dialogue-ducked level, reversal pause and shared
stroke/eraser sound timeline. Preserve each sample's pinned source and hash.

## Opening motion pass

All 432 frames of the 18-second opening-v3 render were inspected in nine
consecutive atlases. The magnet now enters continuously and the title
hierarchy is clear. Fast pen travel still produced three separated exposures.
The renderer now selects up to 24 shutter samples from measured pen and camera
travel. All 26 frames of the focused blur-v4 repair were inspected; the
separated exposures became a continuous trail. Final-film review must bind
this result to the final render again.

## Final audio preparation

All 18 current provider WAVs match their source hashes and independent
transcriptions after the bounded repairs to lines 03 and 09. Total natural
speech is 145.92 seconds, 439 words, with 72 source-preserving caption cues.
The final board timeline is exactly 180 seconds / 4,320 frames.

Sample pitch verification found the libraries use octave labels one lower
than scientific pitch naming. Publisher SFZ mappings and measured spectra
verified the actual roots. Correct the marimba and bell roots; choose a
lower cello recording near the bass part instead of transposing a high
recording excessively. This is frequency and mapping verification, not a
subjective listening claim.

## Encoded still inspection

All 19 original-resolution stills extracted from the first corrected-color
candidate were inspected. The study divider touched the relative-control
label, and the transfer examples' A/B labels sat too close to the ruled lines.
Shorten the divider by 45 board units and lower both example labels by 25.
Rebuild the entire picture and repeat final review on the resulting encode.

The first encode also inherited full-range JPEG color metadata. A decoded
frame and metadata check caught that before acceptance. The renderer now
explicitly converts to limited-range BT.709 YUV420P, checked on a three-frame
encoding probe. Range-normalized old/new picture SSIM was 0.999530 across
4,320 frames; this verifies the color conversion, not stylistic equivalence.

## Showcase interaction check

The browser confirmed chapter playback and continuous playback of both
comparison videos. Entering a frame number initially waited for focus to
leave the input. Add explicit Enter handling and verify exact seeks to
frames 0, 4,318 and 4,319. The final exported movie receives a separate
playback check after the rebuild.

## Final complete-frame review

Inspect all 135 paired atlases of the rebuilt 4,320-frame film and all 19
original-resolution final stills. Record observations and hashes in the
visual ledger, then finalize delivery only after verifying its coverage
against the technical record. The divider, A/B labels, closing ellipse,
continuous erase and whole-board framing are clear in the final encode.
See `visual-review.md` for the exact inspection scale and remaining stylistic
differences.

The final movie also played in the Codex in-app browser, advancing from
34.856 to 45.120 seconds with 1080p dimensions, 180-second duration and no
media error. Verify single-frame stepping and the last-frame seek against
the encoded movie. Save the observations in `browser-playback.json` and the
whole-board comparison in `browser-frame-lab.png`. These playback observations
do not establish subjective audio listening.
