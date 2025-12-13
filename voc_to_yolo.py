import os
import xml.etree.ElementTree as ET

IMG_DIR = 'dataset/images'
ANN_DIR = 'dataset/annotations'
OUT_LABELS = 'dataset/yolo_labels'

os.makedirs(OUT_LABELS, exist_ok=True)

# ✔ Classes you want to detect
# 0 = helmet, 1 = no helmet (head)
classes = {"helmet": 0, "head": 1}

for xml_file in os.listdir(ANN_DIR):
    if not xml_file.endswith(".xml"):
        continue

    xml_path = os.path.join(ANN_DIR, xml_file)
    tree = ET.parse(xml_path)
    root = tree.getroot()

    filename = root.find('filename').text
    txt_filename = filename.replace(".png", ".txt").replace(".jpg", ".txt")
    txt_path = os.path.join(OUT_LABELS, txt_filename)

    size = root.find("size")
    img_w = int(size.find("width").text)
    img_h = int(size.find("height").text)

    with open(txt_path, "w") as f:
        for obj in root.findall("object"):
            name = obj.find("name").text

          
            if name not in classes:
                print(f"Skipping unknown label: {name} in {xml_file}")
                continue

            cls = classes[name]

            bbox = obj.find("bndbox")
            xmin = int(bbox.find("xmin").text)
            ymin = int(bbox.find("ymin").text)
            xmax = int(bbox.find("xmax").text)
            ymax = int(bbox.find("ymax").text)

            # YOLO FORMAT
            x_center = (xmin + xmax) / 2 / img_w
            y_center = (ymin + ymax) / 2 / img_h
            width = (xmax - xmin) / img_w
            height = (ymax - ymin) / img_h

            # Write YOLO Label
            f.write(f"{cls} {x_center} {y_center} {width} {height}\n")

print("✅ YOLO labels successfully generated!")
