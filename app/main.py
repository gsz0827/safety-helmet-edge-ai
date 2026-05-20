from fastapi import FastAPI

from app.api.routes_inference import router as inference_router

app = FastAPI(
    title="Industrial AI Safety Backend",
    version="0.1.0",
    description="AI safety detection backend powered by YOLOv8 and ONNX Runtime.",
)

app.include_router(inference_router)


@app.get("/")
def root():
    return {
        "message": "Industrial AI Safety Backend",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "industrial-ai-safety-backend",
        "version": "0.1.0",
    }
