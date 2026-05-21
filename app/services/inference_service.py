from threading import Lock
from typing import Any

import cv2
import numpy as np

from app.core.config import settings
from edge.config_loader import load_config
from edge.onnx_detector import OnnxDetector


class InferenceService:
    def __init__(self):
        self.config_path = settings.edge_config_path
        self.config: dict[str, Any] | None = None
        self.detector: OnnxDetector | None = None
        self.load_error: str | None = None
        self._lock = Lock()

    def _load_config_with_overrides(self) -> dict[str, Any]:
        config = load_config(self.config_path)

        config.setdefault("model", {})
        config.setdefault("detect", {})

        if settings.model_path:
            config["model"]["model_path"] = settings.model_path

        if settings.model_input_size:
            config["model"]["input_size"] = settings.model_input_size

        if settings.model_class_names:
            config["model"]["class_names"] = [
                name.strip()
                for name in settings.model_class_names.split(",")
                if name.strip()
            ]

        if settings.detect_conf_threshold is not None:
            config["detect"]["conf_threshold"] = settings.detect_conf_threshold

        if settings.detect_iou_threshold is not None:
            config["detect"]["iou_threshold"] = settings.detect_iou_threshold

        return config

    def _ensure_config_loaded(self):
        if self.config is None:
            self.config = self._load_config_with_overrides()

    def _ensure_detector_loaded(self):
        if self.detector is not None:
            return

        with self._lock:
            if self.detector is not None:
                return

            try:
                self._ensure_config_loaded()
                self.detector = OnnxDetector(self.config)
                self.load_error = None
            except Exception as exc:
                self.load_error = str(exc)
                raise

    def get_status(self) -> dict[str, Any]:
        try:
            self._ensure_config_loaded()
            model_config = self.config.get("model", {}) if self.config else {}

            class_names = model_config.get("class_names") or []
            if isinstance(class_names, str):
                class_names = [
                    name.strip()
                    for name in class_names.split(",")
                    if name.strip()
                ]

            return {
                "model_loaded": self.detector is not None,
                "edge_config_path": self.config_path,
                "model_path": model_config.get("model_path"),
                "input_size": model_config.get("input_size"),
                "class_names": class_names,
                "load_error": self.load_error,
            }

        except Exception as exc:
            return {
                "model_loaded": False,
                "edge_config_path": self.config_path,
                "model_path": None,
                "input_size": None,
                "class_names": [],
                "load_error": str(exc),
            }

    def _to_builtin(self, value: Any):
        if isinstance(value, np.generic):
            return value.item()

        if isinstance(value, np.ndarray):
            return value.tolist()

        if isinstance(value, dict):
            return {
                key: self._to_builtin(item)
                for key, item in value.items()
            }

        if isinstance(value, (list, tuple)):
            return [
                self._to_builtin(item)
                for item in value
            ]

        return value

    def detect_image_bytes(self, image_bytes: bytes):
        self._ensure_detector_loaded()

        np_array = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

        if image is None:
            raise ValueError("Invalid image file")

        result = self.detector.detect(image)

        if isinstance(result, tuple):
            detections = result[0]
            inference_time_ms = result[1] if len(result) > 1 else None
        else:
            detections = result
            inference_time_ms = None

        detections = self._to_builtin(detections)

        if inference_time_ms is not None:
            inference_time_ms = float(inference_time_ms)

        return {
            "image_width": int(image.shape[1]),
            "image_height": int(image.shape[0]),
            "detections": detections,
            "inference_time_ms": inference_time_ms,
        }


inference_service = InferenceService()
