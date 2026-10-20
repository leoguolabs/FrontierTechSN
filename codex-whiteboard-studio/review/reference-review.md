# Reference review

Reference: LemoLab, *Einstein in Your Pocket*, Whiteboard Explainer,
https://github.com/lemomo-ai/lemo-opuscar/releases/download/films/whiteboard.mp4

1920 × 1080, 24 fps, 111 seconds, 2,664 decoded frames.
SHA-256: `4455a67e655c6359d9b322c03c9a0ca5584699a268f832691ad47558ba5ffa8a`.

## Coverage

All frames 0–2,663 were decoded and measured. The complete visual pass inspected
56 consecutive-frame atlases: 48 frames per sheet, except the last 24-frame
sheet. Each tile was generated at 320 × 180; the inspection interface displayed
the 2560 × 1224 sheets at 2048 × 979. This is complete atlas coverage, not a
claim that each frame was separately inspected at original resolution.
Selected stills were also opened at 1920 × 1080, including the title at 12.7 s
and the parallel clocks at 51.5 s.

The two-second overview is an index only. It is not the complete review.

## Observations by interval

| Frames | Visible action and style observation |
|---|---|
| 0–191 | Magnet lands with a contracting shadow. Phone/map strokes reveal progressively. Warm surface remains visible through ink. |
| 192–383 | Camera pullback and whip introduce the two-line title. Fast pen travel has subframe trails; the subtitle remains sharp. |
| 384–575 | Blue line motivates a long camera travel toward satellites. Lettering and diagrams remain attached to the board. |
| 576–767 | Signal geometry transitions into a written equation. Orange underline separates emphasis from explanation. |
| 768–959 | Equation completes, then camera returns to the existing phone. Blue circles are drawn around a fixed map. |
| 960–1151 | The magnet identifies an intersection. A short writing pause precedes the whip to paired clocks. |
| 1152–1343 | Two pens draw clock timelines in parallel. The tick discrepancy accumulates; the camera holds long enough to compare it. |
| 1344–1535 | Camera reframes lower for speed/gravity annotations. Individual pen lifts are visible between words and symbols. |
| 1536–1727 | Orange sums the timing offset and circles the result. Camera returns to the earlier distance equation. |
| 1728–1919 | Calculation finishes and is underlined. Return to map; magnet begins drifting along an orange path. |
| 1920–2111 | Drift unfolds over several days. Sea/fish doodle provides a visual consequence. A horizontal dark eraser with an orange inset wipes the path and leaves faint ink. |
| 2112–2303 | Eraser returns along the same geography. Clock timeline is corrected. Parallel pen movement resolves the earlier discrepancy. |
| 2304–2495 | Camera pulls back to reveal the physical board, aluminum frame and tray. Then it moves toward the title for attribution. |
| 2496–2663 | Small handwriting credits complete; pens leave; the final board holds without a black flash. |

## Implications for the independent film

- Use one board with stable world coordinates and revisitable drawings.
- A pen's nib must follow the same path and timing that creates its ink.
- Preserve letter lifts; serialize competing strokes assigned to one pen.
- Scale pen bodies and cast shadows with the camera; avoid flat cursor arrows.
- Keep black, blue and terracotta as the dominant ink families.
- Keep faint prior writing, broad reflections and dry ink texture subtle.
- Short handwritten caption clauses fit the reference better than two-line
  paragraph cards.
- Camera movement needs real subframe blur; stationary captions should stay crisp.
- Use an eraser with a physical wipe footprint and residual ink.
- End with a complete physical board rather than an unrelated flat end card.

## Measurement baseline

See `reference/analysis.json` and `reference/frames.csv` in this review directory.
The CSV contains a measurement row for every decoded frame. Median luminance
was 233.47/255; median bright-board coverage 0.9332; median dark-ink coverage
0.0180. Frame-to-frame mean absolute luminance change had median 2.235 and
90th percentile 6.881. These descriptors help locate deviations; they are
not a perceptual-equivalence score.
