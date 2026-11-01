"""Team, data attribution, and limitations."""
import streamlit as st

from utils import apply_style

st.title("👥 About RoadScan 3-Eye")
st.write("AIEP bootcamp capstone, Olo Academy, Track A: RoadScan.")

st.subheader("Team")
c1, c2, c3 = st.columns(3)
for col, name in zip((c1, c2, c3), ("Sarah Albahesh", "Rimas Al-Abunasser", "Fajer Alshahrani")):
    col.markdown(f'<div class="card"><div class="value" style="font-size:1.3rem">{name}</div>'
                 "</div>", unsafe_allow_html=True)

st.subheader("Data")
st.markdown(
    "**RDD2022**, the multi-national Road Damage Dataset (Deeksha Arya et al.), "
    "[figshare](https://figshare.com/articles/dataset/RDD2022_The_multi-national_Road_Damage_"
    "Dataset_released_through_CRDDC_2022/21431547), licence CC BY 4.0. "
    "We use four classes: D00, D10, D20, D40.")

st.subheader("Limitations")
st.markdown(
    "- The detector was trained on Japan, India and Czech roads; scores drop in new countries "
    "(domain shift).\n"
    "- Potholes (D40) and transverse cracks (D10) are rare in the data.\n"
    "- The priority weights are a first draft and need checking with maintenance staff.\n"
    "- The team model (run 17) starts from a published RDD2022 checkpoint whose training data may "
    "overlap our validation images, so we judge it on US and local photos.\n"
    "- Face and plate blurring uses classic OpenCV detectors and can miss side faces or "
    "angled plates; a production system needs a stronger detector and a manual check.\n"
    "- Citizens in some neighbourhoods report less often, so a queue driven only by reports can "
    "under-serve them; municipalities should add planned patrols.\n"
    "- When a photo has no GPS, the location comes from the device or a map click; RDD2022 "
    "photos have no GPS, so any GPS used with them is simulated.\n"
    "- The duplicate threshold (0.80 within 30 m) was tuned on a small set of our own photo "
    "pairs (E5); without GPS the stricter 0.92 catches fewer repeats (4 of 9) but made no false links.\n"
    "- In the United States the model misses most potholes at the frozen threshold (31.9% "
    "recall), so reports are reviewed by a person before any decision.\n"
    "- Saved open reports live in the `data/reports` folder; on a cloud host they can be reset "
    "when the app restarts.\n"
    "- The app supports decisions; a person still inspects the road before repair.")

st.subheader("Privacy")
st.markdown(
    "- Faces and licence plates are blurred before anything is shown, downloaded or saved.\n"
    "- The original photo is never stored; the queue keeps only a small blurred thumbnail.\n"
    "- Only when you press **Add to open reports**, the app saves the damage fingerprints "
    "(DINOv2 vectors), damage class, GPS, priority and file name in `data/reports`.\n"
    "- To show a readable address, the coordinates are sent to OpenStreetMap (Nominatim).\n"
    "- Reports are accepted only inside Saudi Arabia.\n"
    "- Street photos can show faces and car plates; blur them before sharing results.\n"
    "- GPS is read only to place the report on the map.")

st.subheader("Credits")
st.markdown(
    "- Detector checkpoint: [SreekarAditya/yolo-rdd2022-benchmark]"
    "(https://huggingface.co/SreekarAditya/yolo-rdd2022-benchmark), CC BY 4.0; "
    "[Ultralytics YOLO](https://github.com/ultralytics/ultralytics), AGPL-3.0.\n"
    "- Duplicate finder: [DINOv2-small](https://huggingface.co/facebook/dinov2-small) (Meta, "
    "Apache 2.0) and FAISS.\n"
    "- Maps and addresses: © [OpenStreetMap](https://www.openstreetmap.org/copyright) "
    "contributors; satellite imagery © Esri.\n"
    "- Saudi border: [Natural Earth](https://www.naturalearthdata.com/), public domain.\n"
    "- Face and plate detectors: OpenCV Haar cascades (BSD licence).")
