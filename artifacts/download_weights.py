"""
download_weights.py
يحمّل أوزان الـ baseline وملف الإعدادات من GitHub Release (v1-baseline).
الاستخدام:  python artifacts/download_weights.py
ملاحظة: يشتغل مباشرة لما يكون الريبو Public.
"""
import os
import urllib.request

REPO = "saravii7/3-EyeRoadScanProject"
TAG = "v1-baseline"
FILES = ["baseline_resnet18.pt", "baseline_config.json"]
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

for name in FILES:
    url = f"https://github.com/{REPO}/releases/download/{TAG}/{name}"
    dest = os.path.join(OUT_DIR, name)
    if os.path.exists(dest):
        print("موجود:", name)
        continue
    print("تحميل:", name)
    urllib.request.urlretrieve(url, dest)
print("تم. الملفات في:", OUT_DIR)
