import json
import time
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.metrics import (
    AI_INFERENCE_DURATION_SECONDS,
    AI_INFERENCE_ERRORS_TOTAL,
    AI_INFERENCE_REQUESTS_TOTAL,
    ALARM_CREATED_TOTAL,
)
from app.db.models import Alarm
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.inference import (
    ImageInferenceData,
    ImageInferenceResponse,
    InferenceStatusData,
    InferenceStatusResponse,
)
from app.services.inference_service import inference_service

router = APIRouter(
    prefix="/api/v1/inference",
    tags=["Inference"],
)


def _get_detection_class_name(det: dict[str, Any]) -> str:
    value = (
        det.get("class_name")
        or det.get("label")
        or det.get("name")
        or det.get("class")
        or ""
    )
    return str(value)


def _get_detection_confidence(det: dict[str, Any]) -> float:
    value = (
        det.get("confidence")
        or det.get("score")
        or det.get("conf")
        or 0.0
    )
    return float(value)


def _get_detection_box(det: dict[str, Any]):
    return (
        det.get("box")
        or det.get("bbox")
        or det.get("xyxy")
        or det.get("rect")
    )


def _find_top_no_helmet_detection(
    detections: list[dict[str, Any]],
) -> dict[str, Any] | None:
    candidates = []

    for det in detections:
        class_name = _get_detection_class_name(det)

        if class_name == "no_helmet":
            candidates.append(det)

    if not candidates:
        return None

    return max(
        candidates,
        key=_get_detection_confidence,
    )


@router.get("/status", response_model=InferenceStatusResponse)
def get_inference_status():
    data = InferenceStatusData(
        **inference_service.get_status()
    )

    return ApiResponse[InferenceStatusData](
        code=0,
        message="success",
        data=data,
    )


@router.post("/image", response_model=ImageInferenceResponse)
async def infer_image(
    file: UploadFile = File(...),
    device_id: str = Form(default="edge_ai_001"),
    camera_id: str | None = Form(default=None),
    create_alarm: bool = Form(default=True),
    db: Session = Depends(get_db),
):
    AI_INFERENCE_REQUESTS_TOTAL.inc()
    start_time = time.perf_counter()

    try:
        result = inference_service.detect_image_bytes(
            await file.read()
        )

        detections = result.get("detections", [])
        top_no_helmet = _find_top_no_helmet_detection(detections)

        alarm_created = False
        alarm_id = None

        if create_alarm and top_no_helmet is not None:
            alarm = Alarm(
                device_id=device_id,
                camera_id=camera_id,
                event_type="no_helmet",
                confidence=_get_detection_confidence(top_no_helmet),
                image_url=None,
                bbox_json=json.dumps(
                    _get_detection_box(top_no_helmet),
                    ensure_ascii=False,
                ),
                inference_time_ms=result.get("inference_time_ms"),
                fps=None,
            )

            db.add(alarm)
            db.commit()
            db.refresh(alarm)

            alarm_created = True
            alarm_id = alarm.id

            ALARM_CREATED_TOTAL.labels(
                source="inference",
                event_type="no_helmet",
            ).inc()

        data = ImageInferenceData(
            filename=file.filename or "",
            image_width=result["image_width"],
            image_height=result["image_height"],
            detections=detections,
            inference_time_ms=result.get("inference_time_ms"),
            alarm_created=alarm_created,
            alarm_id=alarm_id,
        )

        return ApiResponse[ImageInferenceData](
            code=0,
            message="success",
            data=data,
        )

    except ValueError as exc:
        AI_INFERENCE_ERRORS_TOTAL.inc()
        raise HTTPException(status_code=400, detail=str(exc))

    except Exception as exc:
        AI_INFERENCE_ERRORS_TOTAL.inc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Inference failed: {exc}")

    finally:
        AI_INFERENCE_DURATION_SECONDS.observe(
            time.perf_counter() - start_time
        )
