"""Technical project overview (for the panel)."""
import streamlit as st

from utils import CLASS_INFO, metric_card


st.markdown(
    """
    <div class="hero">
      <h1><span dir="ltr"><span style="color:#1EC7B6">3</span>-Eye · Road Intelligence</span></h1>
      <p>AI road damage detection for municipal maintenance teams.
         Upload a street photo, find the damage, and know what to fix first.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Headline numbers (edit with your final results)
c1, c2, c3, c4 = st.columns(4)
with c1:
    metric_card("Damage classes", "4")
with c2:
    metric_card("Training images", "8,999")
with c3:
    metric_card("Seconds per photo (CPU)", "0.19")
with c4:
    metric_card("Countries", "5")

st.write("")
st.subheader("What we detect")
cols = st.columns(4)
for col, (code, info) in zip(cols, CLASS_INFO.items()):
    with col:
        st.markdown(
            f'<div class="card"><div class="value" style="color:{info["color"]}">{code}</div>'
            f'<div class="label">{info["name"]}<br>{info["ar"]}</div></div>',
            unsafe_allow_html=True,
        )

st.write("")
st.subheader("How it works")
s1, s2, s3 = st.columns(3)
s1.info("**1. Upload**\n\nA street photo from a phone or car camera.")
s2.warning("**2. Detect**\n\nOur run-17 YOLOv8s finds cracks and potholes, scores repair priority and "
           "checks for duplicates (DINOv2 + FAISS).")
s3.success("**3. Act**\n\nA repair priority from 0 to 100, a map of reports, and a work queue to download.")

st.caption("Technical pages: Image Analysis (full pipeline with timings), Damage Map, Local Test, "
           "Model Results, Priority Score, About.")
