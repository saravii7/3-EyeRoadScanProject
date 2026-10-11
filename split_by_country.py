import os
import shutil

BASE = r"C:\RoadScan_yolo"
SRC_IMG = os.path.join(BASE, "trainval", "images")
SRC_LBL = os.path.join(BASE, "trainval", "labels")

for part in ["train", "val"]:
    os.makedirs(os.path.join(BASE, part, "images"), exist_ok=True)
    os.makedirs(os.path.join(BASE, part, "labels"), exist_ok=True)

counts = {"train": 0, "val": 0}
for name in os.listdir(SRC_IMG):
    if not name.endswith(".jpg"):
        continue
    stem = name[:-4]
    part = "val" if name.startswith("China_MotorBike") else "train"
    shutil.move(os.path.join(SRC_IMG, name), os.path.join(BASE, part, "images", name))
    shutil.move(os.path.join(SRC_LBL, stem + ".txt"), os.path.join(BASE, part, "labels", stem + ".txt"))
    counts[part] += 1

yaml = """path: /kaggle/input/roadscan-yolo
train: train/images
val: val/images
test: test_US/images
names:
  0: D00
  1: D10
  2: D20
  3: D40
"""
with open(os.path.join(BASE, "data.yaml"), "w") as f:
    f.write(yaml)

print(counts)
print("Done.")