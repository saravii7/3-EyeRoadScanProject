"""
download_weights.py
يحمّل أوزان baseline وملف الإعدادات من GitHub Releases:
  v1-baseline  (600 صورة)
  v2-baseline  (8,999 صورة)
الاستخدام:  python artifacts/download_weights.py
ملاحظة: يشتغل مباشرة لما يكون الريبو Public.
"""
import os
import urllib.request

REPO = "saravii7/3-EyeRoadScanProject"

RELEASES = {
    "v1-baseline": ["baseline_resnet18.pt", "baseline_config.json"],
    "v2-baseline": ["baseline_v2_resnet18.pt", "baseline_v2_config.json"],
}

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

for tag, files in RELEASES.items():
    for name in files:
        dest = os.path.join(OUT_DIR, name)
        if os.path.exists(dest):
            print("موجود:", name)
            continue
        print("تحميل:", name)
        url = f"https://github.com/{REPO}/releases/download/{tag}/{name}"
        urllib.request.urlretrieve(url, dest)

print("تم. الملفات في:", OUT_DIR)
