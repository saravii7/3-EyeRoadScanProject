"""Interactive explainer for the team's priority formula (priority.py) with a sensitivity check."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from priority import WEIGHTS, priority_score
from utils import ACCENT, PHOTO_TYPES, conf_slider, apply_style, band, detect, model_picker, open_photo

st.title("🎯 Priority Score")
st.write("Every report gets a score from 0 to 100. Higher means fix first.")
st.code("priority = 100 × (0.45·type + 0.20·size + 0.20·count + 0.15·confidence)",
        language=None)

# Worked examples from priority.py (image 1000 x 500)
W, H = 1000, 500
EXAMPLES = {
    "A: one thin crack (2% of image)":
        [{"cls": "D00", "x": 0, "y": 0, "w": 100, "h": 100, "conf": 0.6}],
    "B: one pothole (10% of image)":
        [{"cls": "D40", "x": 0, "y": 0, "w": 250, "h": 200, "conf": 0.9}],
    "C: five potholes (~30% of image)":
        [{"cls": "D40", "x": 0, "y": 0, "w": 173, "h": 173, "conf": 0.95}] * 5,
}

st.subheader("Try other weights")
cols = st.columns(4)
weights = {}
for col, (k, v) in zip(cols, WEIGHTS.items()):
    weights[k] = col.slider(k.capitalize(), 0.0, 1.0, float(v), 0.05)
if sum(weights.values()) == 0:
    st.error("At least one weight must be above 0.")
    st.stop()

rows = []
for name, dets in EXAMPLES.items():
    base = priority_score(dets, W, H)
    new = priority_score(dets, W, H, weights)
    rows.append({"Example": name, "Team formula": round(base, 1), "Your weights": round(new, 1),
                 "Decision": band(new)[0]})
df = pd.DataFrame(rows)

fig = go.Figure()
fig.add_bar(name="Team formula", x=df["Example"], y=df["Team formula"], marker_color="#6C7A96")
fig.add_bar(name="Your weights", x=df["Example"], y=df["Your weights"], marker_color=ACCENT)
fig.add_hline(y=70, line_dash="dot", line_color="#D95B55", annotation_text="Urgent")
fig.add_hline(y=40, line_dash="dot", line_color="#F3B548", annotation_text="Schedule")
fig.update_layout(barmode="group", yaxis_range=[0, 105], paper_bgcolor="rgba(0,0,0,0)",
                  plot_bgcolor="rgba(0,0,0,0)", font_color="#111827",
                  legend=dict(orientation="h", y=-0.15))
st.plotly_chart(fig, width="stretch")
st.dataframe(df, width="stretch", hide_index=True)

st.subheader("Sensitivity check 1: three worked examples, each weight ±20%")
sens = []
for k in WEIGHTS:
    for f in (0.8, 1.2):
        w = dict(WEIGHTS, **{k: WEIGHTS[k] * f})
        scores = [priority_score(d, W, H, w) for d in EXAMPLES.values()]
        order = "A < B < C" if scores[0] < scores[1] < scores[2] else "order changed"
        sens.append({"Weight": k, "Change": f"{round((f - 1) * 100):+d}%",
                     "A": round(scores[0], 1), "B": round(scores[1], 1),
                     "C": round(scores[2], 1), "Ranking": order})
sens_df = pd.DataFrame(sens)
st.dataframe(sens_df, width="stretch", hide_index=True)
if (sens_df["Ranking"] == "A < B < C").all():
    st.success("The ranking A < B < C stays the same for every ±20% change.")
else:
    st.warning("Some weight changes alter the ranking.")
st.caption("These three examples are far apart, so a stable order here is expected. "
           "Check 2 below repeats the test on real detector output.")

# ---------- Sensitivity on real photos ----------
st.subheader("Sensitivity check 2: real photos, each weight ±20%")
st.write("Upload several road photos. The detector scores each one with the team formula, then "
         "again with every weight moved by ±20%. We count how many photos change their "
         "decision band and how much the ranking moves.")
files = st.file_uploader("Photos for the sensitivity check", type=PHOTO_TYPES,
                         accept_multiple_files=True, key="sens_photos")
if files:
    model = model_picker()
    if model is None:
        st.stop()
    conf = conf_slider()
    reports = []
    with st.spinner("Detecting damage..."):
        for f in files:
            img = open_photo(f)
            if img is None:
                continue
            img = img.convert("RGB")
            _, _, dets = detect(model, img, conf)
            reports.append((f.name, dets, img.width, img.height))
    if len(reports) < 2:
        st.info("Upload at least two photos that open correctly.")
    else:
        base_scores = pd.Series([priority_score(d, w, h) for _, d, w, h in reports])
        base_bands = [band(x)[0] for x in base_scores]
        rows = []
        for k in WEIGHTS:
            for f in (0.8, 1.2):
                w = dict(WEIGHTS, **{k: WEIGHTS[k] * f})
                new = pd.Series([priority_score(d, ww, hh, w) for _, d, ww, hh in reports])
                moved = sum(band(x)[0] != b for x, b in zip(new, base_bands))
                rho = base_scores.corr(new, method="spearman")
                rows.append({"Weight": k, "Change": f"{round((f - 1) * 100):+d}%",
                             "Rank correlation (Spearman)": round(rho, 3) if rho == rho else 1.0,
                             "Photos that change band": f"{moved} of {len(reports)}",
                             "Largest score change": round((new - base_scores).abs().max(), 1)})
        real_df = pd.DataFrame(rows)
        st.dataframe(real_df, width="stretch", hide_index=True)
        worst = real_df["Rank correlation (Spearman)"].min()
        st.success(f"Lowest rank correlation: {worst:.3f} (1.0 = same order). "
                   f"Photos scored: {len(reports)}.")
        st.dataframe(pd.DataFrame({"Photo": [r[0] for r in reports],
                                   "Damages": [len(r[1]) for r in reports],
                                   "Team priority": base_scores.round(1),
                                   "Decision": base_bands}).sort_values(
                         "Team priority", ascending=False),
                     width="stretch", hide_index=True)

st.markdown('<p class="note">Formula: draft v1 from priority.py; the weights are proposals to '
            "re-check on real detector output. The Urgent/Schedule/Monitor bands (70/40) are an "
            "app proposal.</p>", unsafe_allow_html=True)
