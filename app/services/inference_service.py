from typing import Any

import cv2
import numpy as np

from app.core.config import settings
from edge.config_loader import load_config
from edge.onnx_detector import OnnxDetector


class InferenceService:
    def __init__(self):
        self.config = load_config(settings.edge_config_path)
        self._apply_settings_overrides()
        self.detector = OnnxDetector(self.config)

    def _apply_settings_overrides(self):
        self.config.setdefault("model", {})
        self.config.setdefault("detect", {})

        if settings.model_path:
            self.config["model"]["model_path"] = settings.model_path

        if settings.model_input_size:
            self.config["model"]["input_size"] = settings.model_input_size

        if settings.model_class_names:
            self.config["model"]["class_names"] = [
                name.strip()
                for name in settings.model_class_names.split(",")
                if name.strip()
            ]

        if settings.detect_conf_threshold is not None:
            self.config["detect"]["conf_threshold"] = settings.detect_conf_threshold

        if settings.detect_iou_threshold is not None:
            self.config["detect"]["iou_threshold"] = settings.detect_iou_threshold

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
