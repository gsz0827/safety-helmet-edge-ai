import cv2
import time
import numpy as np
import onnxruntime as ort


class OnnxDetector:
    def __init__(self, config):
        model_config = config["model"]
        detect_config = config["detect"]

        self.model_path = model_config["model_path"]
        self.input_size = model_config["input_size"]
        self.class_names = model_config["class_names"]

        self.conf_threshold = detect_config["conf_threshold"]
        self.iou_threshold = detect_config["iou_threshold"]

        print("正在加载 ONNX 模型...")
        print("Model:", self.model_path)

        self.session = ort.InferenceSession(
            self.model_path,
            providers=["CPUExecutionProvider"]
        )

        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name

        print("ONNX Runtime providers:", self.session.get_providers())
        print("Input name:", self.input_name)
        print("Output name:", self.output_name)

    def letterbox(self, image, color=(114, 114, 114)):
        h, w = image.shape[:2]

        scale = min(self.input_size / h, self.input_size / w)

        new_w = int(round(w * scale))
        new_h = int(round(h * scale))

        resized = cv2.resize(
            image,
            (new_w, new_h),
            interpolation=cv2.INTER_LINEAR
        )

        dw = self.input_size - new_w
        dh = self.input_size - new_h

        dw /= 2
        dh /= 2

        top = int(round(dh - 0.1))
        bottom = int(round(dh + 0.1))
        left = int(round(dw - 0.1))
        right = int(round(dw + 0.1))

        padded = cv2.copyMakeBorder(
            resized,
            top,
            bottom,
            left,
            right,
            cv2.BORDER_CONSTANT,
            value=color
        )

        return padded, scale, left, top

    def preprocess(self, frame):
        img, scale, pad_x, pad_y = self.letterbox(frame)

        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = img.transpose(2, 0, 1)
        img = img.astype(np.float32) / 255.0
        img = np.expand_dims(img, axis=0)

        return img, scale, pad_x, pad_y

    @staticmethod
    def xywh_to_xyxy(box):
        x, y, w, h = box

        x1 = x - w / 2
        y1 = y - h / 2
        x2 = x + w / 2
        y2 = y + h / 2

        return [x1, y1, x2, y2]

    def postprocess(self, output, original_shape, scale, pad_x, pad_y):
        predictions = output

        if predictions.ndim == 3:
            predictions = predictions[0]

        expected_dim = 4 + len(self.class_names)

        if predictions.shape[0] == expected_dim:
            predictions = predictions.T
        elif predictions.shape[1] == expected_dim:
            pass
        else:
            raise ValueError(f"Unexpected ONNX output shape: {predictions.shape}")

        boxes = []
        scores = []
        class_ids = []

        original_h, original_w = original_shape[:2]

        for pred in predictions:
            box = pred[:4]
            class_scores = pred[4:]

            class_id = int(np.argmax(class_scores))
            confidence = float(class_scores[class_id])

            if confidence < self.conf_threshold:
                continue

            x1, y1, x2, y2 = self.xywh_to_xyxy(box)

            x1 = (x1 - pad_x) / scale
            y1 = (y1 - pad_y) / scale
            x2 = (x2 - pad_x) / scale
            y2 = (y2 - pad_y) / scale

            x1 = max(0, min(original_w - 1, x1))
            y1 = max(0, min(original_h - 1, y1))
            x2 = max(0, min(original_w - 1, x2))
            y2 = max(0, min(original_h - 1, y2))

            w = x2 - x1
            h = y2 - y1

            if w <= 0 or h <= 0:
                continue

            boxes.append([int(x1), int(y1), int(w), int(h)])
            scores.append(confidence)
            class_ids.append(class_id)

        indices = cv2.dnn.NMSBoxes(
            boxes,
            scores,
            self.conf_threshold,
            self.iou_threshold
        )

        detections = []

        if len(indices) > 0:
            for i in np.array(indices).flatten():
                x, y, w, h = boxes[i]
                class_id = class_ids[i]
                confidence = scores[i]

                detections.append({
                    "class_id": class_id,
                    "class_name": self.class_names[class_id],
                    "confidence": confidence,
                    "box": [x, y, x + w, y + h]
                })

        return detections

    def detect(self, frame):
        input_tensor, scale, pad_x, pad_y = self.preprocess(frame)

        start_time = time.perf_counter()

        outputs = self.session.run(
            [self.output_name],
            {self.input_name: input_tensor}
        )

        end_time = time.perf_counter()

        inference_time_ms = (end_time - start_time) * 1000

        detections = self.postprocess(
            outputs[0],
            frame.shape,
            scale,
            pad_x,
            pad_y
        )

        return detections, inference_time_ms