from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import ApiResponse


class ImageInferenceData(BaseModel):
    filename: str
    image_width: int
    image_height: int
    detections: list[dict[str, Any]] = Field(default_factory=list)
    inference_time_ms: float | None = None

    alarm_created: bool = False
    alarm_id: int | None = None


class ImageInferenceResponse(ApiResponse[ImageInferenceData]):
    pass
