"""One place for the RoadScan pipeline used by the citizen and technical pages:
photo -> YOLO (team model) -> blur faces/plates -> priority -> duplicate search -> save report."""
import time

import streamlit as st

from duplicates import add_report, find_matches
from location import format_place, place_details
from priority import priority_score
from privacy import blur_boxes, find_sensitive
from reports import load_extra, save_report_details
from utils import band, detect, open_photo


def crops(img, dets, margin=0.10):
    out = []
    for d in dets:
        mx, my = d["w"] * margin, d["h"] * margin
        out.append((d["cls"], img.crop((max(0, d["x"] - mx), max(0, d["y"] - my),
                                         min(img.width, d["x"] + d["w"] + mx),
                                         min(img.height, d["y"] + d["h"] + my)))))
    return out


def analyse(uploaded, model, conf, blur_on=True):
    """Run detection, blurring and priority on one uploaded photo. Returns a dict or None."""
    timing = {}
    t_all = time.perf_counter()
    photo = open_photo(uploaded)
    if photo is None:
        return None
    image = photo.convert("RGB")
    t0 = time.perf_counter()
    annotated, df, dets = detect(model, image, conf)
    timing["Damage detection (YOLO)"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    sensitive = find_sensitive(image) if blur_on else []
    shown = blur_boxes(image, sensitive) if sensitive else image
    shown_annotated = blur_boxes(annotated, sensitive) if sensitive else annotated
    timing["Face and plate blurring"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    score = round(priority_score(dets, image.width, image.height), 1)
    label, action, color = band(score)
    timing["Priority score"] = time.perf_counter() - t0
    return {"image": image, "shown": shown, "annotated": shown_annotated, "df": df,
            "dets": dets, "score": score, "label": label, "action": action, "color": color,
            "sensitive": sensitive, "timing": timing, "t_all": t_all}


def open_matches(image, dets, lat, lon):
    """Duplicate candidates among OPEN reports only (repaired/rejected ones are ignored)."""
    if not dets:
        return [], 0.0
    t0 = time.perf_counter()
    matches = find_matches(image, dets, lat, lon)
    secs = time.perf_counter() - t0
    extra = load_extra()
    keep = [m for m in matches if m["id"] in extra  # ignore leftovers saved before the queue
            and extra[m["id"]].get("status", "new") not in ("repaired", "rejected")]
    return keep, secs


def save_new(uploaded, A, location, source="citizen", description=""):
    """Store a new open report (fingerprints + details + blurred thumbnails). Returns its id."""
    lat, lon = location if location else (None, None)
    new_id = add_report(uploaded.name, A["image"], A["dets"], lat, lon, A["score"])
    info = place_details(lat, lon) if lat is not None else None
    save_report_details(new_id, {
        "image": uploaded.name, "priority": A["score"], "decision": A["label"],
        "damages": len(A["dets"]), "classes": sorted({d["cls"] for d in A["dets"]}),
        "address": format_place(info), "lat": lat, "lon": lon, "source": source,
        "description": description, "model": st.session_state.get("model_name"),
        "seconds": round(time.perf_counter() - A["t_all"], 2),
        "boxes": [{k: (round(v, 3) if isinstance(v, float) else v) for k, v in d.items()}
                  for d in A["dets"]]},
        thumb=A["annotated"], crops=crops(A["shown"], A["dets"]))
    return new_id
