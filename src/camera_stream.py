import cv2


class CameraStream:
    def __init__(self, config, stream_config=None):
        self.config = config

        if stream_config is None:
            video_config = config.get("video", {})
            self.camera_id = video_config.get("camera_id", "cam_01")
            self.camera_name = video_config.get("camera_name", "default")
            self.video_url = video_config.get("video_url")
        else:
            self.camera_id = stream_config.get("camera_id", "unknown_camera")
            self.camera_name = stream_config.get("camera_name", self.camera_id)
            self.video_url = stream_config.get("url")

        if not self.video_url:
            raise ValueError(f"摄像头 {self.camera_id} 缺少 url / video_url 配置。")

        self.cap = None

    def open(self):
        print(f"正在打开视频流 [{self.camera_id} - {self.camera_name}]: {self.video_url}")

        self.cap = cv2.VideoCapture(self.video_url)

        if not self.cap.isOpened():
            raise RuntimeError(
                f"无法打开视频流 [{self.camera_id} - {self.camera_name}]，请检查视频地址。"
            )

        print(f"视频流打开成功 [{self.camera_id} - {self.camera_name}]。")

    def read(self):
        if self.cap is None:
            raise RuntimeError(
                f"视频流 [{self.camera_id} - {self.camera_name}] 尚未打开，请先调用 open()。"
            )

        ret, frame = self.cap.read()
        if not ret:
            return None

        return frame

    def release(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            print(f"视频流已释放 [{self.camera_id} - {self.camera_name}]。")