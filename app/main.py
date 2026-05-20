from fastapi import FastAPI

app = FastAPI(
    title="Industrial AI Safety Backend",
    version="0.1.0",
    description="AI safety detection backend powered by YOLOv8 and ONNX Runtime.",
)


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
