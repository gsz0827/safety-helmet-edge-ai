from ultralytics import YOLO

model = YOLO("yolov8n.pt")  # nano version (fast)

model.train(
    data="helmet.yaml",
    epochs=30,
    imgsz=640,
    batch=16
)
