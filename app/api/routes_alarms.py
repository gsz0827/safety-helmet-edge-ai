from datetime import datetime, timedelta

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
    AlarmStatisticsData,
    AlarmStatisticsResponse,
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


@router.get("/statistics", response_model=AlarmStatisticsResponse)
def get_alarm_statistics(
    latest_limit: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    total = db.scalar(
        select(func.count()).select_from(Alarm)
    ) or 0

    pending = db.scalar(
        select(func.count()).select_from(Alarm).where(Alarm.status == "pending")
    ) or 0

    handled = db.scalar(
        select(func.count()).select_from(Alarm).where(Alarm.status == "handled")
    ) or 0

    since_24h = datetime.utcnow() - timedelta(hours=24)

    recent_24h = db.scalar(
        select(func.count()).select_from(Alarm).where(Alarm.created_at >= since_24h)
    ) or 0

    status_rows = db.execute(
        select(Alarm.status, func.count(Alarm.id)).group_by(Alarm.status)
    ).all()

    event_type_rows = db.execute(
        select(Alarm.event_type, func.count(Alarm.id)).group_by(Alarm.event_type)
    ).all()

    camera_rows = db.execute(
        select(Alarm.camera_id, func.count(Alarm.id)).group_by(Alarm.camera_id)
    ).all()

    latest_alarms = db.scalars(
        select(Alarm)
        .order_by(Alarm.created_at.desc())
        .limit(latest_limit)
    ).all()

    data = AlarmStatisticsData(
        total=total,
        pending=pending,
        handled=handled,
        recent_24h=recent_24h,
        by_status={
            str(status): count
            for status, count in status_rows
            if status is not None
        },
        by_event_type={
            str(event_type): count
            for event_type, count in event_type_rows
            if event_type is not None
        },
        by_camera_id={
            str(camera_id): count
            for camera_id, count in camera_rows
            if camera_id is not None
        },
        latest_alarms=[
            AlarmOut.model_validate(alarm)
            for alarm in latest_alarms
        ],
    )

    return ApiResponse[AlarmStatisticsData](
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
