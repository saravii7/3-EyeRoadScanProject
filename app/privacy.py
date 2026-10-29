"""Blur faces and licence plates before anything is shown or saved (Brief: Responsible AI).

Uses OpenCV Haar cascades (BSD licence) stored in models/privacy/. They are fast and run on
CPU, but they are not perfect: side faces and Saudi plates at an angle can be missed.
The road damage detector always runs on the ORIGINAL photo; only what we display or store
is blurred.
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

_DIR = Path(__file__).parent / "models" / "privacy"
_FILES = {"face": "haarcascade_frontalface_default.xml",
          "plate": "haarcascade_russian_plate_number.xml"}
_DETECT_MAX_SIDE = 1280  # detect on a smaller copy for speed, then scale boxes back


def _cascades():
    import cv2
    out = {}
    if not hasattr(cv2, "CascadeClassifier"):  # OpenCV 5 builds may not ship it
        return out
    for kind, name in _FILES.items():
        path = _DIR / name
        if path.exists():
            c = cv2.CascadeClassifier(str(path))
            if not c.empty():
                out[kind] = c
    return out


try:  # load once per Streamlit process
    import streamlit as st
    _cascades = st.cache_resource(_cascades)
except Exception:  # pragma: no cover
    pass


def find_sensitive(image: Image.Image):
    """Boxes (x1, y1, x2, y2, kind) of faces and plates in the original image's pixels."""
    import cv2
    try:
        cascades = _cascades()
    except Exception:
        cascades = {}
    if not cascades:
        return []
    scale = min(1.0, _DETECT_MAX_SIDE / max(image.size))
    small = image.convert("L")
    if scale < 1.0:
        small = small.resize((int(image.width * scale), int(image.height * scale)))
    gray = cv2.equalizeHist(np.asarray(small))
    boxes = []
    params = {"face": dict(scaleFactor=1.1, minNeighbors=6, minSize=(24, 24)),
              "plate": dict(scaleFactor=1.1, minNeighbors=5, minSize=(40, 12))}
    for kind, c in cascades.items():
        for (x, y, w, h) in c.detectMultiScale(gray, **params[kind]):
            boxes.append((int(x / scale), int(y / scale), int((x + w) / scale),
                          int((y + h) / scale), kind))
    return boxes


def blur_available():
    """True when the face/plate detectors loaded (needs OpenCV 4.x: pip install "opencv-python<5")."""
    try:
        return bool(_cascades())
    except Exception:
        return False


def blur_boxes(image: Image.Image, boxes, pad=0.15):
    """Return a copy of image with each box strongly blurred."""
    out = image.copy()
    for x1, y1, x2, y2, _ in boxes:
        px, py = int((x2 - x1) * pad), int((y2 - y1) * pad)
        box = (max(0, x1 - px), max(0, y1 - py), min(out.width, x2 + px), min(out.height, y2 + py))
        region = out.crop(box)
        radius = max(8, (box[2] - box[0]) // 6)
        out.paste(region.filter(ImageFilter.GaussianBlur(radius)), box)
    return out


def count_by_kind(boxes):
    return {"faces": sum(b[4] == "face" for b in boxes),
            "plates": sum(b[4] == "plate" for b in boxes)}
