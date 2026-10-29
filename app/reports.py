"""Open-report queue for the app.

The team's duplicate finder (duplicates.py) stores one DINOv2 vector per damage box in
data/reports/vectors.npy + meta.json. This module keeps the extra, app-only details next to it
(data/reports/extra.json + blurred thumbnails in data/reports/thumbs/) and builds the
work queue: one row per report, sorted by priority (highest first).
It never changes how duplicates.py searches.
"""
import base64
import io
import json
import shutil
import time
from pathlib import Path

import numpy as np
import pandas as pd

from duplicates import DATA_DIR

REPORTS_DIR = Path(DATA_DIR)
EXTRA = REPORTS_DIR / "extra.json"
THUMBS = REPORTS_DIR / "thumbs"


# ------------------------------------------------------------------ storage
def _read_json(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return default


def load_extra():
    return {int(k): v for k, v in _read_json(EXTRA, {}).items()}


def _write_extra(extra):
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    EXTRA.write_text(json.dumps({str(k): v for k, v in extra.items()}, ensure_ascii=False,
                                indent=1), encoding="utf-8")


def save_report_details(report_id, info, thumb=None, crops=None):
    """info: dict (address, decision, classes, ...). thumb: blurred PIL image of the result.
    crops: list of (class, blurred PIL crop) used as evidence for later duplicate matches."""
    THUMBS.mkdir(parents=True, exist_ok=True)
    extra = load_extra()
    now = time.strftime("%Y-%m-%d %H:%M")
    info = dict(info, id=report_id, added=now, times_reported=1, status="new",
                history=[{"time": now, "by": info.get("source", "citizen"),
                          "event": "created"}])
    if thumb is not None:
        t = thumb.copy()
        t.thumbnail((640, 640))
        t.save(THUMBS / f"{report_id}.jpg", quality=85)
    for i, (cls, crop) in enumerate(crops or []):
        c = crop.copy()
        c.thumbnail((320, 320))
        c.save(THUMBS / f"{report_id}_{i}_{cls}.jpg", quality=85)
    extra[report_id] = info
    _write_extra(extra)


def link_duplicate(report_id):
    """A citizen reported damage that is already open: count it, don't create a new report."""
    extra = load_extra()
    if report_id in extra:
        now = time.strftime("%Y-%m-%d %H:%M")
        extra[report_id]["times_reported"] = extra[report_id].get("times_reported", 1) + 1
        extra[report_id]["last_reported"] = now
        extra[report_id].setdefault("history", []).append(
            {"time": now, "by": "citizen", "event": "repeat_report"})
        _write_extra(extra)


def thumb_path(report_id):
    p = THUMBS / f"{report_id}.jpg"
    return p if p.exists() else None


def crop_path(report_id, cls):
    hits = sorted(THUMBS.glob(f"{report_id}_*_{cls}.jpg"))
    return hits[0] if hits else None


def as_data_uri(path):
    if not path:
        return None
    return "data:image/jpeg;base64," + base64.b64encode(Path(path).read_bytes()).decode()


# -------------------------------------------------------------------- queue
def load_queue():
    """One row per open report, highest priority first, with its queue position."""
    meta = _read_json(REPORTS_DIR / "meta.json", [])
    if not meta:
        return pd.DataFrame()
    extra = load_extra()
    rows = {}
    for m in meta:
        r = rows.setdefault(m["id"], {"id": m["id"], "image": m.get("image"), "lat": m.get("lat"),
                                      "lon": m.get("lon"), "priority": m.get("priority"),
                                      "classes": set()})
        r["classes"].add(m["cls"])
    out = []
    for rid, r in rows.items():
        e = extra.get(rid, {})
        if e.get("status", "new") in ("repaired", "rejected"):
            continue
        out.append({**r, "classes": ", ".join(sorted(r["classes"])),
                    "decision": e.get("decision"), "address": e.get("address"),
                    "damages": e.get("damages"), "times_reported": e.get("times_reported", 1),
                    "added": e.get("added"), "location_source": e.get("location_source"),
                    "status": e.get("status", "new"), "team": e.get("team")})
    q = pd.DataFrame(out)
    if q.empty:
        return q
    q["priority"] = pd.to_numeric(q["priority"], errors="coerce").fillna(0)
    q = q.sort_values(["priority", "times_reported", "id"], ascending=[False, False, True])
    q.insert(0, "position", range(1, len(q) + 1))
    return q.reset_index(drop=True)


def queue_position(report_id):
    q = load_queue()
    if q.empty or report_id not in set(q["id"]):
        return None, len(q)
    return int(q.loc[q["id"] == report_id, "position"].iloc[0]), len(q)


def to_geojson(q):
    feats = []
    for _, r in q.iterrows():
        if pd.isna(r["lat"]) or pd.isna(r["lon"]) or r["lat"] is None:
            continue
        props = {k: (None if (isinstance(v, float) and np.isnan(v)) else v)
                 for k, v in r.items() if k not in ("lat", "lon")}
        props = {k: (int(v) if isinstance(v, (np.integer,)) else
                     float(v) if isinstance(v, (np.floating,)) else v) for k, v in props.items()}
        feats.append({"type": "Feature",
                      "geometry": {"type": "Point", "coordinates": [float(r["lon"]), float(r["lat"])]},
                      "properties": props})
    return json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False, indent=1)


