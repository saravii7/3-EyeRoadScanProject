"""Upload GPS-tagged photos: each one becomes a point on the map, ranked by repair priority,
with likely duplicate reports linked (team duplicate finder: DINOv2 + GPS radius)."""
import folium
import pandas as pd
import streamlit as st
from PIL import Image
from streamlit_folium import st_folium

from priority import priority_score
from duplicates import embed_crops
from utils import (apply_style, conf_slider, band, detect, find_similar_duplicates, get_gps, metric_card,
                   model_picker)

st.title("🗺️ Damage Map")
st.caption("Upload your own street photos taken with location ON. Each photo becomes a point "
           "on the map, colored by repair priority.")

model = model_picker()
if model is None:
    st.stop()
conf = conf_slider()
radius = st.sidebar.slider("Duplicate radius (metres)", 5, 50, 30, 5)

files = st.file_uploader("Upload photos", type=["jpg", "jpeg", "dng"], accept_multiple_files=True)
if not files:
    st.info("Upload one or more photos to build the map.")
    st.stop()


@st.cache_data(show_spinner=False)
def scan(file_bytes, name, conf, _model):
    import io
    try:
        image = Image.open(io.BytesIO(file_bytes))
        image.load()
    except Exception:
        return None
    gps = get_gps(image)  # read GPS before convert(), which drops EXIF
    if gps is None:
        return None
    from PIL import ImageOps
    image = ImageOps.exif_transpose(image)  # phone photos are stored sideways
    image.thumbnail((1600, 1600))  # keep memory low on the free cloud host
    rgb = image.convert("RGB")
    _, df, dets = detect(_model, rgb, conf)
    score = round(priority_score(dets, rgb.width, rgb.height), 1)
    classes = sorted(df["Class"].unique()) if len(df) else []
    crops = list(zip([d["cls"] for d in dets], embed_crops(rgb, dets)))  # DINOv2 fingerprints
    return {"file": name, "lat": gps[0], "lon": gps[1], "priority": score,
            "damages": len(df), "class_list": classes, "crops": crops}


points, no_gps = [], []
progress = st.progress(0.0, text="Scanning photos...")
for i, f in enumerate(files):
    p = scan(f.getvalue(), f.name, conf, model)
    if p is None:
        no_gps.append(f.name)
    else:
        p["decision"], p["action"], p["color"] = band(p["priority"])
        points.append(p)
    progress.progress((i + 1) / len(files), text=f"Scanned {f.name}")
progress.empty()

if no_gps:
    st.warning(f"No GPS found (or file can't be opened): {', '.join(no_gps)}. "
               "Turn on location in the phone camera, "
               "and don't send photos through WhatsApp (it removes GPS).")
if not points:
    st.stop()

with st.spinner("Comparing damage crops between nearby reports..."):
    dups = find_similar_duplicates(points, radius)

c1, c2, c3, c4 = st.columns(4)
with c1:
    metric_card("Reports on map", len(points))
with c2:
    metric_card("Total damages", sum(p["damages"] for p in points))
with c3:
    urgent = sum(p["decision"] == "Urgent" for p in points)
    metric_card("Urgent", urgent, "#D95B55")
with c4:
    metric_card("Possible duplicates", len(dups), "#F3B548")

m = folium.Map(location=[sum(p["lat"] for p in points) / len(points),
                         sum(p["lon"] for p in points) / len(points)], zoom_start=17,
               attributionControl=False)
folium.TileLayer("Esri.WorldImagery", name="Satellite").add_to(m)
for p in points:
    folium.CircleMarker(
        location=[p["lat"], p["lon"]], radius=8 + p["priority"] / 8,
        color=p["color"], fill=True, fill_opacity=0.85,
        tooltip=f"{p['file']}: {p['priority']}",
        popup=folium.Popup(
            f"<b>{p['file']}</b><br>Priority: {p['priority']}/100 ({p['decision']})<br>"
            f"Damages: {p['damages']} ({', '.join(p['class_list']) or '-'})<br>"
            f"Action: {p['action']}", max_width=260),
    ).add_to(m)
for d in dups:
    a, b = points[d["i"]], points[d["j"]]
    folium.PolyLine([[a["lat"], a["lon"]], [b["lat"], b["lon"]]], color="#F3B548",
                    weight=3, dash_array="6", tooltip="Possible duplicate").add_to(m)
folium.LayerControl().add_to(m)
st_folium(m, use_container_width=True, height=540, returned_objects=[])
st.caption("Map data © OpenStreetMap contributors · Satellite imagery © Esri")

left, right = st.columns([3, 2])
with left:
    st.subheader("Work queue (most urgent first)")
    queue = pd.DataFrame(points).drop(columns=["crops"]).sort_values("priority", ascending=False)
    queue["classes"] = queue["class_list"].apply(", ".join)
    st.dataframe(queue[["file", "priority", "decision", "action", "damages", "classes",
                        "lat", "lon"]], width="stretch", hide_index=True)
    st.download_button("⬇️ Download work queue (CSV)", queue.drop(columns=["class_list",
                       "color"]).to_csv(index=False), "roadscan_work_queue.csv", "text/csv")
with right:
    st.subheader("Possible duplicates")
    if dups:
        st.dataframe(pd.DataFrame(dups).drop(columns=["i", "j"]), width="stretch",
                     hide_index=True)
    else:
        st.write("None found.")
    st.markdown('<p class="note">Likely duplicate = within the chosen radius, same damage class, '
                "and DINOv2 crop similarity above the team threshold (0.80, tuned in E5 on "
                "our photo pairs).</p>", unsafe_allow_html=True)
