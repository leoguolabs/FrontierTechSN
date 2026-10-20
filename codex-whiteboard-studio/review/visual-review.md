# Three-minute edition: final visual review

**Decision:** ready for the user's short-film review. Confidence is high that
the independent film reproduces the reference's recognizable whiteboard
language and that the observed visual defects have been repaired. This is
not a claim of pixel identity or a measurable “100%” aesthetic match.

Final movie SHA-256:
`170b4e1df4c1467246a89365bab4443972a2208ec6837fc4c84ce631db623936`

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
variation and dry strokes create the intended physical surface. Black, blue
and orange white-barrel markers have consistent contact, shadow and lift
behavior. Fast movement now produces a continuous blur instead of detached
duplicate pen images. Short caption cards remain sharp during camera travel.

The camera follows an argument on one persistent board. Whip movements connect
the different diagrams without resetting the surface. The final zoom places
the complete board and tray inside the picture and holds a readable three-row
composition. The more complex study section retains a clear visual hierarchy.

The eraser performs three continuous passes across the answer, leaves a faint
ghost, and preserves the surrounding bubble and document. It no longer jumps
between rows or reveals a rectangular wipe. The practice, feedback and transfer
diagrams build in a legible sequence. The final orange ellipse clears the
closing question.

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
−1.39 dBTP. Eighteen Chatterbox source WAVs retain their job and hash bindings;
independent transcription matches the finalized narration after bounded repairs.
These are transcription, waveform and loudness checks. Subjective listening
has not been established and is not claimed.

The short edition is ready to show. The user's approval is still pending.
The 12-minute edition has not started. The English process article is prepared
locally and has not been published to X.
