import os
import shutil
import xml.etree.ElementTree as ET
from collections import Counter

ROOT = r"C:\RDD2022\RDD2022"
OUT = r"C:\RoadScan_yolo"
TRAIN_COUNTRIES = ["Japan", "India", "Czech", "China_MotorBike"]
TEST_COUNTRIES = ["United_States"]
CLASS_MAP = {"D00": 0, "D10": 1, "D20": 2, "D40": 3}

def convert(country, split_name):
    src_img = os.path.join(ROOT, country, country, "train", "images")
    src_xml = os.path.join(ROOT, country, country, "train", "annotations", "xmls")
    dst_img = os.path.join(OUT, split_name, "images")
    dst_lbl = os.path.join(OUT, split_name, "labels")
    os.makedirs(dst_img, exist_ok=True)
    os.makedirs(dst_lbl, exist_ok=True)

    stats = Counter()
    for name in os.listdir(src_xml):
        if not name.endswith(".xml"):
            continue
        stem = name[:-4]
        img_path = os.path.join(src_img, stem + ".jpg")
        if not os.path.exists(img_path):
            stats["missing_image"] += 1
            continue

        root = ET.parse(os.path.join(src_xml, name)).getroot()
        w = float(root.find("size/width").text)
        h = float(root.find("size/height").text)

        lines = []
        for obj in root.findall("object"):
            cls = obj.find("name").text.strip()
            if cls not in CLASS_MAP:
                stats["ignored_boxes"] += 1
                continue
            b = obj.find("bndbox")
            x1 = max(0.0, float(b.find("xmin").text))
            y1 = max(0.0, float(b.find("ymin").text))
            x2 = min(w, float(b.find("xmax").text))
            y2 = min(h, float(b.find("ymax").text))
            if x2 <= x1 or y2 <= y1:
                stats["bad_boxes"] += 1
                continue
            cx = (x1 + x2) / 2 / w
            cy = (y1 + y2) / 2 / h
            bw = (x2 - x1) / w
            bh = (y2 - y1) / h
            lines.append("%d %.6f %.6f %.6f %.6f" % (CLASS_MAP[cls], cx, cy, bw, bh))
            stats["kept_boxes"] += 1

        if not lines:
            stats["images_without_kept_boxes"] += 1
        shutil.copy2(img_path, os.path.join(dst_img, stem + ".jpg"))
        with open(os.path.join(dst_lbl, stem + ".txt"), "w") as f:
            f.write("\n".join(lines))
        stats["images"] += 1
    return stats

for c in TRAIN_COUNTRIES:
    print(c, "->", dict(convert(c, "trainval")))
for c in TEST_COUNTRIES:
    print(c, "->", dict(convert(c, "test_US")))
print("Done. Output folder:", OUT)
