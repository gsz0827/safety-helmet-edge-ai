from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.common import ApiResponse
from app.schemas.inference import ImageInferenceData, ImageInferenceResponse
from app.services.inference_service import inference_service

router = APIRouter(
    prefix="/api/v1/inference",
    tags=["Inference"],
)


@router.post("/image", response_model=ImageInferenceResponse)
async def infer_image(file: UploadFile = File(...)):
    try:
        result = inference_service.detect_image_bytes(
            await file.read()
        )

        data = ImageInferenceData(
            filename=file.filename or "",
            **result,
        )

        return ApiResponse[ImageInferenceData](
            code=0,
            message="success",
            data=data,
        )

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Inference failed: {exc}")
