from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.inference_service import inference_service

router = APIRouter(
    prefix="/api/v1/inference",
    tags=["Inference"],
)


@router.post("/image")
async def infer_image(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        result = inference_service.detect_image_bytes(image_bytes)

        return {
            "ok": True,
            "filename": file.filename,
            **result,
        }

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Inference failed: {exc}")
