import time

from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.api.routes_alarms import router as alarms_router
from app.api.routes_cameras import router as cameras_router
from app.api.routes_devices import router as devices_router
from app.api.routes_inference import router as inference_router
from app.api.routes_models import router as models_router
from app.core.config import settings
from app.core.metrics import HTTP_REQUEST_DURATION_SECONDS, HTTP_REQUESTS_TOTAL
from app.db.init_db import init_db

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI safety detection backend powered by YOLOv8 and ONNX Runtime.",
)

app.include_router(inference_router)
app.include_router(devices_router)
app.include_router(cameras_router)
app.include_router(alarms_router)
app.include_router(models_router)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    path = request.url.path
    method = request.method

    response = await call_next(request)

    duration = time.perf_counter() - start_time

    HTTP_REQUESTS_TOTAL.labels(
        method=method,
        path=path,
        status_code=str(response.status_code),
    ).inc()

    HTTP_REQUEST_DURATION_SECONDS.labels(
        method=method,
        path=path,
    ).observe(duration)

    return response


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def root():
    return {
        "message": settings.app_name,
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics",
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "industrial-ai-safety-backend",
        "version": settings.app_version,
        "env": settings.app_env,
    }


@app.get("/metrics")
def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
