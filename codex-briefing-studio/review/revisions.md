# Revision record

## Still pass 1 — rejected

The first preview exposed a font-parser error: an unsupported numeric weight
was interpreted as a font size, making the final title enormous. Tag baselines
also clipped the label bottoms. Students overlapped the percentage annotations.

Changed the title weight to a supported value, moved tag baselines, separated
people from numerical evidence, and replaced “NOT LEARNING” with “WEAKER ALONE.”
The original wording overreached the study.

## Still pass 2 — rejected

The board was measurably brighter than the encoded reference. The measured
neutral background in representative frames was roughly RGB 242/240/233,
versus 227/223/212 in the reference.

Adjusted the base material toward the reference, widened the four-test and
tutor camera poses, and separated the physics formula and lower-board figures.

## Still pass 3 — revised

The new material, labels, study comparison, and final board were inspected at
1920 × 1080. The four labels fit, and the numerical comparison no longer
intersected the student drawing. The physics formula still touched the subtitle
region; it was moved above the figures. A remnant of the seated pose appeared
in the teacher drawing; the teacher paths were separated.

The opening now pulls out from the equation to show the whole question.
The final connector was rerouted to avoid the method card. Caption timing
changed from estimated reading fractions to actual ASR word observations.

The retained preview directories distinguish these revisions. Final encoded
frame inspection and playback are recorded separately after rendering.

## Encoded picture pass 1 — revised

The full 3,866-frame picture was decoded and retained. Full-resolution checks
found four concrete defects: the opening stamp covered the student's desk;
the flag's crescent used an opaque red patch over translucent red; the ruler's
zero and 100 marks did not align with the comparison axis; and an equation-like
label could be read as asserting that recognition equals knowledge.

Moved the stamp, constructed the crescent with a clipped even-odd path, aligned
the ruler, and used an explicit not-equal sign. Raised the lower-board people
to clear the tray. The first encoded pass remains in `media/picture-pass1.mp4`.

The board material cache now blurs one reduced-resolution ghost layer instead
of repeatedly blurring the entire board. This improves browser preview startup
without changing the physical drawing vocabulary.

Full-resolution inspection of pass 2 showed that raising the bottom figures
cleared the tray but put their heads over the labels. Reduced these three
figures to 180 board units and placed them wholly between the labels and tray.

Compared the numerical reveal with actual word timestamps. The practice result
originally appeared almost three seconds after “48 percent.” Advanced the
dimension and result while retaining the sequence of measure, value, and
qualification. The result now starts immediately after the spoken number.

Reduced excessive wall exposure in the lower-board shots. The people now fit
above the subtitle region and the metal tray stays near the bottom edge.

The rectangular notebook photograph still differed from the reference's cutout
props. A transparent generative derivative removes the wooden table and restores
the cropped notebook edges. Inspected its alpha and both rendered placements.
The final composition uses the cutout with renderer-supplied shadows and magnets.

Checked the opening stamp in the following four-test view as well as its own
shot. It overlapped the later-learner's head. Narrowed and moved it into the
gap between figures. Cached settled cutout shadows in board coordinates so
they scale with the camera and do not require a fresh alpha blur on every frame.

## Speech repair

Unprompted recognition of original segment 08 reported “but thinking remains
yours” where the source asks “What thinking remains yours?” The original WAV,
provider job, request hash, and recognition evidence remain retained. A separate
seed-bound candidate passed an independent transcription check. Segment 11 also
changed a conditional sentence into a question; a separate seed-bound candidate
restored the source wording and passed the same check. Adoption waits until the
initial sequential provider run has finished, preventing a manifest race.

Segment 13 added “End of the coin” after the complete script. The correct final
word ended near 7.98 seconds, decaying into a low-energy interval by 8.15 seconds;
the unwanted phrase began at about 8.60 seconds. A candidate retains the exact
first 199,200 PCM samples (8.30 seconds at 24 kHz). The original remains intact.
A new unprompted transcription of this trimmed candidate matches the entire
source with no extra or missing words. No speech was synthesized or spliced into
the retained prefix.

All 14 final speech segments passed source-bound, unprompted transcription.
Candidates 08, 11, and the exact-prefix trim of 13 were adopted after the
original run completed. Accepted overrides preserve those choices on resume.

## Final caption correction

The first audio/caption composite exposed ASR punctuation and spacing artifacts:
“what thinking remains yours.” lost the authored question mark, and percentages
and hyphenated recognizer words acquired stray spaces. The caption builder now
uses recognition only for word timestamps and maps those timestamps back to the
exact authored words, capitalization, and punctuation. Validation compares every
shot’s concatenated caption text with its narration. The earlier composite is
retained as `media/final-caption-draft1.mp4`; it is not the delivery.

## Delivered revision 2 — motion and materials

The first publication retained visibly separated outlines during rapid camera
moves. Full-resolution comparison at frames 633 and 2443 showed that three
exposure samples were insufficient. Adaptive sampling now integrates the same
half-frame shutter window with projected adjacent samples at most 0.75 pixels
apart. Balanced averaging prevents accumulated brightness rounding. All 110
frames in two focused motion clips were inspected before the complete render.

The same revision reduces magnet highlights, brings blue/red ink toward the
encoded reference, and replaces squared stamp borders and opaque pits with
rounded borders and transparent wear. A one-second transition removes the
closing camera's abrupt change in drift.

The complete revised encode was inspected in 194 paired sheets covering every
one of its 3,866 frames. Twenty-four actual encoded frames were inspected at
1920 × 1080. The final ledger records both scales of observation. The extracted
AAC track is byte-identical to the first delivery; the accepted speech and
timeline have not been regenerated. Revision 1 remains recoverable in the
local media and ZIP archive, with its original review and publication records.
