# Delivery review — 2026-10-19

Final artifact identity: `delivery-manifest.json` contains SHA-256 and bytes for the six MP4s. Detailed machine reports and extracted boundary frames are in `outputs/visual-methods-20261019/qa/<method>/delivery-check.json`. The report scripts do not issue a visual-quality verdict.

All six: 1920×1080, 24 fps, 24 seconds, 576 decoded frames; full video/audio decode passed; timestamps match the shared frame timeline; AAC narration present. The same local voice track is muxed into every film.

| Film | Size | Frames | Loudness | True peak | Technical checks |
|---|---:|---:|---:|---:|---|
| lemo | 0.90 MiB | 576 | -17.70 LUFS | -1.96 dBTP | PASS |
| hyperframes | 1.98 MiB | 576 | -17.70 LUFS | -1.96 dBTP | PASS |
| shotcraft | 9.35 MiB | 576 | -17.70 LUFS | -1.96 dBTP | PASS |
| remotion | 1.37 MiB | 576 | -17.70 LUFS | -1.96 dBTP | PASS |
| bits | 1.75 MiB | 576 | -17.70 LUFS | -1.96 dBTP | PASS |
| motion | 0.80 MiB | 576 | -17.70 LUFS | -1.96 dBTP | PASS |

## Actual image and playback review

- Inspected rendered frames across all four shots and final holds. Remotion Bits JSX/string and transform-matrix problems were found and corrected using the actual component API. Motion Canvas body fonts were made consistent before its final native export.
- All six final files were played in Ego Lite on the local review page. DOM observations showed all six at approximately 0.488 seconds with readyState 4 and no media error, then all six at 24 seconds with ended=true and no error. This verifies real playback and endpoint completion, not a subjective frame-by-frame viewing verdict.
- Shotcraft received the fresh independent review required by its source Skill. It found an actual final-shot timing bug: Remotion Freeze clamped a virtual global frame at the root duration. A dedicated recipe clock now reaches the full source timeline, including nested card time. Final captions were enlarged and their entrance moved earlier; the final white word and complete feedback route hold for over one second. The independent recheck inspected the new encoded movie at frames 540, 551 and 575. The report is preserved in the runtime output folder.
- Documented design exception: Shotcraft's opening non-narrative kicker/brand labels retain the recipe's 26/30px hierarchy instead of the source Skill's generic 32px auxiliary-text minimum. Main narrative captions were enlarged to 56px. Do not describe this as unconditional compliance with every source aesthetic rule.
- HyperFrames lint/validate/inspect were run. No blocking layout error remained; contrast warnings from inherited colors were checked against rendered frames. GSAP-managed editing warnings are expected for these authored timelines.
- This was not a blind model benchmark, production pipeline acceptance test, or proof that every original X demo was made by Codex. The actual model behind unspecified author demos remains unknown. No Opus model was invoked for this batch.
- Audio was checked for complete decoding, duration, loudness and peak. A full subjective listening pass is not claimed; voice quality and pacing remain part of the user's review. No BGM or SFX were used.

## Verification scope

Python scripts compile; actual native renderers exported the media; six final encoded files passed decode/cadence/audio checks; the review page loaded all source/media links and played every video to completion. No production service restart, scheduler change, task recovery, publication, or repository-wide test suite was needed for this isolated experiment.
