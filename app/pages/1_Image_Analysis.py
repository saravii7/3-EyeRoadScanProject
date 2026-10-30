"""Upload a photo and follow the full RoadScan pipeline:
detect damage -> repair priority -> location (Saudi Arabia only) -> duplicate check against the
open-report queue (DINOv2 + FAISS + GPS radius) -> add to the queue. Faces and plates are blurred
in everything shown or saved. Every step is timed on CPU."""
import io
import time

import plotly.express as px
import streamlit as st

from pipeline import open_matches, save_new
from location import location_section, place_details, format_place
from priority import priority_score
from privacy import blur_available, blur_boxes, count_by_kind, find_sensitive
from reports import (as_data_uri, crop_path, link_duplicate, queue_position,
                     save_report_details, thumb_path)
from utils import (CLASS_INFO, PHOTO_TYPES, apply_style, band, conf_slider, detect, gauge,
                   metric_card, model_picker, open_photo)

st.title("🔍 Image Analysis")

model = model_picker()
if model is None:
    st.stop()
conf = conf_slider()
blur_on = st.sidebar.toggle("Blur faces and plates", value=True)

uploaded = st.file_uploader("Upload a road photo", type=PHOTO_TYPES)
if not uploaded:
    st.info("Upload a photo to start.")
    st.stop()

timing = {}
t_all = time.perf_counter()

photo = open_photo(uploaded)
if photo is None:
    st.stop()
image = photo.convert("RGB")

# 1) detection on the ORIGINAL photo
t0 = time.perf_counter()
with st.spinner("Scanning the road..."):
    annotated, df, dets = detect(model, image, conf)
timing["Damage detection (YOLO)"] = time.perf_counter() - t0

# 2) privacy: blur faces and plates in everything we show or store
t0 = time.perf_counter()
sensitive = find_sensitive(image) if blur_on else []
shown = blur_boxes(image, sensitive) if sensitive else image
shown_annotated = blur_boxes(annotated, sensitive) if sensitive else annotated
timing["Face and plate blurring"] = time.perf_counter() - t0

# 3) priority
t0 = time.perf_counter()
score = round(priority_score(dets, image.width, image.height), 1)
label, action, color = band(score)
timing["Priority score"] = time.perf_counter() - t0

# --- Top row: gauge + cards ---
g, c1, c2, c3 = st.columns([2, 1.3, 1, 1])
with g:
    st.plotly_chart(gauge(score, color), width="stretch")
with c1:
    metric_card("Decision", label, color)
with c2:
    metric_card("Damages found", len(df))
with c3:
    potholes = int((df["Class"] == "D40").sum()) if not df.empty else 0
    metric_card("Potholes", potholes, CLASS_INFO["D40"]["color"])
st.markdown(f"### Recommended action: **{action}**")
if blur_on and not blur_available():
    st.warning("Face and plate blurring is not available on this computer (OpenCV 5 has no "
               "Haar cascades). Run: pip install \"opencv-python<5\" and restart the app.")
elif blur_on:
    n = count_by_kind(sensitive)
    st.caption(f"Privacy: blurred {n['faces']} face(s) and {n['plates']} plate(s) before display.")

# 4) location
t0 = time.perf_counter()
location = location_section(uploaded)
timing["Location and address"] = time.perf_counter() - t0


# 5) duplicate check against the open-report queue
def _crops(img, boxes, margin=0.10):
    out = []
    for d in boxes:
        mx, my = d["w"] * margin, d["h"] * margin
        out.append((d["cls"], img.crop((max(0, d["x"] - mx), max(0, d["y"] - my),
                                         min(img.width, d["x"] + d["w"] + mx),
                                         min(img.height, d["y"] + d["h"] + my)))))
    return out


def _queue_add():
    st.session_state["pending_action"] = ("add", None)


def _queue_link(rid):
    st.session_state["pending_action"] = ("link", rid)


st.subheader("🔁 Duplicate check")
saved = st.session_state.setdefault("saved_reports", {})
photo_key = f"{uploaded.name}-{uploaded.size}"
lat, lon = location if location else (None, None)

# A button press is stored by its callback first, then handled here, so it is never lost
# when the page reruns (maps and location widgets can trigger extra reruns).
pending = st.session_state.get("pending_action")
if pending and dets and photo_key not in saved:
    kind, rid = pending
    if kind == "add":
        A = {"image": image, "dets": dets, "score": score, "label": label, "shown": shown,
             "annotated": shown_annotated, "t_all": t_all}
        new_id = save_new(uploaded, A, location, source="technical")
        saved[photo_key] = ("added", new_id)
        st.session_state["last_added"] = new_id
    else:
        link_duplicate(rid)
        saved[photo_key] = ("linked", rid)
st.session_state.pop("pending_action", None)

