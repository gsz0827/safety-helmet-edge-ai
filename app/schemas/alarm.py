from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ApiResponse


class AlarmCreate(BaseModel):
    device_id: str = Field(..., examples=["edge_ai_001"])
    camera_id: str | None = Field(default=None, examples=["cam_01"])
    event_type: str = Field(..., examples=["no_helmet"])
    confidence: float = Field(..., ge=0, le=1, examples=[0.92])
    image_url: str | None = None
    bbox_json: str | None = None
    inference_time_ms: float | None = None
    fps: float | None = None


class AlarmOut(BaseModel):
    id: int
    device_id: str
    camera_id: str | None
    event_type: str
    confidence: float
    image_url: str | None
    bbox_json: str | None
    inference_time_ms: float | None
    fps: float | None
    status: str
    handler: str | None
    remark: str | None
    handled_at: datetime | None
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class AlarmListData(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[AlarmOut]


class AlarmHandleRequest(BaseModel):
    handler: str = Field(default="admin", examples=["admin"])
    remark: str | None = Field(default=None, examples=["已通知现场负责人处理"])


class AlarmCreateResponse(ApiResponse[AlarmOut]):
    pass


class AlarmDetailResponse(ApiResponse[AlarmOut]):
    pass


class AlarmListResponse(ApiResponse[AlarmListData]):
    pass
