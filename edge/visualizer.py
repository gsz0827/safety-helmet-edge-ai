import cv2


class Visualizer:
    def __init__(self):
        pass

    def draw_detections(self, frame, detections):
        for det in detections:
            x1, y1, x2, y2 = det["box"]
            class_name = det["class_name"]
            confidence = det["confidence"]

            if class_name == "no_helmet":
                color = (0, 0, 255)
            else:
                color = (0, 255, 0)

            label = f"{class_name} {confidence:.2f}"

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            cv2.putText(
                frame,
                label,
                (x1, max(25, y1 - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                color,
                2
            )

        return frame

    def draw_status(self, frame, fps, inference_time_ms):
        text = f"FPS: {fps:.2f} | Inference: {inference_time_ms:.2f} ms"

        cv2.putText(
            frame,
            text,
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )

        return frame

    def show(self, window_name, frame):
        cv2.imshow(window_name, frame)

    def should_quit(self):
        return cv2.waitKey(1) & 0xFF == ord("q")

    def close(self):
        cv2.destroyAllWindows()