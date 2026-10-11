import os
import xml.etree.ElementTree as ET
from collections import Counter

ROOT = r"C:\RDD2022\RDD2022"
COUNTRIES = ["Czech", "China_MotorBike", "China_Drone", "India", "Japan", "United_States"]
MAIN = ["D00", "D10", "D20", "D40"]

summary = {}
all_other = Counter()

for country in COUNTRIES:
    xml_dir = os.path.join(ROOT, country, country, "train", "annotations", "xmls")
    if not os.path.isdir(xml_dir):
        print(country, "-> folder not found:", xml_dir)
        continue

    images_with = Counter()
    other = Counter()
    total = 0
    empty = 0
    for name in os.listdir(xml_dir):
        if not name.endswith(".xml"):
            continue
        total += 1
        tree = ET.parse(os.path.join(xml_dir, name))
        labels = [o.find("name").text.strip() for o in tree.findall("object")]
        if not labels:
            empty += 1
        for lab in set(labels):
            if lab in MAIN:
                images_with[lab] += 1
            else:
                other[lab] += 1
    all_other.update(other)
    summary[country] = (total, empty, images_with)

print()
print("Images that contain each class (per country)")
print("%-16s %7s %7s %7s %7s %7s %7s" % ("country", "images", "empty", "D00", "D10", "D20", "D40"))
tot = Counter()
for c, (t, e, iw) in summary.items():
    print("%-16s %7d %7d %7d %7d %7d %7d" % (c, t, e, iw["D00"], iw["D10"], iw["D20"], iw["D40"]))
    tot["images"] += t
    tot["empty"] += e
    for k in MAIN:
        tot[k] += iw[k]
print("-" * 70)
print("%-16s %7d %7d %7d %7d %7d %7d" % ("TOTAL", tot["images"], tot["empty"], tot["D00"], tot["D10"], tot["D20"], tot["D40"]))
print()
print("Extra classes found (images containing them):", dict(all_other))