"""Duplicate finder for RoadScan: is a new report a copy of an open one?

Pipeline: crop each detected box -> DINOv2-small fingerprint (frozen, L2-normalised)
-> search open reports -> keep those of the SAME class, within radius_m metres
(if both have GPS) and with cosine similarity >= threshold.

Usage (Streamlit page, after `location = location_section(uploaded)`):

    from duplicates import find_matches, add_report
    lat, lon = location if location else (None, None)
    matches = find_matches(image, dets, lat, lon)      # image = PIL image, dets = detector output
    if matches:   # best first
        m = matches[0]
        st.warning(f"Likely duplicate of #{m['id']} (similarity {m['similarity']:.2f})")
    else:
        st.success("New report")
    if st.button("Add to open reports"):
        add_report(image_name, image, dets, lat, lon, priority)

`dets`: list of {"cls": "D40", "x":..., "y":..., "w":..., "h":..., "conf":...}
(pixels, x/y = top-left corner), same format as utils.detect().

THRESHOLD (0.80) and RADIUS_M (30) were tuned in E5.
THRESHOLD_NO_GPS (0.92) was chosen on the tuning pairs only and measured once on the test pairs (E5).
"""
import json
import math
from pathlib import Path

import numpy as np

MODEL_NAME = "facebook/dinov2-small"
DIM = 384
MARGIN = 0.10             # extra context around each box (10 %)
RADIUS_M = 30             # search radius for reports that have GPS
THRESHOLD = 0.80          # cosine similarity, with GPS    (tuned in E5)
THRESHOLD_NO_GPS = 0.92   # stricter when we cannot use distance (tuned in E5).
DATA_DIR = Path("data/reports")

try:  # cache the model across Streamlit reruns; plain functools cache elsewhere
    import streamlit as st
    _cache = st.cache_resource
except Exception:  # pragma: no cover
    from functools import lru_cache
    _cache = lru_cache(maxsize=1)


# ---------------------------------------------------------------- fingerprints
@_cache
def load_embedder():
    """Load DINOv2-small once (CPU, no training). Returns (processor, model)."""
    from transformers import AutoImageProcessor, AutoModel
    proc = AutoImageProcessor.from_pretrained(MODEL_NAME)
    model = AutoModel.from_pretrained(MODEL_NAME).eval()
    return proc, model


def _fingerprint(pil_img, embedder):
    import torch
    proc, model = embedder
    inputs = proc(images=pil_img, return_tensors="pt")
    with torch.no_grad():
        out = model(**inputs)
    v = out.last_hidden_state[:, 0]                       # CLS token
    v = torch.nn.functional.normalize(v, dim=-1)          # L2-normalised
    return v[0].numpy()


def embed_crops(image, dets, embedder=None, margin=MARGIN):
    """One normalised 384-d vector per detection (crop = box + `margin` context)."""
    if not dets:
        return []
    embedder = embedder or load_embedder()
    W, H = image.size
    vecs = []
    for d in dets:
        mx, my = d["w"] * margin, d["h"] * margin
        box = (max(0, d["x"] - mx), max(0, d["y"] - my),
               min(W, d["x"] + d["w"] + mx), min(H, d["y"] + d["h"] + my))
        vecs.append(_fingerprint(image.crop(box).convert("RGB"), embedder))
    return vecs


# -------------------------------------------------------------------- geometry
def distance_m(a, b):
    """Distance in metres between two (lat, lon) points (haversine)."""
    R = 6371000
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp, dl = p2 - p1, math.radians(b[1] - a[1])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


# ----------------------------------------------------------------------- store
class ReportStore:
    """Open reports: one fingerprint per detected box, with report id, class, lat/lon,
    priority and image name. Search uses FAISS (inner product = cosine on unit vectors).
    Saved to <data_dir>/vectors.npy + meta.json."""

    def __init__(self, data_dir=DATA_DIR):
        import faiss
        self.dir = Path(data_dir)
        self.index = faiss.IndexFlatIP(DIM)
        self.meta = []
        self._load()

    # persistence
    def _load(self):
        vec_path, meta_path = self.dir / "vectors.npy", self.dir / "meta.json"
        if vec_path.exists() and meta_path.exists():
            vecs = np.load(vec_path).astype("float32")
            self.meta = json.loads(meta_path.read_text())
            if len(vecs) != len(self.meta):
                raise ValueError("data/reports is corrupted: vectors and meta differ in length")
            if len(vecs):
                self.index.add(vecs)

    def _save(self):
        self.dir.mkdir(parents=True, exist_ok=True)
        n = self.index.ntotal
        vecs = self.index.reconstruct_n(0, n) if n else np.zeros((0, DIM), "float32")
        np.save(self.dir / "vectors.npy", vecs)
        (self.dir / "meta.json").write_text(json.dumps(self.meta, indent=1))

    # API
    def next_id(self):
        return max((m["id"] for m in self.meta), default=0) + 1

    def add_report(self, report_id, vecs, dets, lat=None, lon=None,
                   priority=None, image_name=None):
        """Add one report (all its boxes). Returns the report id."""
        if len(vecs) != len(dets):
            raise ValueError("need one vector per detection")
        for v, d in zip(vecs, dets):
            self.index.add(np.asarray([v], dtype="float32"))
            self.meta.append({"id": report_id, "cls": d["cls"], "lat": lat, "lon": lon,
                              "priority": priority, "image": image_name})
        self._save()
        return report_id

    def find_matches(self, vecs, dets, lat=None, lon=None, radius_m=RADIUS_M,
                     threshold=THRESHOLD, threshold_no_gps=THRESHOLD_NO_GPS):
        """Open reports that look like this one, best first. One entry per report:
        {"id", "similarity", "distance_m" (None if no GPS), "cls"}."""
        if self.index.ntotal == 0 or not vecs:
            return []
        have_gps = lat is not None and lon is not None
        best = {}
        for v, d in zip(vecs, dets):
            k = min(self.index.ntotal, 50)
            scores, ids = self.index.search(np.asarray([v], dtype="float32"), k)
            for s, i in zip(scores[0], ids[0]):
                m = self.meta[i]
                if m["cls"] != d["cls"]:
                    continue
                if have_gps and m["lat"] is not None:
                    dist = distance_m((lat, lon), (m["lat"], m["lon"]))
                    if dist > radius_m or s < threshold:
                        continue
                else:                      # either side has no GPS: look at the shape only
                    dist = None
                    if s < threshold_no_gps:
                        continue
                if m["id"] not in best or s > best[m["id"]]["similarity"]:
                    best[m["id"]] = {"id": m["id"], "similarity": float(s),
                                     "distance_m": dist, "cls": m["cls"]}
        return sorted(best.values(), key=lambda x: -x["similarity"])


# ------------------------------------------- convenience wrappers for the page
@_cache
def get_store():
    return ReportStore()


def find_matches(image, dets, lat=None, lon=None, radius_m=RADIUS_M,
                 threshold=THRESHOLD, threshold_no_gps=THRESHOLD_NO_GPS):
    """Fingerprint the new image's boxes and search the open reports."""
    vecs = embed_crops(image, dets)
    return get_store().find_matches(vecs, dets, lat, lon, radius_m,
                                    threshold, threshold_no_gps)


def add_report(image_name, image, dets, lat=None, lon=None, priority=None):
    """Save this image as a new open report. Returns its report id."""
    store = get_store()
    vecs = embed_crops(image, dets)
    return store.add_report(store.next_id(), vecs, dets, lat, lon, priority, image_name)
