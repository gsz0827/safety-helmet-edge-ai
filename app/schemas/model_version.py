from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ApiResponse


class ModelVersionCreate(BaseModel):
    name: str = Field(..., examples=["helmet-yolov8n"])
    version: str = Field(..., examples=["v1.0.0"])
    framework: str = Field(default="onnxruntime", examples=["onnxruntime"])
    model_path: str = Field(..., examples=["runs/detect/helmet_final/weights/best.onnx"])
    input_size: int = Field(default=640, examples=[640])

    precision: float | None = Field(default=None, ge=0, le=1, examples=[0.924])
    recall: float | None = Field(default=None, ge=0, le=1, examples=[0.866])
    map50: float | None = Field(default=None, ge=0, le=1, examples=[0.936])
    latency_ms: float | None = Field(default=None, examples=[23.5])

    is_active: bool = Field(default=False, examples=[True])


class ModelVersionOut(BaseModel):
    id: int
    name: str
    version: str
    framework: str
    model_path: str
    input_size: int

    precision: float | None
    recall: float | None
    map50: float | None
    latency_ms: float | None

    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }


class ModelVersionListData(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[ModelVersionOut]


class ModelVersionCreateResponse(ApiResponse[ModelVersionOut]):
    pass


class ModelVersionDetailResponse(ApiResponse[ModelVersionOut]):
    pass


class ModelVersionListResponse(ApiResponse[ModelVersionListData]):
    pass
