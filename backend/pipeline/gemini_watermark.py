"""Local repair of the visible Gemini corner mark, before delivery overlays.

The default region is measured from the 1280x720 Gemini explainer download.
Coordinates are percentages of the source frame, not the padded delivery canvas.
This is spatial interpolation, not automatic logo detection or lossless recovery.
"""
from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class WatermarkRegion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    x: float = Field(default=87.5, gt=0, lt=100, allow_inf_nan=False)
    y: float = Field(default=77.78, gt=0, lt=100, allow_inf_nan=False)
    width: float = Field(default=6.25, gt=0, lt=100, allow_inf_nan=False)
    height: float = Field(default=11.11, gt=0, lt=100, allow_inf_nan=False)

    @model_validator(mode="after")
    def inside_frame(self) -> WatermarkRegion:
        if self.x + self.width >= 100 or self.y + self.height >= 100:
            raise ValueError("Watermark region must leave a border inside the source frame")
        return self


class WatermarkReviewEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class WatermarkReview(BaseModel):
    """Manual review of every source frame in the configured repair area."""

    model_config = ConfigDict(extra="forbid")
    version: Literal[1]
    decision: Literal["absent_in_configured_region"]
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_dimensions: tuple[int, int]
    reviewed_frame_count: int = Field(gt=0, strict=True)
    region_percent: WatermarkRegion
    reviewed_at: str = Field(min_length=1)
    notes: str = Field(min_length=1)
    evidence: list[WatermarkReviewEvidence] = Field(min_length=1)


def repair_plan(width: int, height: int, region: dict | None = None) -> dict:
    """Produce a validated delogo filter plus cache/provenance metadata."""
    area = WatermarkRegion.model_validate(region or {})
    x, y = math.floor(width * area.x / 100), math.floor(height * area.y / 100)
    right = math.ceil(width * (area.x + area.width) / 100)
    bottom = math.ceil(height * (area.y + area.height) / 100)
    if x < 1 or y < 1 or right >= width or bottom >= height or right - x < 4 or bottom - y < 4:
        raise ValueError("Watermark region is too small or too close to the source frame edge")
    return {
        "version": 1,
        "method": "ffmpeg_delogo",
        "source_dimensions": [width, height],
        "region_percent": area.model_dump(),
        "region_pixels": {"x": x, "y": y, "width": right - x, "height": bottom - y},
        "filter": f"delogo=x={x}:y={y}:w={right - x}:h={bottom - y}:show=0",
    }
