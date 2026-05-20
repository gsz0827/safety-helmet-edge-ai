from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ApiResponse


class DeviceCreate(BaseModel):
    device_id: str = Field(..., examples=["edge_ai_001"])
    name: str = Field(..., examples=["边缘推理节点 001"])
    location: str | None = Field(default=None, examples=["一号车间入口"])


class DeviceStatusUpdate(BaseModel):
    status: str = Field(..., examples=["online"])


class DeviceOut(BaseModel):
    id: int
    device_id: str
    name: str
    location: str | None
    status: str
    last_seen_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }


class DeviceListData(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[DeviceOut]


class DeviceCreateResponse(ApiResponse[DeviceOut]):
    pass


class DeviceDetailResponse(ApiResponse[DeviceOut]):
    pass


class DeviceListResponse(ApiResponse[DeviceListData]):
    pass
