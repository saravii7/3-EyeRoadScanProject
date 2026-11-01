"""Shared helpers for the RoadScan 3-Eye app: model loading, detection, priority, styling, GPS."""
import math
from pathlib import Path

import pandas as pd
import streamlit as st
from PIL import Image, ExifTags, ImageOps

try:  # iPhone HEIC photos
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass

from priority import CLASS_WEIGHT, priority_score  # the team's formula (copied from the repo)

APP_DIR = Path(__file__).parent
MODELS_DIR = APP_DIR / "models"
ACCENT = "#1EC7B6"

# RDD2022 classes used in our project
CLASS_INFO = {
    "D00": {"name": "Longitudinal crack", "ar": "شق طولي", "color": "#4FC3F7"},
    "D10": {"name": "Transverse crack", "ar": "شق عرضي", "color": "#81C784"},
    "D20": {"name": "Alligator crack", "ar": "تشقق تمساحي", "color": "#FFB74D"},
    "D40": {"name": "Pothole", "ar": "حفرة", "color": "#E57373"},
}

# Some checkpoints (e.g. the external run-15 YOLOv8s) use long names instead of D-codes.
CLASS_ALIASES = {
    "longitudinal_crack": "D00", "transverse_crack": "D10",
    "alligator_crack": "D20", "pothole": "D40",
}

# Priority bands (0-100, higher = fix first). Thresholds are a UI proposal, not from the report.
BANDS = [
    (70, "Urgent", "Repair this week", "#D95B55"),
    (40, "Schedule", "Add to maintenance plan", "#F3B548"),
    (0, "Monitor", "Re-check later", "#43A878"),
]


# ---------- Styling ----------
NAVY, INK, MUTED, LINE, SOFT = "#082B36", "#111827", "#758199", "#E6EBF2", "#F5F7FB"
PLOT = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color=INK)