if not dets:
    st.caption("No damage found, so there is nothing to compare.")
elif photo_key in saved:
    kind, rid = saved[photo_key]
    pos, total = queue_position(rid)
    if kind == "added":
        st.success(f"Saved as open report #{rid}. Queue position: {pos} of {total} "
                   "(sorted by priority).")
    else:
        st.success(f"Linked to open report #{rid} as a repeat report (no new report created). "
                   f"Its queue position: {pos} of {total}.")
    st.page_link("views/m_queue.py", label="Open the report queue", icon="📋")
else:
    t0 = time.perf_counter()
    with st.spinner("Comparing with open reports..."):
        matches, _ = open_matches(image, dets, lat, lon)
    timing["Duplicate search (DINOv2 + FAISS)"] = time.perf_counter() - t0
    if matches:
        m = matches[0]  # best first
        where = f"{m['distance_m']:.0f} m away" if m["distance_m"] is not None else "no GPS"
        st.warning(f"Likely duplicate of open report #{m['id']} · similarity "
                   f"{m['similarity']:.2f} · {where} · class {m['cls']}")
        # evidence: the new damage next to the stored one
        new_crop = next((c for cls, c in _crops(shown, dets) if cls == m["cls"]), None)
        old_crop, old_full = crop_path(m["id"], m["cls"]), thumb_path(m["id"])
        e1, e2, e3 = st.columns(3)
        if new_crop is not None:
            e1.image(new_crop, caption=f"New photo · {m['cls']}", width="stretch")
        if old_crop:
            e2.image(str(old_crop), caption=f"Report #{m['id']} · {m['cls']}", width="stretch")
        if old_full:
            e3.image(str(old_full), caption=f"Report #{m['id']} (full photo)", width="stretch")
        if len(matches) > 1:
            st.caption("Other candidates: " + ", ".join(
                f"#{x['id']} ({x['similarity']:.2f})" for x in matches[1:4]))
        b1, b2 = st.columns(2)
        b1.button(f"Same damage: link to report #{m['id']}", on_click=_queue_link,
                  args=(m["id"],), type="primary", width="stretch")
        b2.button("Different damage: add as a new report", on_click=_queue_add, width="stretch")
    else:
        st.success("New report: no similar open report nearby.")
        st.button("Add to open reports", on_click=_queue_add, type="primary")
    st.caption("Duplicate rule: same class, within 30 m and similarity ≥ 0.80 (tuned in E5 on our "
               "photo pairs); without GPS 0.90 (provisional).")

# --- Original vs detected ---
st.subheader("🖼️ Original vs detected")
a, b = st.columns(2)
a.image(shown, caption="Original", width="stretch")
b.image(shown_annotated, caption="Detected", width="stretch")

timing["Total (end to end)"] = time.perf_counter() - t_all
with st.expander(f"⏱️ Processing time on CPU: {timing['Total (end to end)']:.2f} s"):
    st.dataframe({"Step": list(timing), "Seconds": [round(v, 3) for v in timing.values()]},
                 width="stretch", hide_index=True)
    st.caption("The first photo is slower (models load once). Address lookup needs internet.")

if df.empty:
    st.success("No damage detected at this confidence level.")
    st.stop()

# --- Table + chart ---
left, right = st.columns([3, 2])
with left:
    st.subheader("Detections")
    st.dataframe(df, width="stretch", hide_index=True)
with right:
    counts = df["Class"].value_counts().reset_index()
    counts.columns = ["Class", "Count"]
    fig = px.bar(counts, x="Class", y="Count", color="Class",
                 color_discrete_map={k: v["color"] for k, v in CLASS_INFO.items()},
                 title="Damage by class")
    fig.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, width="stretch")

with st.expander("How is the priority calculated?"):
    st.markdown(
        "`priority = 100 × (0.45·type + 0.20·size + 0.20·count + 0.15·confidence)`  \n"
        "- **type**: worst class found (D40 = 1.0, D20 = 0.8, D10 = 0.5, D00 = 0.4)\n"
        "- **size**: total box area ÷ image area ÷ 0.25, capped at 1\n"
        "- **count**: number of boxes ÷ 5, capped at 1\n"
        "- **confidence**: mean detector confidence\n\n"
        "Open the **Priority Score** page to try other weights.")

# --- Downloads (blurred) ---
buf = io.BytesIO()
shown_annotated.save(buf, format="PNG")
report = df.assign(Image=uploaded.name, **{"Image priority": score, "Decision": label})
d1, d2 = st.columns(2)
d1.download_button("⬇️ Download detected image", buf.getvalue(), "roadscan_result.png",
                   "image/png", width="stretch")
d2.download_button("⬇️ Download report (CSV)", report.to_csv(index=False),
                   "roadscan_report.csv", "text/csv", width="stretch")
