from fastapi import FastAPI

from app.api.routes_alarms import router as alarms_router
from app.api.routes_inference import router as inference_router
from app.core.config import settings
from app.db.init_db import init_db

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI safety detection backend powered by YOLOv8 and ONNX Runtime.",
)

app.include_router(inference_router)
app.include_router(alarms_router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def root():
    return {
        "message": settings.app_name,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "industrial-ai-safety-backend",
        "version": settings.app_version,
        "env": settings.app_env,
    }
