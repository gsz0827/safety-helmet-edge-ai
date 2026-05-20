from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import Camera, Device
from app.db.session import get_db
from app.schemas.camera import (
    CameraCreate,
    CameraCreateResponse,
    CameraDetailResponse,
    CameraEnabledUpdate,
    CameraListData,
    CameraListResponse,
    CameraOut,
    CameraStatusUpdate,
)
from app.schemas.common import ApiResponse

router = APIRouter(
    prefix="/api/v1/cameras",
    tags=["Cameras"],
)


@router.post("", response_model=CameraCreateResponse)
def create_camera(payload: CameraCreate, db: Session = Depends(get_db)):
    device = db.scalar(
        select(Device).where(Device.device_id == payload.device_id)
    )

    if device is None:
        raise HTTPException(status_code=400, detail="Device does not exist")

    camera = Camera(
        camera_id=payload.camera_id,
        device_id=payload.device_id,
        name=payload.name,
        stream_url=payload.stream_url,
        enabled=True,
        status="offline",
    )

    db.add(camera)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Camera already exists")

    db.refresh(camera)

    return ApiResponse[CameraOut](
        code=0,
        message="success",
        data=CameraOut.model_validate(camera),
    )


@router.get("", response_model=CameraListResponse)
def list_cameras(
    device_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    enabled: bool | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    stmt = select(Camera)
    count_stmt = select(func.count()).select_from(Camera)

    if device_id:
        stmt = stmt.where(Camera.device_id == device_id)
        count_stmt = count_stmt.where(Camera.device_id == device_id)

    if status:
        stmt = stmt.where(Camera.status == status)
        count_stmt = count_stmt.where(Camera.status == status)

    if enabled is not None:
        stmt = stmt.where(Camera.enabled == enabled)
        count_stmt = count_stmt.where(Camera.enabled == enabled)

    total = db.scalar(count_stmt) or 0

    cameras = db.scalars(
        stmt.order_by(Camera.created_at.desc()).offset(offset).limit(limit)
    ).all()

    data = CameraListData(
        total=total,
        limit=limit,
        offset=offset,
        items=[
            CameraOut.model_validate(camera)
            for camera in cameras
        ],
    )

    return ApiResponse[CameraListData](
        code=0,
        message="success",
        data=data,
    )


@router.get("/{camera_id}", response_model=CameraDetailResponse)
def get_camera(camera_id: str, db: Session = Depends(get_db)):
    camera = db.scalar(
        select(Camera).where(Camera.camera_id == camera_id)
    )

    if camera is None:
        raise HTTPException(status_code=404, detail="Camera not found")

    return ApiResponse[CameraOut](
        code=0,
        message="success",
        data=CameraOut.model_validate(camera),
    )


@router.patch("/{camera_id}/status", response_model=CameraDetailResponse)
def update_camera_status(
    camera_id: str,
    payload: CameraStatusUpdate,
    db: Session = Depends(get_db),
):
    camera = db.scalar(
        select(Camera).where(Camera.camera_id == camera_id)
    )

    if camera is None:
        raise HTTPException(status_code=404, detail="Camera not found")

    camera.status = payload.status
    camera.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(camera)

    return ApiResponse[CameraOut](
        code=0,
        message="success",
        data=CameraOut.model_validate(camera),
    )


@router.patch("/{camera_id}/enabled", response_model=CameraDetailResponse)
def update_camera_enabled(
    camera_id: str,
    payload: CameraEnabledUpdate,
    db: Session = Depends(get_db),
):
    camera = db.scalar(
        select(Camera).where(Camera.camera_id == camera_id)
    )

    if camera is None:
        raise HTTPException(status_code=404, detail="Camera not found")

    camera.enabled = payload.enabled
    camera.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(camera)

    return ApiResponse[CameraOut](
        code=0,
        message="success",
        data=CameraOut.model_validate(camera),
    )
