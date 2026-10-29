"""Priority score for a road-damage report (0-100). Higher = fix first.

Input: the detector's boxes for ONE image, plus the image size.
Each detection is a dict: {"cls": "D40", "x": ..., "y": ..., "w": ..., "h": ..., "conf": 0.9}
(x, y = top-left corner in pixels; w, h = box width/height in pixels.)

Formula (draft v1, weights/limits are proposals to be re-checked on real detector output):
    priority = 100 * (0.45*type + 0.20*size + 0.20*count + 0.15*conf)
    type  = highest class weight among the boxes (D40=1.0, D20=0.8, D10=0.5, D00=0.4)
    size  = sum of box areas / image area / 0.25, capped at 1
    count = number of boxes / 5, capped at 1
    conf  = mean confidence of the boxes
"""

CLASS_WEIGHT = {"D40": 1.0, "D20": 0.8, "D10": 0.5, "D00": 0.4}
WEIGHTS = {"type": 0.45, "size": 0.20, "count": 0.20, "conf": 0.15}
SIZE_FULL = 0.25   # boxes covering >= 25% of the image count as size = 1
COUNT_FULL = 5     # >= 5 boxes count as count = 1


def priority_score(detections, img_w, img_h, weights=WEIGHTS):
    """Return the priority (0-100) for one image. No detections -> 0.0."""
    if not detections:
        return 0.0
    if img_w <= 0 or img_h <= 0:
        raise ValueError("image width/height must be positive")
    for d in detections:
        if d["cls"] not in CLASS_WEIGHT:
            raise ValueError(f"unknown class {d['cls']!r}; expected one of {sorted(CLASS_WEIGHT)}")
        if not 0.0 <= d["conf"] <= 1.0:
            raise ValueError(f"confidence must be in [0, 1], got {d['conf']}")

    type_f = max(CLASS_WEIGHT[d["cls"]] for d in detections)
    area = sum(d["w"] * d["h"] for d in detections) / (img_w * img_h)
    size_f = min(area / SIZE_FULL, 1.0)
    count_f = min(len(detections) / COUNT_FULL, 1.0)
    conf_f = sum(d["conf"] for d in detections) / len(detections)

    feats = {"type": type_f, "size": size_f, "count": count_f, "conf": conf_f}
    total_w = sum(weights.values())
    return 100 * sum(weights[k] * feats[k] for k in weights) / total_w


if __name__ == "__main__":
    # quick self-check on the worked examples (image 1000x500)
    W, H = 1000, 500
    a = [{"cls": "D00", "x": 0, "y": 0, "w": 100, "h": 100, "conf": 0.6}]       # 2% of image
    b = [{"cls": "D40", "x": 0, "y": 0, "w": 250, "h": 200, "conf": 0.9}]       # 10%
    c = [{"cls": "D40", "x": 0, "y": 0, "w": 173, "h": 173, "conf": 0.95}] * 5  # ~30% total
    for name, dets in (("A thin crack", a), ("B pothole 10%", b), ("C 5 potholes", c)):
        print(f"{name:15s} {priority_score(dets, W, H):5.1f}")
