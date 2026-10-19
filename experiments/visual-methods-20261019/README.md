# Six video-method samples

Six actual 24-second, 1080p/24 fps films with identical narration, created for visual review. This is an isolated experiment, not a production integration.

## Review

From repository root:

```sh
python experiments/visual-methods-20261019/serve_review.py
```

Open `http://127.0.0.1:9020/` in Ego Lite. The server binds only to localhost and exposes a dedicated staged review directory, not the repository. It offers all six videos, simultaneous playback, common cut points, separate audio controls, original demonstrations, source links and technical-check results. MP4 files are under `outputs/visual-methods-20261019/final/`; sources below are committed, media/dependencies are intentionally ignored.

## Contents

- `RESEARCH.md` / `research.json`: six X search results, plus the Motion Canvas supplement; evidence limits, licenses, and project fit.
- `BRIEF.md`, `timeline.json`, `narration.srt`: controlled script and timing.
- `lemo/`: original Swiss-style Canvas film with deterministic `render(t)`.
- `hyperframes/`: original HTML/GSAP composition, rendered with existing HyperFrames 0.6.99.
- `react/`: original Remotion core/Bits films, and adapted Shotcraft assembly.
- `prepare_shotcraft.py`: reproducible source adaptations. `RecipeClock.tsx` avoids Remotion's root-duration clamp when mapping 30 fps recipe time to the 24 fps final composition.
- `motion/`: actual Motion Canvas generator scene and export metadata.
- `provenance.json`, `runtime-package-lock.json`, `CREDITS.md`: pinned source identity, isolated dependency lock, attribution.
- `QA.md`: final file checks and visual-review boundaries.

## Re-render in this workspace

Dependencies and selected upstream sources were prepared under `outputs/visual-methods-20261019/` without changing production dependencies. `react/node_modules` and `motion/node_modules` point to the isolated `runtime/node_modules`; `react/public`, `lemo/assets` and `hyperframes/assets` point to the runtime `assets` directory. HyperFrames uses the existing local `gsap/dist/gsap.min.js` copied into its ignored composition file.

Set `PLAYWRIGHT_CHROME` to a compatible installed Chromium executable, then:

```sh
python experiments/visual-methods-20261019/render_samples.py lemo hyperframes shotcraft remotion bits
```

The tested browser was Chromium build 1161 in the local Playwright cache. Remotion requires `--chrome-mode=chrome-for-testing` with this executable. Render each Remotion composition sequentially with one worker; concurrent complex filter rendering previously timed out. Use `--audio` to recreate the common narration with installed macOS Daniel; this is platform-dependent. `--mux-only` uses existing silent videos.

Motion Canvas uses its native exporter: run `npm run serve` inside `motion/`, open localhost:9019, select Video (FFmpeg), confirm 1920×1080, 24 fps and range 0–576, then Render. Its committed `src/project.meta` contains these settings. After successful export:

```sh
python experiments/visual-methods-20261019/render_samples.py motion --mux-only
```

To reconstruct a deleted runtime: copy `runtime-package.json` and `runtime-package-lock.json` to `outputs/visual-methods-20261019/runtime/{package.json,package-lock.json}` and run `npm ci` there. Fetch upstream repositories into `outputs/visual-methods-20261019/vendor/` at the exact revisions in `provenance.json`. Lemo requires `core/`, its root package files and `npm ci`; Shotcraft requires `demos/`, including `_fixtures`, plus LICENSE. Fetch Archivo.ttf and its OFL notice from the credited Google Fonts source, recreate the links described above, regenerate narration, then render. Do not execute unpinned replacement source or substitute screenshots for native renders.

## Proposed production boundary

Current paths inspected: `backend/pipeline/visual_plan.py`, `director.py`, `scene_kit.py`, `assembler.py`, `composer.py`. Keep their existing scene/HTML/rendering contract. The first implementation should add a small set of tested HTML/GSAP shot recipes through `scene_kit.render_scene()` and the director's selection logic. Remotion/Bits/Motion Canvas can later expose an isolated clip-rendering adapter producing MP4 plus metadata/QA, consumed by composition as media. Installing a Skill alone will not make these foreign renderers usable inside the existing HTML pipeline.

No scheduler, current production video, persisted setting, backend, or publishing state was modified.
