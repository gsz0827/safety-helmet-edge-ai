import cv2
import numpy as np

from edge.config_loader import load_config
from edge.onnx_detector import OnnxDetector


class InferenceService:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = load_config(config_path)
        self.detector = OnnxDetector(self.config)

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

        return {
            "image_width": image.shape[1],
            "image_height": image.shape[0],
            "detections": detections,
            "inference_time_ms": inference_time_ms,
        }


inference_service = InferenceService()
