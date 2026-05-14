from src.camera_stream import CameraStream


class MultiCameraManager:
    def __init__(self, config):
        self.config = config
        self.cameras = []

        video_config = config.get("video", {})
        streams = video_config.get("streams", [])

        # 兼容旧版 config.yaml: video.video_url
        if not streams and video_config.get("video_url"):
            streams = [
                {
                    "camera_id": video_config.get("camera_id", "cam_01"),
                    "camera_name": video_config.get("camera_name", "default"),
                    "url": video_config.get("video_url"),
                    "enabled": True,
                }
            ]

        for stream_config in streams:
            if not stream_config.get("enabled", True):
                continue

            camera = CameraStream(config, stream_config)
            self.cameras.append(camera)

        if not self.cameras:
            raise RuntimeError("没有可用摄像头，请检查 config.yaml 中 video.streams 配置。")

    def open_all(self):
        opened_cameras = []

        for camera in self.cameras:
            try:
                camera.open()
                opened_cameras.append(camera)
            except Exception as exc:
                print(
                    f"摄像头打开失败 [{camera.camera_id} - {camera.camera_name}]: {exc}"
                )

        self.cameras = opened_cameras

        if not self.cameras:
            raise RuntimeError("所有摄像头都打开失败，系统无法启动。")

        print(f"已成功打开 {len(self.cameras)} 路摄像头。")

    def read_all(self):
        frames = []

        for camera in self.cameras:
            frame = camera.read()

            if frame is None:
                print(f"读取视频帧失败 [{camera.camera_id} - {camera.camera_name}]。")
                continue

            frames.append(
                {
                    "camera_id": camera.camera_id,
                    "camera_name": camera.camera_name,
                    "source_url": camera.video_url,
                    "frame": frame,
                }
            )

        return frames

    def release_all(self):
        for camera in self.cameras:
            camera.release()