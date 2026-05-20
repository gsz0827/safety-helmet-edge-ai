from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import Device
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.device import (
    DeviceCreate,
    DeviceCreateResponse,
    DeviceDetailResponse,
    DeviceListData,
    DeviceListResponse,
    DeviceOut,
    DeviceStatusUpdate,
)

router = APIRouter(
    prefix="/api/v1/devices",
    tags=["Devices"],
)


@router.post("", response_model=DeviceCreateResponse)
def create_device(payload: DeviceCreate, db: Session = Depends(get_db)):
    device = Device(
        device_id=payload.device_id,
        name=payload.name,
        location=payload.location,
        status="offline",
    )

    db.add(device)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Device already exists")

    db.refresh(device)

    return ApiResponse[DeviceOut](
        code=0,
        message="success",
        data=DeviceOut.model_validate(device),
    )


@router.get("", response_model=DeviceListResponse)
def list_devices(
    status: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    stmt = select(Device)
    count_stmt = select(func.count()).select_from(Device)

    if status:
        stmt = stmt.where(Device.status == status)
        count_stmt = count_stmt.where(Device.status == status)

    total = db.scalar(count_stmt) or 0

    devices = db.scalars(
        stmt.order_by(Device.created_at.desc()).offset(offset).limit(limit)
    ).all()

    data = DeviceListData(
        total=total,
        limit=limit,
        offset=offset,
        items=[
            DeviceOut.model_validate(device)
            for device in devices
        ],
    )

    return ApiResponse[DeviceListData](
        code=0,
        message="success",
        data=data,
    )


@router.get("/{device_id}", response_model=DeviceDetailResponse)
def get_device(device_id: str, db: Session = Depends(get_db)):
    device = db.scalar(
        select(Device).where(Device.device_id == device_id)
    )

    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")

    return ApiResponse[DeviceOut](
        code=0,
        message="success",
        data=DeviceOut.model_validate(device),
    )


@router.patch("/{device_id}/status", response_model=DeviceDetailResponse)
def update_device_status(
    device_id: str,
    payload: DeviceStatusUpdate,
    db: Session = Depends(get_db),
):
    device = db.scalar(
        select(Device).where(Device.device_id == device_id)
    )

    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")

    device.status = payload.status
    device.last_seen_at = datetime.utcnow()
    device.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(device)

    return ApiResponse[DeviceOut](
        code=0,
        message="success",
        data=DeviceOut.model_validate(device),
    )
