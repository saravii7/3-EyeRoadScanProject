"""Results from the team's report and repo: baseline, YOLO runs 14-17 and the model the app uses."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils import ACCENT, apply_style, metric_card

st.title("📊 Model Results")
st.caption("Validation = China_MotorBike (1,977 images), a country the models never trained on. "
           "Final test on United States + local photos is still pending (experiment E4).")

LAYOUT = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
              font_color="#17233B", legend=dict(orientation="h", y=-0.2))

# ---- Detector runs 14-17 ----
st.subheader("Detector runs (validation: China_MotorBike)")
runs = pd.DataFrame({
    "Run": ["14", "15", "16", "17"],
    "Model and training": [
        "YOLO11s from COCO, trained by us on 8,999 images",
        "Published YOLOv8s RDD2022 checkpoint, no training by us",
        "Run-15 checkpoint fine-tuned by us (lr 0.01 recipe of run 14)",
        "Run-15 checkpoint gently fine-tuned by us (lr 0.0001, 7 epochs)"],
    "mAP50": [0.227, 0.962, 0.794, 0.959],
    "mAP50-95": [0.087, 0.671, 0.447, 0.658],
    "CPU s / photo": [0.16, 0.19, 0.22, 0.19],
})
st.dataframe(runs, width="stretch", hide_index=True)
st.info("**Team model in this app: run 17** (our gentle fine-tuning of the published RDD2022 "
        "YOLOv8s). On validation it is within 1.3 points of the published checkpoint (mAP50-95 "
        "0.658 vs 0.671), so fine-tuning did not add accuracy on China. Both may have seen these "
        "China images in the published pre-training, so the fair comparison is on United States "
        "and our local photos (experiment E4).")

st.subheader("Run 17 per class (validation)")
pc = pd.DataFrame({
    "Class": ["D00 longitudinal", "D10 transverse", "D20 alligator", "D40 pothole"],
    "AP50": [0.940, 0.929, 0.981, 0.986],
    "AP50-95": [0.662, 0.604, 0.734, 0.632],
    "Image precision @0.5": [0.997, 0.988, 0.958, 0.988],
    "Image recall @0.5": [0.935, 0.879, 0.975, 0.988],
    '"Always present" F1': [0.836, 0.544, 0.395, 0.153],
})
st.dataframe(pc, hide_index=True, width="stretch")
st.markdown('<p class="note">D10 (transverse cracks) is the weakest class: lowest AP50-95 and '
            "image recall. Image metrics only check whether a class is present; detection AP also "
            "checks where the box is.</p>", unsafe_allow_html=True)

from pathlib import Path  # noqa: E402

ASSETS = Path(__file__).resolve().parent.parent / "assets"
st.subheader("Operating threshold: 0.46 (chosen on validation)")
st.markdown("Rule fixed before looking: highest mean box F1 over the four classes, with pothole "
            "recall at least 90% (a missed pothole costs more than a false alarm).")
thr = pd.DataFrame({
    "Class": ["D00", "D10", "D20", "D40"],
    "Precision": [0.891, 0.861, 0.929, 0.942], "Recall": [0.827, 0.793, 0.961, 0.966],
    "F1": [0.858, 0.826, 0.945, 0.954],
})
t1, t2 = st.columns([2, 3])
t1.dataframe(thr, hide_index=True, width="stretch")
t1.markdown('<p class="note">At 0.46 vs 0.25: box macro-F1 89.6% vs 86.3%, false positives '
            "471 vs 1,413, pothole recall 96.6% vs 97.0%. Tuned on validation, so optimistic.</p>",
            unsafe_allow_html=True)
if (ASSETS / "threshold_selection.png").exists():
    t2.image(str(ASSETS / "threshold_selection.png"), caption="Threshold sweep (validation)",
             width="stretch")

pics = [("confusion_matrix", "Run 17 confusion matrix (validation)"),
        ("F1_curve", "Run 17 box F1 vs confidence (validation)"),
        ("results", "Run 17 training curves")]
found = [(ASSETS / f"{n}.png", c) for n, c in pics if (ASSETS / f"{n}.png").exists()]
if found:
    cols = st.columns(len(found))
    for col, (path, cap) in zip(cols, found):
        col.image(str(path), caption=cap, width="stretch")

st.subheader("Required experiments")
st.dataframe(pd.DataFrame({
    "ID": ["E1", "E2", "E3", "E4", "E5"],
    "Question": ["Baseline classifier vs detector", "Model size / resolution vs CPU speed",
                 "Which augmentations help", "Cross-country and local generalisation",
                 "Duplicate embeddings: pHash vs ResNet vs DINOv2"],
    "Status": ["Baseline v1/v2 and detector runs done; controlled comparison to finish",
               "Pending", "Pending", "Pending: United States + local photos, run once",
               "Duplicate finder built (DINOv2); comparison on team pairs pending"],
}), hide_index=True, width="stretch")

# ---- Detector (run 14) ----
st.subheader("Our first detector: YOLO11s from COCO (run 14)")
c1, c2, c3, c4 = st.columns(4)
with c1:
    metric_card("mAP50", "0.227")
with c2:
    metric_card("Precision / Recall", "0.30 / 0.30")
with c3:
    metric_card("CPU time per photo", "0.16 s")
with c4:
    metric_card("Training images", "8,999")
st.markdown('<p class="note">COCO-pretrained YOLO11s, 640 px, best epoch 49 of 64, '
            "trained on Japan, India and Czech.</p>", unsafe_allow_html=True)

# ---- Baseline per class ----
st.subheader("Baseline: ResNet-18 image classifier")
base = pd.DataFrame({
    "Class": ["D00", "D10", "D20", "D40"],
    "v1 F1 (600 imgs)": [0.84, 0.55, 0.39, 0.15],
    "v2 F1 (8,999 imgs)": [0.84, 0.57, 0.43, 0.15],
    '"Always present" F1': [0.84, 0.54, 0.39, 0.15],
})
fig = go.Figure()
fig.add_bar(name='"Always present" reference', x=base["Class"],
            y=base['"Always present" F1'], marker_color="#4A5163")
fig.add_bar(name="Baseline v1", x=base["Class"], y=base["v1 F1 (600 imgs)"],
            marker_color="#6C7A96")
fig.add_bar(name="Baseline v2", x=base["Class"], y=base["v2 F1 (8,999 imgs)"],
            marker_color=ACCENT)
fig.update_layout(barmode="group", title="Validation F1 per class", yaxis_range=[0, 1],
                  **LAYOUT)
st.plotly_chart(fig, width="stretch")
st.markdown(
    "- v1 is no better than answering *present* for every image.\n"
    "- v2 ranks images a bit better (test AUC for D40 rose from 0.47 to 0.61), "
    "but an image classifier can't say **where** the damage is.")

# ---- Image-level comparison ----
st.subheader("Image-level macro-F1 (validation)")
comp = pd.DataFrame({
    "Model": ["Baseline v1", "Baseline v2", "YOLO11s @ 0.5", "YOLO11s tuned*"],
    "Macro-F1": [0.482, 0.496, 0.244, 0.723],
})
fig2 = go.Figure(go.Bar(x=comp["Macro-F1"], y=comp["Model"], orientation="h",
                        marker_color=["#6C7A96", "#6C7A96", "#4A5163", ACCENT],
                        text=comp["Macro-F1"], textposition="outside"))
fig2.update_layout(xaxis_range=[0, 1], height=300, **LAYOUT)
st.plotly_chart(fig2, width="stretch")
st.markdown('<p class="note">* Threshold tuned on the same validation set, so this is an '
            "optimistic development number, not a final result.</p>", unsafe_allow_html=True)

# ---- Data split ----
st.subheader("Data split by country")
split = pd.DataFrame({
    "Country": ["Japan", "India", "Czech", "China_MotorBike", "United_States", "China_Drone"],
    "Images": [10506, 7706, 2829, 1977, 4805, 2401],
    "Role": ["train", "train", "train", "validation", "test", "robustness check"],
})
st.dataframe(split, width="stretch", hide_index=True)
st.markdown('<p class="note">We split by country, not by random image, so the score shows '
            "whether the model works in a country it never saw.</p>", unsafe_allow_html=True)

with st.expander("About the published checkpoint (run 15)"):
    st.markdown(
        "A published RDD2022 checkpoint ([SreekarAditya/yolo-rdd2022-benchmark]"
        "(https://huggingface.co/SreekarAditya/yolo-rdd2022-benchmark), CC BY 4.0) scored "
        "mAP50 0.962 on the same China images. **We did not train it**, and its training data "
        "may include these images, so its score is a diagnostic reference, not our result. "
        "Our own contribution is the comparison and fine-tuning in runs 16 and 17.")

# Optional: training plots. Copy them from the Kaggle run 14 output into an assets/ folder:
# st.image("assets/results.png", caption="YOLO11s training curves")
# st.image("assets/confusion_matrix.png", caption="YOLO11s confusion matrix")
