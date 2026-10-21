# Illustrated three-minute edition: final visual review

**Decision:** illustrated refinement ready to show. The user accepted the
first short in principle and requested people and a Turkish flag. Confidence
is high that
the independent film reproduces the reference's recognizable whiteboard
language and that the observed visual defects have been repaired. This is
not a claim of pixel identity or a measurable “100%” aesthetic match.

Final movie SHA-256:
`9db8ae139d3ccbc7e576bb40a790ab8baded687fed897d6a9a43325f8b431df9`

Reference SHA-256:
`4455a67e655c6359d9b322c03c9a0ca5584699a268f832691ad47558ba5ffa8a`

## What was actually inspected

- All 2,664 reference frames, in 56 consecutive-frame atlases, plus selected
  original-resolution reference frames. See `reference-review.md`.
- All 4,320 final delivery frames, paired by visual function with reference
  frames in 135 consecutive comparison atlases. All 135 were visually opened
  and inspected; individual notes, file hashes and review times are in
  `visual-ledger.json`.
- All 19 original-resolution stills from the final encode, including every
  narration segment's closing picture and the final whole-board view.
- Every-frame measurements and strict decoding were performed separately.
  Their success does not substitute for the visual inspections above.

Comparison tiles were generated at 320 × 180 pixels. Each paired atlas is
2,560 × 1,624 pixels and was displayed at approximately 1,967 × 1,248. Thus
“every-frame review” means complete consecutive atlas coverage; it does not
mean that every frame was individually opened at native 1,920 × 1,080.
Full-resolution inspection is the separate set of 19 recorded stills.

## Style and motion findings

The warm reflective board, faint old ink, single-line handwriting, pressure
variation and dry strokes create the intended physical surface. Black, blue, orange
and red white-barrel markers have consistent contact, shadow and lift
behavior. Fast movement now produces a continuous blur instead of detached
duplicate pen images. Short caption cards remain sharp during camera travel.

The camera follows an argument on one persistent board. Whip movements connect
the different diagrams without resetting the surface. The final zoom places
the complete board and tray inside the picture and holds a readable three-row
composition. The more complex study section retains a clear visual hierarchy.

The eraser performs three continuous passes across the answer, leaves a faint
ghost, and preserves the surrounding bubble and thinking learner. It no longer jumps
between rows or reveals a rectangular wipe. The practice, feedback and transfer
diagrams build in a legible sequence. The final orange ellipse clears the
closing question.

## People and place cues

Five original line-character drawings now appear across four scenes. The study
compares a seated learner using a blue laptop with the same character answering
an orange-marked exam. A thinking figure faces the physics book and lightbulb;
another considers the work left after an answer is erased. The practical loop
begins with a learner writing a first attempt on paper.

These are timed strokes in the same pen queues as the lettering. Their heads,
arms, clothes, chairs, desks and tools appear through physical marker movement.
The red-hatched Turkish flag leaves the crescent and five-point star as exposed
board surface. The flag and every character remain on the board at the closing
zoom. They are explanatory illustrations, not portraits of study participants.

Development stills exposed a notebook crossing a torso, laptop hands too far
from the keyboard and a physics learner facing away from the example. The
notebook was moved outside the body, the typing pose aligned and the thinking
pose mirrored.
The final encoded atlas sequence and native stills verify those repairs. The
exam figure does not cover its data, the eraser stays clear of the person, and
the first-attempt figure fits above its label without touching the next card.

## Revisions verified on the final encode

Earlier iterations exposed font-metric errors, duplicate drawing-cache IDs,
competing pen queues, weak title hierarchy, intersecting marks, discontinuous
eraser movement and separated motion-blur exposures. These were repaired and
the affected movements rerendered during development.

The full-resolution inspection then caught a study divider touching its label
and A/B labels sitting too close to document rules. Both layouts were corrected,
the entire film was rebuilt, and the complete final-frame review was repeated.
The final labels and divider have clear separation. A briefly passing pen near
“expert material” clears the label before the transition; the label also has a
clear reading hold.

The encode now explicitly uses limited-range BT.709 YUV420P. The earlier
range-conversion comparison was a color-preservation check, not a style score.
No unresolved visual defect was identified during the final review.

## Differences that remain

This is a new 180-second story, while the reference lasts 111 seconds. The
independent film has a centered title, a different whole-board layout, denser
research diagrams and longer reading holds. Its overall motion and color
coverage therefore differ. It recreates the visual vocabulary rather than
the reference's exact sequence, timing or drawings.

Reference frames are mapped by function, such as a title, comparison or erase.
The reference side can jump when the function changes; the candidate itself
remains continuous. Neither that mapping nor an image-similarity metric can
establish literal aesthetic equivalence.

## Audio, delivery and approval boundaries

The final technical record confirms 180 seconds, 24 fps, 4,320 decoded frames,
1,920 × 1,080, synchronized audio placement, approximately −14.01 LUFS and
−1.42 dBTP. Eighteen Chatterbox source WAVs retain their job and hash bindings;
independent transcription matches the finalized narration after bounded repairs.
These are transcription, waveform and loudness checks. Subjective listening
has not been established and is not claimed.

The first short was accepted in principle. This illustrated refinement is
ready to show; the prior version is preserved in the export's
`versions/01-reviewed-short/` folder. At the time of this short-edition review,
the 12-minute edition had not started. Its subsequent review is recorded
separately in `editions/long/review/visual-review.md`.
The English process article includes this refinement and remains local,
unpublished to X.
