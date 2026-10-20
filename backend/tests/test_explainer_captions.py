from copy import deepcopy

import pytest

from backend.explainer_captions import build_srt


def timeline():
    return {"duration_seconds": 7, "scenes": [
        {"start_seconds": 0, "duration_seconds": 3, "narration": "Try\nremembering.",
         "pacing": {"speech_start_seconds": 0.08, "speech_end_seconds": 2.7}},
        {"start_seconds": 3, "duration_seconds": 4, "narration": "再核对答案。",
         "pacing": {"speech_start_seconds": 0.05, "speech_end_seconds": 1.5}},
    ]}


def test_subtitles_follow_speech_and_exclude_closing_hold():
    assert build_srt(timeline()) == (
        "1\n00:00:00,080 --> 00:00:02,700\nTry remembering.\n\n"
        "2\n00:00:03,050 --> 00:00:04,500\n再核对答案。\n"
    )


def test_legacy_timeline_uses_measured_narration_duration():
    data = timeline()
    for scene in data["scenes"]:
        scene.pop("pacing")
        scene["narration_duration_seconds"] = 1.25
    assert "00:00:03,000 --> 00:00:04,250" in build_srt(data)


@pytest.mark.parametrize("change", [
    {"start_seconds": -1}, {"start_seconds": float("nan")}, {"start_seconds": 1},
    {"narration": " \n "}, {"duration_seconds": 100},
    {"pacing": {"speech_start_seconds": 1, "speech_end_seconds": 0.5}},
    {"pacing": {"speech_start_seconds": 0, "speech_end_seconds": 5}},
    {"pacing": {"speech_start_seconds": 0}},
])
def test_rejects_invalid_or_overlapping_timing(change):
    data = deepcopy(timeline())
    data["scenes"][1].update(change)
    with pytest.raises(ValueError):
        build_srt(data)
