"""Evaluation on the team-built local test set (YOLO labels) and automatic error analysis.

Matching rule (standard for detection): a prediction and a ground-truth box match when their
IoU >= 0.5. Each ground-truth box is matched at most once, highest-confidence predictions first.
Error categories:
  - missed      : ground-truth damage with no prediction of any class at IoU >= 0.5 (FN)
  - wrong_class : a prediction overlaps a ground-truth box (IoU >= 0.5) but with another class
  - false_alarm : a prediction that overlaps no ground-truth box (FP)
"""
from PIL import ImageDraw

CLASSES = ["D00", "D10", "D20", "D40"]


def read_yolo_labels(text, img_w, img_h):
    """YOLO txt (class cx cy w h, normalised) -> list of {cls, x, y, w, h} in pixels."""
    boxes = []
    for line in text.strip().splitlines():
        parts = line.split()
        if len(parts) < 5:
            continue
        c, cx, cy, w, h = int(float(parts[0])), *map(float, parts[1:5])
        if c < 0 or c >= len(CLASSES):
            continue
        boxes.append({"cls": CLASSES[c], "x": (cx - w / 2) * img_w, "y": (cy - h / 2) * img_h,
                      "w": w * img_w, "h": h * img_h})
    return boxes


def iou(a, b):
    ax2, ay2, bx2, by2 = a["x"] + a["w"], a["y"] + a["h"], b["x"] + b["w"], b["y"] + b["h"]
    iw = max(0.0, min(ax2, bx2) - max(a["x"], b["x"]))
    ih = max(0.0, min(ay2, by2) - max(a["y"], b["y"]))
    inter = iw * ih
    union = a["w"] * a["h"] + b["w"] * b["h"] - inter
    return inter / union if union > 0 else 0.0


def match_image(gts, preds, iou_thr=0.5):
    """Returns per-image results: tp/fp/fn per class, confusion pairs and error list."""
    preds = sorted(preds, key=lambda d: -d.get("conf", 1.0))
    used = set()
    tp, fp, fn = ({c: 0 for c in CLASSES} for _ in range(3))
    confusion = []  # (true class or "background", predicted class or "background")
    errors = []
    for p in preds:
        best, best_j = 0.0, None
        for j, g in enumerate(gts):  # same class first
            if j not in used and g["cls"] == p["cls"]:
                v = iou(p, g)
                if v > best:
                    best, best_j = v, j
        if best >= iou_thr:
            used.add(best_j)
            tp[p["cls"]] += 1
            confusion.append((p["cls"], p["cls"]))
            continue
        best, best_j = 0.0, None  # any class: wrong label on a real damage?
        for j, g in enumerate(gts):
            if j not in used:
                v = iou(p, g)
                if v > best:
                    best, best_j = v, j
        fp[p["cls"]] += 1
        if best >= iou_thr:
            used.add(best_j)
            fn[gts[best_j]["cls"]] += 1
            confusion.append((gts[best_j]["cls"], p["cls"]))
            errors.append({"category": "wrong_class", "true": gts[best_j]["cls"],
                           "pred": p["cls"], "conf": p.get("conf"), "box": p,
                           "gt_box": gts[best_j]})
        else:
            confusion.append(("background", p["cls"]))
            errors.append({"category": "false_alarm", "true": "background", "pred": p["cls"],
                           "conf": p.get("conf"), "box": p})
    for j, g in enumerate(gts):
        if j not in used:
            fn[g["cls"]] += 1
            confusion.append((g["cls"], "background"))
            errors.append({"category": "missed", "true": g["cls"], "pred": "background",
                           "conf": None, "box": g})
    return {"tp": tp, "fp": fp, "fn": fn, "confusion": confusion, "errors": errors}


def summarise(results):
    """Per-class precision / recall / F1 over all images."""
    rows = []
    for c in CLASSES:
        tp = sum(r["tp"][c] for r in results)
        fp = sum(r["fp"][c] for r in results)
        fn = sum(r["fn"][c] for r in results)
        p = tp / (tp + fp) if tp + fp else 0.0
        r_ = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * p * r_ / (p + r_) if p + r_ else 0.0
        rows.append({"Class": c, "Ground truth": tp + fn, "TP": tp, "FP": fp, "FN": fn,
                     "Precision": round(p, 3), "Recall": round(r_, 3), "F1": round(f1, 3)})
    return rows


def draw_boxes(image, gts, preds):
    """Ground truth in green, predictions in red (labels = class codes)."""
    out = image.convert("RGB").copy()
    d = ImageDraw.Draw(out)
    lw = max(3, out.width // 120)
    for g in gts:
        d.rectangle([g["x"], g["y"], g["x"] + g["w"], g["y"] + g["h"]], outline=(46, 204, 113),
                    width=lw)
        d.text((g["x"] + 4, g["y"] + 4), f"GT {g['cls']}", fill=(46, 204, 113))
    for p in preds:
        d.rectangle([p["x"], p["y"], p["x"] + p["w"], p["y"] + p["h"]], outline=(231, 76, 60),
                    width=lw)
        d.text((p["x"] + 4, p["y"] + p["h"] - 14), f"{p['cls']} {p.get('conf', 0):.2f}",
               fill=(231, 76, 60))
    return out
