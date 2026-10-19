# Visual methods comparison — production brief

Authorized purpose: six original short samples for the user's private visual review, plus research into Codex-compatible workflows. These are feasibility samples, not claims of each tool's maximum quality or an AI model benchmark.

## Common controls

- Topic: **The agent loop**. Conceptual explanation; no invented product, performance, current-news claim or actual customer interface.
- 1920 × 1080, 24 fps, 576 frames / 24 seconds, English narration.
- Identical narration and shared edit boundaries at frames 0, 144, 288, 432. Natural local macOS Daniel voice; generated per sentence, with pauses rather than time stretching.
- Narration: “An AI model can give you an answer. An agent can take the next step. It reads a goal, uses a tool, and checks the result. Then it tries again. Action. Feedback. Correction.”
- Original procedural graphics, no stock footage, no generative-video service, no Opus invocation. Authored in this Codex session; do not infer a particular underlying model version from the output.
- Audio control: voice only, no BGM or SFX. It is deliberately not a voice-quality comparison.
- Legible key messages; at least one second of hold after main title settles. Clean ending with no fade to blank. No camera shake or continuous full-screen beat pumping.

## Director treatment

Three story structures considered: (1) headline montage with unrelated B-roll; (2) model versus agent split-screen; (3) one answer becomes an actionable, checked loop. Choose (3): each shot adds a causal step, allowing actual diagrams and state changes instead of decorative title changes.

| Frames | Meaning | Visual purpose | Voice start |
|---|---|---|---|
| 0–143 | An answer | Single focal object / headline; establish the question | 0.6s |
| 144–287 | Taking action | Answer becomes a tool action; purposeful spatial motion | 6.3s |
| 288–431 | Reading, using, checking | Sequential causal chain and evidence/result | 12.1s |
| 432–575 | Feedback loop | Action → feedback → correction; hold final state | 18.1s |

Signature: an incomplete route visibly closes into a loop when feedback arrives.
Camera vocabulary across methods: macro-to-context pullback; horizontal tracking; deliberate focus push; orbit/diagram reframing. Do not force all four into every sample.

## Six implementations

1. **lemo-opuscar / Swiss motion**: Canvas `render(t)` and Lemo's own still/video renderer; use the style's grid, typographic mass, functional red shapes and choreography. Three authored styleframes precede full render. The referenced news style is announced but absent from the checked style list; do not label this as a reproduction of that tweet.
2. **HyperFrames**: native seekable HTML and a paused GSAP timeline. Warm editorial paper/navy/copper from FrontierTechSN's design context, spatial diagrams and one intentional dark reversal. Existing pinned renderer, isolated composition.
3. **video-shotcraft**: autonomous creation; exact `orbit-ring-title-open`, `scanline-annotate-focus`, `word-relay-geometry` recipe sources, plus a clearly identified custom bridge. Use a dedicated 30 fps recipe clock mapped to 24 fps, including nested card clocks. Adapt final whitening 10 source frames earlier and enlarge subtitles to 56px, leaving at least one second of final readability. Add an explicitly original thin feedback route below the final caption. Replace demo content with this explainer, retain source attribution. Reference style is explicitly defined by those recipes; separate speculative styleframe stage is omitted, and the actual implemented recipe frames are reviewed before full render. Conceptual panels are not replicas of real software. Dark graphite/lime opening, warm paper/cobalt analysis, graphite conclusion follow the selected source looks. Final independent review required by the source skill.
4. **Remotion core**: original React/SVG animation, frame-indexed interpolation, springs, sequences; editorial blueprint style. This is a control for the renderer plus Codex without a shot library.
5. **Remotion Bits**: actual `remotion-bits` components (text/sequence/3D depending on verified API), not a hand-built imitation. Soft dark/violet spatial product-film treatment.
6. **Motion Canvas**: actual TypeScript generator scene, reactive signals and vector path drawing, official renderer/exporter. Light technical explainer style; strongest emphasis on mechanism rather than headline packaging.

Shotcraft source references: gallery/api/library.json and demos/opening/orbit-ring-title-open/OrbitRingTitleOpen.tsx; demos/effects/scanline-annotate-focus/ScanlineAnnotateFocus.tsx; demos/typography/word-relay-geometry/WordRelayGeometry.tsx. Exact cards in references/shots/{opening,effects,typography}. Source repository commit is recorded in provenance.json. Global Q8 finale rule is intentionally adapted: this is a mechanism explainer, not a multifunction product launch; the loop is the finale, not a staged product group portrait.

## Review and integration boundaries

Render and inspect key frames, then encoded-file full decode/frame cadence/audio checks and browser playback. Separate factual renderer checks from subjective visual judgments. No production scheduler/settings/task modifications. Runtime dependencies and media remain under ignored outputs/; source and research are committed. No publishing.
