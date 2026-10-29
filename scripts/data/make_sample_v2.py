"""
make_sample_v2.py
عينة التدريب v2: 9,000 صورة (اليابان 4,000 + الهند 3,500 + التشيك 1,500)
seed ثابت = 42. يعطي أولوية للصور اللي فيها الفئات النادرة (D10, D40).
يشتغل داخل دفتر Kaggle بعد ربط الـ Dataset roadscan-yolo.
"""
import os, random, shutil
from collections import Counter

SRC = "/kaggle/input/datasets/sarvii7/roadscan-yolo/RoadScan_yolo"
DST = "/kaggle/working/sample9000"
SEED = 42
PLAN = {"Japan": 4000, "India": 3500, "Czech": 1500}
EMPTY_FRAC = {"Japan": 0.125, "India": 0.143, "Czech": 0.285}
names = ["D00", "D10", "D20", "D40"]

random.seed(SEED)
for part in ["train", "val"]:
    os.makedirs(f"{DST}/{part}/images", exist_ok=True)
    os.makedirs(f"{DST}/{part}/labels", exist_ok=True)

img_dir = f"{SRC}/train/images"
lbl_dir = f"{SRC}/train/labels"
files = sorted(os.listdir(lbl_dir))

def classes(stem):
    return {int(l.split()[0]) for l in open(f"{lbl_dir}/{stem}.txt") if l.strip()}

chosen = []
for c, total in PLAN.items():
    stems = [f[:-4] for f in files if f.startswith(c + "_")]
    full, empty = [], []
    for s in stems:
        (full if classes(s) else empty).append(s)
    n_empty = min(int(total * EMPTY_FRAC[c]), len(empty))
    n_full = min(total - n_empty, len(full))
    rare = [s for s in full if classes(s) & {1, 3}]
    rest = [s for s in full if s not in set(rare)]
    random.shuffle(rare); random.shuffle(rest)
    pick = (rare + rest)[:n_full] + random.sample(empty, n_empty)
    chosen += pick
    print(c, "| with damage:", n_full, "| empty:", n_empty)

for s in chosen:
    shutil.copy(f"{img_dir}/{s}.jpg", f"{DST}/train/images/{s}.jpg")
    shutil.copy(f"{lbl_dir}/{s}.txt", f"{DST}/train/labels/{s}.txt")

# val (الصين) كامل
for n in os.listdir(f"{SRC}/val/images"):
    shutil.copy(f"{SRC}/val/images/{n}", f"{DST}/val/images/{n}")
    shutil.copy(f"{SRC}/val/labels/{n[:-4]}.txt", f"{DST}/val/labels/{n[:-4]}.txt")

open("/kaggle/working/sample9000_list.txt", "w").write("\n".join(sorted(chosen)))
open("/kaggle/working/data.yaml", "w").write(f"""path: {DST}
train: train/images
val: val/images
names:
  0: D00
  1: D10
  2: D20
  3: D40
""")

tot = Counter()
for s in chosen:
    for c in classes(s):
        tot[names[c]] += 1
print("train:", len(chosen), "| val:", len(os.listdir(f"{DST}/val/images")))
print("images containing each class:", dict(tot))
