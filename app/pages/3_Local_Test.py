"""Team-built local test set (photos from our own city): per-class results, confusion matrix and
an automatic error-analysis gallery. Run it ONCE with the frozen model and threshold; never tune
anything on these photos."""
import io
import time
from collections import Counter

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from PIL import Image

from evaluation import CLASSES, draw_boxes, match_image, read_yolo_labels, summarise
from privacy import blur_boxes, find_sensitive
from utils import ACCENT, apply_style, conf_slider, detect, metric_card, model_picker

st.title("🧪 Local Test Set and Error Analysis")
st.caption("Upload our labelled local photos (JPG) and their YOLO label files (.txt with the same "
           "name, classes 0=D00, 1=D10, 2=D20, 3=D40). This is the final test: freeze the model "
           "and threshold first, run once, and never tune on these photos.")

model = model_picker()
if model is None:
    st.stop()
conf = conf_slider()

files = st.file_uploader("Photos and label files", type=["jpg", "jpeg", "png", "txt"],
                         accept_multiple_files=True)
if not files:
    st.info("Select all photos and all .txt label files together.")
    st.stop()

images = {f.name.rsplit(".", 1)[0]: f for f in files if not f.name.lower().endswith(".txt")}
labels = {f.name.rsplit(".", 1)[0]: f for f in files if f.name.lower().endswith(".txt")}
pairs = sorted(set(images) & set(labels))
missing = sorted(set(images) - set(labels))
if missing:
    st.warning(f"No label file for: {', '.join(missing)}. A photo with no damage needs an "
               "empty .txt file.")
if not pairs:
    st.stop()


@st.cache_data(show_spinner=False)
def run(name, img_bytes, label_text, conf, model_name):
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    t0 = time.perf_counter()
    _, _, preds = detect(model, img, conf)
    secs = time.perf_counter() - t0
    gts = read_yolo_labels(label_text, img.width, img.height)
    res = match_image(gts, preds)
    return {"name": name, "gts": gts, "preds": preds, "res": res, "secs": secs}


results = []
bar = st.progress(0.0, text="Evaluating...")
for i, stem in enumerate(pairs):
    results.append(run(stem, images[stem].getvalue(), labels[stem].getvalue().decode(), conf,
                       st.session_state.get("model_name")))
    bar.progress((i + 1) / len(pairs), text=f"Evaluated {stem}")
bar.empty()

summary = pd.DataFrame(summarise([r["res"] for r in results]))
errors = [dict(e, image=r["name"]) for r in results for e in r["res"]["errors"]]
cat = Counter(e["category"] for e in errors)
tp_all, fp_all, fn_all = summary["TP"].sum(), summary["FP"].sum(), summary["FN"].sum()
micro_p = tp_all / (tp_all + fp_all) if tp_all + fp_all else 0
micro_r = tp_all / (tp_all + fn_all) if tp_all + fn_all else 0

c1, c2, c3, c4 = st.columns(4)
with c1:
    metric_card("Photos", len(results))
with c2:
    metric_card("Precision", f"{micro_p:.2f}")
with c3:
    metric_card("Recall", f"{micro_r:.2f}")
with c4:
    metric_card("CPU s / photo", f"{sum(r['secs'] for r in results) / len(results):.2f}")

st.subheader("Per-class results (IoU ≥ 0.5)")
st.dataframe(summary, hide_index=True, width="stretch")
st.caption(f"Confidence threshold {conf if isinstance(conf, dict) else round(conf, 2)}. mAP is computed in the evaluation notebook; this "
           "page reports precision, recall and F1 at the app's operating threshold.")

st.subheader("Confusion matrix")
labels_cm = CLASSES + ["background"]
cm = pd.DataFrame(0, index=labels_cm, columns=labels_cm)
for r in results:
    for t, p in r["res"]["confusion"]:
        cm.loc[t, p] += 1
fig = go.Figure(go.Heatmap(z=cm.values, x=[f"pred {c}" for c in labels_cm],
                           y=[f"true {c}" for c in labels_cm], colorscale=[[0, "#F5F7FB"],
                                                                          [1, ACCENT]],
                           text=cm.values, texttemplate="%{text}", showscale=False))
fig.update_layout(height=420, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                  font_color="#111827", yaxis_autorange="reversed")
st.plotly_chart(fig, width="stretch")

st.subheader("Error analysis")
e1, e2, e3 = st.columns(3)
with e1:
    metric_card("Missed damage (FN)", cat.get("missed", 0), "#D95B55")
with e2:
    metric_card("False alarms (FP)", cat.get("false_alarm", 0), "#F3B548")
with e3:
    metric_card("Wrong class", cat.get("wrong_class", 0), "#4FC3F7")

if errors:
    err_df = pd.DataFrame([{"Image": e["image"], "Category": e["category"], "True": e["true"],
                            "Predicted": e["pred"],
                            "Confidence": None if e["conf"] is None else round(e["conf"], 2)}
                           for e in errors])
    st.dataframe(err_df.groupby(["Category", "True", "Predicted"]).size()
                 .reset_index(name="Count").sort_values("Count", ascending=False),
                 hide_index=True, width="stretch")
    st.download_button("⬇️ All errors (CSV)", err_df.to_csv(index=False),
                       "local_test_errors.csv", "text/csv")

    st.markdown("**Gallery** (green = our label, red = model). Write a reason and a fix for each "
                "category in the report.")
    choice = st.selectbox("Category", ["missed", "false_alarm", "wrong_class"],
                          format_func={"missed": "Missed damage", "false_alarm": "False alarms",
                                       "wrong_class": "Wrong class"}.get)
    shown = [r for r in results if any(e["category"] == choice for e in r["res"]["errors"])]
    cols = st.columns(3)
    for i, r in enumerate(shown[:12]):
        img = Image.open(io.BytesIO(images[r["name"]].getvalue())).convert("RGB")
        img = blur_boxes(img, find_sensitive(img))
        cols[i % 3].image(draw_boxes(img, r["gts"], r["preds"]), caption=r["name"],
                          width="stretch")
else:
    st.success("No errors at this threshold.")