# ----------------------------------------------------------- remove / reset
def remove_reports(ids):
    """Mark reports as repaired: drop their vectors, meta, details and thumbnails."""
    ids = set(int(i) for i in ids)
    vec_path, meta_path = REPORTS_DIR / "vectors.npy", REPORTS_DIR / "meta.json"
    meta = _read_json(meta_path, [])
    if meta and vec_path.exists():
        vecs = np.load(vec_path)
        keep = [i for i, m in enumerate(meta) if m["id"] not in ids]
        np.save(vec_path, vecs[keep] if keep else np.zeros((0, vecs.shape[1]), "float32"))
        meta_path.write_text(json.dumps([meta[i] for i in keep], indent=1))
    extra = load_extra()
    for i in ids:
        extra.pop(i, None)
        for p in THUMBS.glob(f"{i}.jpg"):
            p.unlink()
        for p in THUMBS.glob(f"{i}_*.jpg"):
            p.unlink()
    _write_extra(extra)
    _reset_store_cache()


def clear_all():
    if REPORTS_DIR.exists():
        shutil.rmtree(REPORTS_DIR)
    _reset_store_cache()


def _reset_store_cache():
    """duplicates.get_store() is cached by Streamlit; reload it from disk next time."""
    try:
        from duplicates import get_store
        get_store.clear()
    except Exception:
        pass


def image_to_jpeg_bytes(img):
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


# ------------------------------------------------- municipal workflow
def get_report(report_id):
    return load_extra().get(int(report_id))


def update_report(report_id, actor="البلدية", event=None, **fields):
    """Change status / team / schedule etc. and log the change in the report history."""
    extra = load_extra()
    rid = int(report_id)
    if rid not in extra:
        return
    r = extra[rid]
    r.update({k: v for k, v in fields.items()})
    if event:
        r.setdefault("history", []).append({"time": time.strftime("%Y-%m-%d %H:%M"),
                                            "by": actor, "event": event})
    _write_extra(extra)
    if event:
        try:
            from notify import on_event  # WhatsApp updates to citizens who opted in
            on_event(rid, event)
        except Exception:
            pass  # a notification problem must never block the municipality's work


def add_note(report_id, text, actor="البلدية"):
    extra = load_extra()
    rid = int(report_id)
    if rid in extra and text.strip():
        extra[rid].setdefault("notes", []).append({"time": time.strftime("%Y-%m-%d %H:%M"),
                                                   "by": actor, "text": text.strip()})
        _write_extra(extra)


def all_reports():
    """Every report (open and closed) as a DataFrame, newest first."""
    extra = load_extra()
    if not extra:
        return pd.DataFrame()
    rows = []
    for rid, e in extra.items():
        rows.append({"id": rid, "status": e.get("status", "new"), "priority": e.get("priority", 0),
                     "decision": e.get("decision"), "classes": ", ".join(e.get("classes", [])),
                     "address": e.get("address"), "lat": e.get("lat"), "lon": e.get("lon"),
                     "team": e.get("team"), "scheduled_for": e.get("scheduled_for"),
                     "added": e.get("added"), "times_reported": e.get("times_reported", 1),
                     "damages": e.get("damages"), "seconds": e.get("seconds"),
                     "source": e.get("source", "citizen"), "repaired_at": e.get("repaired_at")})
    df = pd.DataFrame(rows)
    df["priority"] = pd.to_numeric(df["priority"], errors="coerce").fillna(0)
    return df.sort_values("id", ascending=False).reset_index(drop=True)
