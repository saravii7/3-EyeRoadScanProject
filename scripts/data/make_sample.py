"""
make_sample.py
ينشئ عينة التدريب (600 صورة: 200 لكل دولة) من Dataset roadscan-yolo.
يشتغل داخل دفتر Kaggle بعد ربط الـ Dataset.
seed ثابت = 42، عشان تطلع نفس العينة عند الجميع.
"""
import os, random, shutil

SRC = "/kaggle/input/datasets/sarvii7/roadscan-yolo/RoadScan_yolo"
DST = "/kaggle/working/sample600"
SEED = 42
PER_COUNTRY = 200
COUNTRIES = ["Japan", "India", "Czech"]
MAX_EMPTY_FRAC = 0.15   # أقصى نسبة صور بدون ضرر

random.seed(SEED)
for part in ["train", "val"]:
    os.makedirs(f"{DST}/{part}/images", exist_ok=True)
    os.makedirs(f"{DST}/{part}/labels", exist_ok=True)

img_dir = f"{SRC}/train/images"
lbl_dir = f"{SRC}/train/labels"
names = sorted(os.listdir(img_dir))

chosen = []
for c in COUNTRIES:
    pool = [n[:-4] for n in names if n.startswith(c + "_") and n.endswith(".jpg")]
    full, empty = [], []
    for stem in pool:
        size = os.path.getsize(f"{lbl_dir}/{stem}.txt")
        (full if size > 0 else empty).append(stem)
    n_empty = int(PER_COUNTRY * MAX_EMPTY_FRAC)
    pick = random.sample(full, PER_COUNTRY - n_empty) + random.sample(empty, n_empty)
    chosen += pick
    print(c, "| with damage:", PER_COUNTRY - n_empty, "| empty:", n_empty)

for stem in chosen:
    shutil.copy(f"{img_dir}/{stem}.jpg", f"{DST}/train/images/{stem}.jpg")
    shutil.copy(f"{lbl_dir}/{stem}.txt", f"{DST}/train/labels/{stem}.txt")

# val (الصين) ننسخه كاملاً
for n in os.listdir(f"{SRC}/val/images"):
    shutil.copy(f"{SRC}/val/images/{n}", f"{DST}/val/images/{n}")
    shutil.copy(f"{SRC}/val/labels/{n[:-4]}.txt", f"{DST}/val/labels/{n[:-4]}.txt")

with open("/kaggle/working/sample600_list.txt", "w") as f:
    f.write("\n".join(sorted(chosen)))

yaml = f"""path: {DST}
train: train/images
val: val/images
names:
  0: D00
  1: D10
  2: D20
  3: D40
"""
open("/kaggle/working/data.yaml", "w").write(yaml)
print("train:", len(chosen), "| val:", len(os.listdir(f"{DST}/val/images")))
