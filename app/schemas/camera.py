from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ApiResponse


class CameraCreate(BaseModel):
    camera_id: str = Field(..., examples=["cam_01"])
    device_id: str = Field(..., examples=["edge_ai_001"])
    name: str = Field(..., examples=["一号车间入口摄像头"])
    stream_url: str = Field(..., examples=["rtsp://example.com/live"])


class CameraStatusUpdate(BaseModel):
    status: str = Field(..., examples=["online"])


class CameraEnabledUpdate(BaseModel):
    enabled: bool = Field(..., examples=[True])


class CameraOut(BaseModel):
    id: int
    camera_id: str
    device_id: str
    name: str
    stream_url: str
    enabled: bool
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }


class CameraListData(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[CameraOut]


class CameraCreateResponse(ApiResponse[CameraOut]):
    pass


class CameraDetailResponse(ApiResponse[CameraOut]):
    pass


class CameraListResponse(ApiResponse[CameraListData]):
    pass
