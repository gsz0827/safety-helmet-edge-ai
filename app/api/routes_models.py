from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.db.models import ModelVersion
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.model_version import (
    ModelVersionCreate,
    ModelVersionCreateResponse,
    ModelVersionDetailResponse,
    ModelVersionListData,
    ModelVersionListResponse,
    ModelVersionOut,
)

router = APIRouter(
    prefix="/api/v1/models",
    tags=["Models"],
)


@router.post("", response_model=ModelVersionCreateResponse)
def create_model_version(
    payload: ModelVersionCreate,
    db: Session = Depends(get_db),
):
    if payload.is_active:
        db.execute(
            update(ModelVersion).values(
                is_active=False,
                updated_at=datetime.utcnow(),
            )
        )

    model_version = ModelVersion(**payload.model_dump())

    db.add(model_version)
    db.commit()
    db.refresh(model_version)

    return ApiResponse[ModelVersionOut](
        code=0,
        message="success",
        data=ModelVersionOut.model_validate(model_version),
    )


@router.get("", response_model=ModelVersionListResponse)
def list_model_versions(
    name: str | None = Query(default=None),
    framework: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    stmt = select(ModelVersion)
    count_stmt = select(func.count()).select_from(ModelVersion)

    if name:
        stmt = stmt.where(ModelVersion.name == name)
        count_stmt = count_stmt.where(ModelVersion.name == name)

    if framework:
        stmt = stmt.where(ModelVersion.framework == framework)
        count_stmt = count_stmt.where(ModelVersion.framework == framework)

    if is_active is not None:
        stmt = stmt.where(ModelVersion.is_active == is_active)
        count_stmt = count_stmt.where(ModelVersion.is_active == is_active)

    total = db.scalar(count_stmt) or 0

    model_versions = db.scalars(
        stmt.order_by(ModelVersion.created_at.desc()).offset(offset).limit(limit)
    ).all()

    data = ModelVersionListData(
        total=total,
        limit=limit,
        offset=offset,
        items=[
            ModelVersionOut.model_validate(model_version)
            for model_version in model_versions
        ],
    )

    return ApiResponse[ModelVersionListData](
        code=0,
        message="success",
        data=data,
    )


@router.get("/active", response_model=ModelVersionDetailResponse)
def get_active_model_version(db: Session = Depends(get_db)):
    model_version = db.scalar(
        select(ModelVersion).where(ModelVersion.is_active == True)
    )

    if model_version is None:
        raise HTTPException(status_code=404, detail="Active model not found")

    return ApiResponse[ModelVersionOut](
        code=0,
        message="success",
        data=ModelVersionOut.model_validate(model_version),
    )


@router.get("/{model_id}", response_model=ModelVersionDetailResponse)
def get_model_version(model_id: int, db: Session = Depends(get_db)):
    model_version = db.get(ModelVersion, model_id)

    if model_version is None:
        raise HTTPException(status_code=404, detail="Model version not found")

    return ApiResponse[ModelVersionOut](
        code=0,
        message="success",
        data=ModelVersionOut.model_validate(model_version),
    )


@router.patch("/{model_id}/activate", response_model=ModelVersionDetailResponse)
def activate_model_version(model_id: int, db: Session = Depends(get_db)):
    model_version = db.get(ModelVersion, model_id)

    if model_version is None:
        raise HTTPException(status_code=404, detail="Model version not found")

    db.execute(
        update(ModelVersion).values(
            is_active=False,
            updated_at=datetime.utcnow(),
        )
    )

    model_version.is_active = True
    model_version.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(model_version)

    return ApiResponse[ModelVersionOut](
        code=0,
        message="success",
        data=ModelVersionOut.model_validate(model_version),
    )
