"""Export subtitles from the narration and measured timing of a rendered story."""

import math
import re


def _seconds(value) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError("Subtitle timing must contain finite, non-negative seconds")
    return float(value)


def _srt_time(value: float) -> str:
    hours, millis = divmod(round(value * 1000), 3600000)
    minutes, millis = divmod(millis, 60000)
    seconds, millis = divmod(millis, 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"


def build_srt(timeline: dict) -> str:
    """Keep speech boundaries, excluding inter-scene silence and closing holds."""
    if not isinstance(timeline, dict) or not isinstance(timeline.get("scenes"), list) or not timeline["scenes"]:
        raise ValueError("A rendered narration timeline is required for subtitles")
    duration = _seconds(timeline.get("duration_seconds"))
    captions = []
    previous_end = 0
    for index, item in enumerate(timeline["scenes"], 1):
        if not isinstance(item, dict) or not isinstance(item.get("narration"), str):
            raise ValueError("Every subtitle scene must contain narration")
        text = re.sub(r"\s+", " ", item["narration"]).strip()
        if not text:
            raise ValueError("Subtitle narration cannot be blank")
        offset = _seconds(item.get("start_seconds"))
        scene_duration = _seconds(item.get("duration_seconds"))
        pacing = item.get("pacing")
        if pacing is None:
            start = 0.0
            end = _seconds(item.get("narration_duration_seconds"))
        elif isinstance(pacing, dict):
            start = _seconds(pacing.get("speech_start_seconds"))
            end = _seconds(pacing.get("speech_end_seconds"))
        else:
            raise ValueError("Invalid subtitle speech boundaries")
        start_ms, end_ms = round((offset + start) * 1000), round((offset + end) * 1000)
        if (end > scene_duration + 0.001 or offset + scene_duration > duration + 0.001
                or start_ms < previous_end or end_ms <= start_ms):
            raise ValueError("Subtitle timing overlaps or exceeds the rendered timeline")
        captions.append(f"{index}\n{_srt_time(offset + start)} --> {_srt_time(offset + end)}\n{text}\n")
        previous_end = end_ms
    return "\n".join(captions)
