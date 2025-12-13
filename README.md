YOLOv8 Safety Helmet Detection

This project implements a Safety Helmet Detection System using YOLOv8.
The model is trained to detect whether construction workers are wearing a helmet or not using a dataset originally sourced from Kaggle (Hard Hat Workers Dataset).

📌 Project Overview

Task: Object Detection

Model: YOLOv8

Framework: Ultralytics

Dataset Format: YOLOv8

Classes:

0 → helmet

1 → no_helmet (head)

The project converts Pascal VOC (.xml) annotations into YOLO format, trains a YOLOv8 model, and evaluates its performance using Precision, Recall, and mAP50.

YOLOv8-csc/
│
├── dataset/
│ ├── images/ # Original images
│ ├── annotations/ # Pascal VOC (.xml) annotations
│ ├── yolo_labels/ # Converted YOLO labels (.txt)
│
├── data/
│ ├── train/
│ │ ├── images/
│ │ └── labels/
│ ├── val/
│ │ ├── images/
│ │ └── labels/
│
├── voc_to_yolo.py # Converts VOC XML → YOLO format
├── split_dataset.py # Splits dataset into train/validation
├── data.yaml # YOLO dataset configuration
├── requirements.txt # Python dependencies
├── .gitignore
└── README.md

Environment Setup
1️⃣ Create Virtual Environment (Recommended)
python -m venv venv

Activate:

Windows

venv\Scripts\activate

Install Dependencies
pip install -r requirements.txt

Dataset Source

The dataset is sourced from Kaggle:

🔗 https://www.kaggle.com/datasets/andrewmvd/hard-hat-detection

It contains:

~5,000 images

Pascal VOC annotations

Labels: helmet, head, person

Only helmet and head are used in this project.

Convert Annotations to YOLO Format

Run the conversion script:

python voc_to_yolo.py

This will:

Read .xml annotation files

Convert bounding boxes to YOLO format

Skip unused labels such as person

Save .txt labels to dataset/yolo_labels/

Split Dataset (Train / Validation)

Run:

python split_dataset.py

This will:

Create data/train and data/val folders

Copy images and labels into YOLO-ready structure

Dataset Configuration (data.yaml)

Example:

path: data
train: train/images
val: val/images

names:
0: helmet
1: no_helmet

Training the YOLOv8 Model

Train the model for 20–50 epochs:

yolo detect train model=yolov8n.pt data=data.yaml epochs=40 imgsz=640

Training outputs will be saved automatically in:

runs/detect/train/

📊 Evaluation Metrics

After training, YOLOv8 automatically generates:
Precision (P)

Recall (R)

mAP@0.5

mAP@0.5:0.95

Confusion Matrix

Training Curves

These results are used for performance evaluation and reporting.

🔍 Inference (Testing)

To test the trained model on an image or video:

yolo detect predict model=runs/detect/train/weights/best.pt source=your_image.jpg