def apply_style(rtl=None):
    """3-Eye look: light civic palette, navy sidebar, teal accent. Arabic pages run RTL."""
    if rtl is None:
        rtl = st.session_state.get("lang", "ar") == "ar"
    direction = f"""
        .main .block-container, [data-testid="stMain"] {{direction: rtl; text-align: right;}}
        [data-testid="stMain"] [data-testid="stDataFrame"], [data-testid="stMain"] pre,
        [data-testid="stMain"] code, .ltr {{direction: ltr; text-align: left;}}
        [data-testid="stSidebar"] {{direction: rtl; text-align: right;}}
    """ if rtl else ""
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&display=swap');
        html, body, [class*="css"], .stApp, .stMarkdown, button, input, textarea, select {{
            font-family: 'IBM Plex Sans Arabic', sans-serif !important;}}
        #MainMenu, footer {{visibility: hidden;}}
        .block-container {{padding-top: 2rem;}}
        [data-testid="stSidebar"] {{background: {NAVY};}}
        [data-testid="stSidebar"] * {{color: #E9EEF7;}}
        [data-testid="stSidebar"] [data-testid="stSidebarNavSeparator"] {{border-color: #14404D;}}
        [data-testid="stSidebar"] input, [data-testid="stSidebar"] [data-baseweb="select"] * {{color: {INK};}}
        [data-testid="stSidebar"] button {{background: transparent; border: 1px solid #2A5966;}}
        [data-testid="stSidebar"] button:hover {{border-color: {ACCENT};}}
        .hero {{
            padding: 2rem 2.2rem; border-radius: 22px; color: white;
            background: linear-gradient(135deg, {NAVY} 0%, #0E3B48 55%, {ACCENT} 160%);
            margin-bottom: 1.5rem; box-shadow: 0 16px 44px rgba(19,36,65,.12);
        }}
        .hero h1 {{margin: 0; font-size: 2.4rem; color: white;}}
        .hero-brand {{display: flex; align-items: center; gap: 2rem; flex-wrap: wrap;}}
        .hero-brand img {{width: 210px; max-width: 45%; border-radius: 18px;}}
        .hero-brand p {{flex: 1; min-width: 220px; font-size: 1.25rem; color: #F4F6F5;}}
        [data-testid="stSidebarHeader"] img, [data-testid="stLogo"] {{height: 3.2rem;}}
        .hero p {{color: #A6BBC0; font-size: 1.1rem; margin-top: .4rem;}}
        .card {{
            background: white; border: 1px solid {LINE}; border-radius: 16px;
            padding: 1.1rem 1.2rem; text-align: center; height: 100%;
            box-shadow: 0 8px 24px rgba(19,36,65,.05);
        }}
        .card .value {{font-size: clamp(1.5rem, 2.4vw, 2.2rem); font-weight: 700;
                       white-space: nowrap; overflow: hidden; text-overflow: ellipsis;}}
        .card .label {{color: {MUTED}; font-size: .9rem;}}
        .note {{color: {MUTED}; font-size: .85rem;}}
        .chip {{display: inline-block; padding: .15rem .7rem; border-radius: 999px;
                font-size: .85rem; font-weight: 600; margin: 0 .15rem;}}
        .leaflet-control-attribution {{display: none !important;}}
        {direction}
        </style>
        """,
        unsafe_allow_html=True,
    )


def brand_logo_uri():
    """The 3-Eye vertical logo as a data URI (works on Streamlit Cloud too)."""
    import base64
    p = APP_DIR / "assets" / "brand" / "logo_vertical.png"
    return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()


def chip(text, color):
    return (f'<span class="chip" style="background:{color}22;color:{color};'
            f'border:1px solid {color}55">{text}</span>')


def metric_card(label, value, color=ACCENT):
    st.markdown(
        f'<div class="card"><div class="value" style="color:{color}">{value}</div>'
        f'<div class="label">{label}</div></div>',
        unsafe_allow_html=True,
    )


# ---------- Model ----------
# Which weights are the team's own. Rimas's Kaggle outputs: put the files in models/ with
# these names. The app always prefers the team's model; the published checkpoint is only a
# reference for comparison.
MODEL_INFO = {
    "run17_best_finetuned.pt": {"label": "Run 17 · our fine-tuned YOLOv8s (team model)", "ours": True, "rank": 1},
    "run17_yolov8s_rdd_finetuned.pt": {"label": "Run 17 · our fine-tuned YOLOv8s", "ours": True, "rank": 1},
    "run16_yolov8s_rdd_best.pt": {"label": "Run 16 · our fine-tuned YOLOv8s (first recipe)", "ours": True, "rank": 2},
    "run14_yolo11s_best.pt": {"label": "Run 14 · our YOLO11s trained from COCO", "ours": True, "rank": 3},
    "best.pt": {"label": "Our model (best.pt)", "ours": True, "rank": 4},
    "yolov8s_seed0_best.pt": {"label": "Reference · published RDD2022 YOLOv8s (not trained by us)",
                              "ours": False, "rank": 9},
}
# Confidence threshold per model, frozen on VALIDATION (China_MotorBike), never on the test set.
# Run 17: 0.46 = highest mean box F1 over the four classes with pothole recall >= 90%
# (Rimas, experiment 19, THRESHOLD_SELECTION.md / model_config.json). None = provisional 0.25.
MODEL_CONF = {"run17_best_finetuned.pt": 0.46, "run17_yolov8s_rdd_finetuned.pt": 0.46,
              "run16_yolov8s_rdd_best.pt": None, "run14_yolo11s_best.pt": None, "best.pt": None,
              "yolov8s_seed0_best.pt": None}
CONF_REASON = {"run17_best_finetuned.pt": "Frozen on validation (China): best mean box F1 with "
                                         "pothole recall ≥ 90%."}
DEFAULT_CONF = 0.25


def model_info(name):
    return MODEL_INFO.get(name, {"label": name, "ours": None, "rank": 5})


def available_models():
    names = [p.name for p in MODELS_DIR.glob("*.pt")]
    return sorted(names, key=lambda n: (model_info(n)["rank"], n))


def model_picker():
    """Sidebar: choose the weights (team model first). Returns the loaded model or None.
    The chosen file name is kept in st.session_state["model_name"]."""
    names = available_models()
    if not names:
        st.error("No model found. Put the team's weights in the `models/` folder "
                 "(for example `models/run17_yolov8s_rdd_finetuned.pt`) and refresh the page.")
        return None
    try:
        import ultralytics  # noqa: F401
    except ImportError:
        st.error("The YOLO library is not installed. Run `pip install --no-cache-dir ultralytics` "
                 "in the terminal, then restart the app.")
        return None
    choice = st.sidebar.selectbox("Model", names, index=0,
                                  format_func=lambda n: model_info(n)["label"])
    st.session_state["model_name"] = choice
    info = model_info(choice)
    if info["ours"] is False:
        st.sidebar.warning("Reference model, not trained by our team. Put our run-17 weights in "
                           "`models/` to use the team model.")
    elif info["ours"]:
        st.sidebar.success("Team model")
    return load_model(str(MODELS_DIR / choice))


def conf_slider():
    """Sidebar threshold control. Returns one threshold or a {class: threshold} dict.
    Default = the thresholds chosen on validation for the selected model."""
    name = st.session_state.get("model_name", "")
    chosen = MODEL_CONF.get(name)
    if isinstance(chosen, dict):
        use = st.sidebar.toggle("Validation thresholds per class", value=True)
        if use:
            st.sidebar.caption("Chosen on validation (China) to maximise F1: " + ", ".join(
                f"{k} {v:.2f}" for k, v in chosen.items()))
            return chosen
        return st.sidebar.slider("Confidence threshold", 0.05, 0.95, 0.30, 0.05)
    value = chosen if chosen is not None else DEFAULT_CONF
    conf = st.sidebar.slider("Confidence threshold", 0.05, 0.95, float(value), 0.05)
    if chosen is None:
        st.sidebar.caption("0.25 is provisional: no validation threshold for this model.")
    else:
        st.sidebar.caption(f"Default {chosen:.2f}. " + CONF_REASON.get(
            name, "Chosen on the validation set."))
    return conf


@st.cache_resource
def load_model(path):
    """Load the YOLO model once and keep it in memory."""
    from ultralytics import YOLO
    return YOLO(path)


def to_code(name):
    return CLASS_ALIASES.get(name, name)


def detect(model, image: Image.Image, conf):
    """Run YOLO on one PIL image. conf = one threshold, or {class code: threshold}.
    Returns (annotated image, DataFrame of boxes, list of detections in priority.py format)."""
    low = min(conf.values()) if isinstance(conf, dict) else conf
    result = model.predict(image, conf=low, imgsz=640, iou=0.7, max_det=300, verbose=False)[0]
    # Label boxes with the Brief's codes (D00, D10, D20, D40), whatever names the checkpoint uses
    result.names = {k: to_code(v) for k, v in result.names.items()}
    if isinstance(conf, dict) and len(result.boxes):
        keep = [float(b.conf) >= conf.get(result.names[int(b.cls)], low) for b in result.boxes]
        result.boxes = result.boxes[keep]
    annotated = Image.fromarray(result.plot()[:, :, ::-1])  # BGR -> RGB

    W, H = image.width, image.height
    dets, rows = [], []
    for box in result.boxes:
        code = to_code(result.names[int(box.cls)])
        if code not in CLASS_WEIGHT:
            continue
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        d = {"cls": code, "x": x1, "y": y1, "w": x2 - x1, "h": y2 - y1,
             "conf": float(box.conf)}
        dets.append(d)
        rows.append({
            "Class": code,
            "Type": CLASS_INFO[code]["name"],
            "Confidence": round(d["conf"], 2),
            "Area %": round(d["w"] * d["h"] / (W * H) * 100, 1),
            "Box priority": round(priority_score([d], W, H), 1),
        })
    return annotated, pd.DataFrame(rows), dets


def band(score):
    """Return (label, action, color) for a priority score."""
    for limit, label, action, color in BANDS:
        if score >= limit:
            return label, action, color
    return BANDS[-1][1:]


# ---------- GPS ----------
def get_gps(image: Image.Image):
    """Return (lat, lon) from photo EXIF, or None if the photo has no GPS."""
    exif = image.getexif()
    if not exif:
        return None
    gps = exif.get_ifd(ExifTags.IFD.GPSInfo)
    if not gps or 2 not in gps or 4 not in gps:
        return None

    def to_degrees(values, ref):
        d, m, s = (float(v) for v in values)
        deg = d + m / 60 + s / 3600
        return -deg if ref in ("S", "W") else deg

    return to_degrees(gps[2], gps.get(1, "N")), to_degrees(gps[4], gps.get(3, "E"))


def distance_m(a, b):
    """Distance in metres between two (lat, lon) points."""
    lat1, lon1, lat2, lon2 = map(math.radians, (*a, *b))
    h = (math.sin((lat2 - lat1) / 2) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2)
    return 6_371_000 * 2 * math.asin(math.sqrt(h))


def find_duplicates(points, radius_m=15):
    """Simple duplicate finder: two reports are 'possible duplicates' when they are
    within radius_m metres and share at least one damage class."""
    pairs = []
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            a, b = points[i], points[j]
            shared = set(a["class_list"]) & set(b["class_list"])
            dist = distance_m((a["lat"], a["lon"]), (b["lat"], b["lon"]))
            if shared and dist <= radius_m:
                pairs.append({"Report A": a["file"], "Report B": b["file"],
                              "Distance (m)": round(dist, 1),
                              "Shared classes": ", ".join(sorted(shared)), "i": i, "j": j})
    return pairs


def find_similar_duplicates(points, radius_m=30, threshold=None):
    """Damage Map version of the team's duplicate finder (duplicates.py):
    two reports are likely duplicates when they are within radius_m metres, share a damage
    class, and at least one same-class crop pair has DINOv2 cosine similarity >= threshold.
    Each point needs: file, lat, lon, crops = list of (class, unit vector)."""
    import numpy as np
    from duplicates import THRESHOLD
    threshold = THRESHOLD if threshold is None else threshold
    pairs = []
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            a, b = points[i], points[j]
            dist = distance_m((a["lat"], a["lon"]), (b["lat"], b["lon"]))
            if dist > radius_m:
                continue
            best, best_cls = -1.0, None
            for ca, va in a["crops"]:
                for cb, vb in b["crops"]:
                    if ca == cb:
                        s = float(np.dot(va, vb))
                        if s > best:
                            best, best_cls = s, ca
            if best_cls is not None and best >= threshold:
                pairs.append({"Report A": a["file"], "Report B": b["file"],
                              "Distance (m)": round(dist, 1), "Class": best_cls,
                              "Similarity": round(best, 2), "i": i, "j": j})
    return sorted(pairs, key=lambda p: -p["Similarity"])


PHOTO_TYPES = ["jpg", "jpeg", "png", "dng", "heic", "heif"]


def open_photo(file):
    """Open an uploaded photo. iPhone .DNG exports that are really JPEG/MPO open fine;
    true RAW files do not, so we show a clear message instead of a crash."""
    try:
        file.seek(0)
        img = Image.open(file)
        img.load()
        # Phones store photos sideways plus an "orientation" tag; turn them upright so the
        # model, the boxes and the saved thumbnails see the road the right way up.
        return ImageOps.exif_transpose(img)
    except Exception:
        st.error(f"Can't open **{file.name}**. Please upload a JPG or PNG photo "
                 "(export RAW/HEIC photos as JPG first, keeping the location).")
        return None


# ---------- Image helpers ----------
def before_after(original: Image.Image, detected: Image.Image, reveal: int):
    """Left part shows the detected image, right part the original, split at reveal %."""
    split = int(original.width * reveal / 100)
    out = original.copy()
    if split > 0:
        out.paste(detected.resize(original.size).crop((0, 0, split, original.height)), (0, 0))
    line = Image.new("RGB", (4, original.height), (0, 194, 168))
    out.paste(line, (max(0, min(split - 2, original.width - 4)), 0))
    return out


def gauge(score, color):
    """Plotly gauge for the 0-100 priority."""
    import plotly.graph_objects as go
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score, number={"suffix": " / 100"},
        gauge={"axis": {"range": [0, 100]}, "bar": {"color": color},
               "steps": [{"range": [0, 40], "color": "#E3F6EB"},
                         {"range": [40, 70], "color": "#FFF2D8"},
                         {"range": [70, 100], "color": "#FFEBE9"}]},
        title={"text": "Repair priority"}))
    fig.update_layout(height=260, margin=dict(t=50, b=10, l=30, r=30),
                      paper_bgcolor="rgba(0,0,0,0)", font_color=INK)
    return fig


def team_model():
    """Load the team model quietly (no sidebar widgets) for the citizen/municipality pages.
    Uses the model chosen on a technical page if any, else the first (team) model."""
    names = available_models()
    if not names:
        st.error("No model found in models/.")
        return None, None
    name = st.session_state.get("model_name") or names[0]
    if name not in names:
        name = names[0]
    st.session_state.setdefault("model_name", name)
    conf = MODEL_CONF.get(name) or DEFAULT_CONF
    return load_model(str(MODELS_DIR / name)), conf
