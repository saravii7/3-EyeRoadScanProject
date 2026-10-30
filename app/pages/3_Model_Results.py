"""Results from the team's report and repo: baseline, YOLO runs 14-17 and the model the app uses."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils import ACCENT, apply_style, metric_card

st.title("📊 Model Results")
st.caption("Validation = China_MotorBike (1,977 images), a country the models never trained on. "
           "United States (4,804 images) was evaluated once with the frozen model and threshold "
           "(E4, run 21); local photos are the final independent test.")

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
    "Status": ["Baseline v1/v2 and detector runs done",
               "Pending",
               "Done (run 20): keep the current recipe; all-on was best",
               "Done for countries (run 21); local photos pending",
               "Done (notebook 05): threshold 0.80 within 30 m"],
}), hide_index=True, width="stretch")

# ---- E4: countries (run 21) ----
st.subheader("E4 · Same frozen model in other countries (run 21)")
st.dataframe(pd.DataFrame({
    "Country": ["China_MotorBike (development)", "United States (test, run once)", "Japan*",
                "India*"],
    "Images": [1977, 4804, 500, 500],
    "mAP50": ["95.9%", "76.4%", "82.3%", "62.0%"],
    "mAP50-95": ["65.8%", "49.7%", "50.5%", "40.3%"],
    "Micro-F1 @0.46": ["86.8%", "76.1%", "72.9%", "56.1%"],
    "Pothole recall": ["96.6%", "31.9%", "n/a", "n/a"],
}), hide_index=True, width="stretch")
st.warning("Honest finding: in the United States the model finds only 43 of 135 potholes "
           "(31.9%) at the frozen threshold, against 96.6% on China. China was used for "
           "development, so its numbers are optimistic. We did not re-tune on the US set. "
           "Most misses are small boxes (1,784 of 4,122 missed boxes cover under 1% of the image).")
st.caption("* Japan and India rows use the leftover images outside our training sample, which "
           "contain few labels (India 42 boxes), so they are diagnostics, not country scores. "
           "Czech leftovers have no labels at all.")

# ---- E3: augmentation (run 20) ----
st.subheader("E3 · Augmentation ablation (run 20)")
st.dataframe(pd.DataFrame({
    "Arm": ["All on (control)", "No mosaic", "No HSV colour", "No horizontal flip"],
    "mAP50": ["95.86%", "95.61%", "95.89%", "95.70%"],
    "mAP50-95": ["65.30%", "64.59%", "65.25%", "65.05%"],
    "Change (pp)": ["0.00", "-0.72", "-0.05", "-0.25"],
}), hide_index=True, width="stretch")
st.caption("Seven epochs, one seed: a development observation, not a final ranking. Decision: "
           "keep the current recipe. The app still uses the run-17 checkpoint at 0.46.")

# ---- E5: duplicates (notebook 05) ----
st.subheader("E5 · Duplicate finder on our own photo pairs (notebook 05)")
d1, d2, d3 = st.columns(3)
with d1:
    metric_card("Caught (GPS, 30 m)", "8 / 9")
with d2:
    metric_card("False links (GPS)", "0 / 24", "#43A878")
with d3:
    metric_card("Recall@1 (test)", "9 / 9")
st.dataframe(pd.DataFrame({
    "Method (no GPS)": ["DINOv2 (used)", "ResNet-18", "pHash"],
    "AUC tuning": [0.79, 0.81, 0.74], "AUC test": [0.79, 0.81, 0.66],
    "Recall@1 test": ["8/9", "7/9", "6/9"], "Recall@5 test": ["9/9", "9/9", "9/9"],
}), hide_index=True, width="stretch")
st.caption("Threshold 0.80 was chosen on tuning pairs (10 same / 36 different) and measured once "
           "on separate test pairs (9 same / 24 different). Without GPS the same threshold gives "
           "12/24 false links, so the location radius does most of the filtering. The sample is "
           "small, so these numbers are encouraging, not final. The no-GPS threshold (0.90) is "
           "still provisional.")

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
