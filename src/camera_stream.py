import cv2


class CameraStream:
    def __init__(self, config):
        self.video_url = config["video"]["video_url"]
        self.cap = None

    def open(self):
        print("正在打开视频流：", self.video_url)

        self.cap = cv2.VideoCapture(self.video_url)

        if not self.cap.isOpened():
            raise RuntimeError("无法打开视频流，请检查 config.yaml 中的 video_url。")

        print("视频流打开成功。")

    def read(self):
        if self.cap is None:
            raise RuntimeError("视频流尚未打开，请先调用 open()。")

        ret, frame = self.cap.read()

        if not ret:
            return None

        return frame

    def release(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            print("视频流已释放。")