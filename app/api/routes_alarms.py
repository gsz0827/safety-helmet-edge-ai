from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Alarm
from app.db.session import get_db
from app.schemas.alarm import (
    AlarmCreate,
    AlarmCreateResponse,
    AlarmDetailResponse,
    AlarmHandleRequest,
    AlarmListData,
    AlarmListResponse,
    AlarmOut,
)
from app.schemas.common import ApiResponse

router = APIRouter(
    prefix="/api/v1/alarms",
    tags=["Alarms"],
)


@router.post("", response_model=AlarmCreateResponse)
def create_alarm(payload: AlarmCreate, db: Session = Depends(get_db)):
    alarm = Alarm(**payload.model_dump())

    db.add(alarm)
    db.commit()
    db.refresh(alarm)

    return ApiResponse[AlarmOut](
        code=0,
        message="success",
        data=AlarmOut.model_validate(alarm),
    )


@router.get("", response_model=AlarmListResponse)
def list_alarms(
    status: str | None = Query(default=None),
    camera_id: str | None = Query(default=None),
    event_type: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    stmt = select(Alarm)
    count_stmt = select(func.count()).select_from(Alarm)

    if status:
        stmt = stmt.where(Alarm.status == status)
        count_stmt = count_stmt.where(Alarm.status == status)

    if camera_id:
        stmt = stmt.where(Alarm.camera_id == camera_id)
        count_stmt = count_stmt.where(Alarm.camera_id == camera_id)

    if event_type:
        stmt = stmt.where(Alarm.event_type == event_type)
        count_stmt = count_stmt.where(Alarm.event_type == event_type)

    total = db.scalar(count_stmt) or 0

    stmt = stmt.order_by(Alarm.created_at.desc()).offset(offset).limit(limit)
    alarms = db.scalars(stmt).all()

    data = AlarmListData(
        total=total,
        limit=limit,
        offset=offset,
        items=[
            AlarmOut.model_validate(alarm)
            for alarm in alarms
        ],
    )

    return ApiResponse[AlarmListData](
        code=0,
        message="success",
        data=data,
    )


@router.get("/{alarm_id}", response_model=AlarmDetailResponse)
def get_alarm(alarm_id: int, db: Session = Depends(get_db)):
    alarm = db.get(Alarm, alarm_id)

    if alarm is None:
        raise HTTPException(status_code=404, detail="Alarm not found")

    return ApiResponse[AlarmOut](
        code=0,
        message="success",
        data=AlarmOut.model_validate(alarm),
    )


@router.patch("/{alarm_id}/handle", response_model=AlarmDetailResponse)
def handle_alarm(
    alarm_id: int,
    payload: AlarmHandleRequest,
    db: Session = Depends(get_db),
):
    alarm = db.get(Alarm, alarm_id)

    if alarm is None:
        raise HTTPException(status_code=404, detail="Alarm not found")

    alarm.status = "handled"
    alarm.handler = payload.handler
    alarm.remark = payload.remark
    alarm.handled_at = datetime.utcnow()

    db.commit()
    db.refresh(alarm)

    return ApiResponse[AlarmOut](
        code=0,
        message="success",
        data=AlarmOut.model_validate(alarm),
    )
