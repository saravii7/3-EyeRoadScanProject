"""3-Eye (RoadScan, AIEP capstone Track A). Run with:  streamlit run Home.py

Arabic-first app for citizens and the municipality, running the team's real run-17 YOLOv8s,
the priority formula, DINOv2 + FAISS duplicate search and a Saudi-only location check.
The technical section shows the full pipeline, evaluation and results for the panel."""
import streamlit as st

from i18n import lang, language_switch, t
from utils import apply_style

st.set_page_config(page_title="3-Eye · RoadScan", page_icon="👁️", layout="wide")

pages = {
    t("sec_citizen"): [
        st.Page("views/c_home.py", title=t("p_home"), icon="🏠", default=True),
        st.Page("views/c_report.py", title=t("p_report"), icon="📸"),
        st.Page("views/c_mine.py", title=t("p_mine"), icon="🧾"),
    ],
    t("sec_city"): [
        st.Page("views/m_overview.py", title=t("p_overview"), icon="🏛️"),
        st.Page("views/m_queue.py", title=t("p_queue"), icon="📋"),
        st.Page("views/m_detail.py", title=t("p_detail"), icon="🔎"),
        st.Page("views/m_map.py", title=t("p_map"), icon="🗺️"),
        st.Page("views/m_maint.py", title=t("p_maint"), icon="🛠️"),
        st.Page("views/m_outbox.py", title=t("p_outbox"), icon="📲"),
        st.Page("views/m_analytics.py", title=t("p_analytics"), icon="📈"),
        st.Page("views/m_health.py", title=t("p_health"), icon="🩺"),
    ],
    t("sec_tech"): [
        st.Page("views/t_project.py", title="Project overview", icon="🛣️"),
        st.Page("pages/1_Image_Analysis.py", title="Image Analysis (full pipeline)", icon="🔍"),
        st.Page("pages/2_Damage_Map.py", title="Batch photo map", icon="🧭"),
        st.Page("pages/3_Local_Test.py", title="Local test & error analysis", icon="🧪"),
        st.Page("pages/3_Model_Results.py", title="Model results", icon="📊"),
        st.Page("pages/4_Priority_Score.py", title="Priority score", icon="🎯"),
        st.Page("pages/5_About.py", title="About & responsible AI", icon="👥"),
    ],
}

try:
    nav = st.navigation(pages, expanded=True)
except TypeError:  # older Streamlit
    nav = st.navigation(pages)
st.sidebar.markdown(f"### 👁️ 3-Eye\n{t('app_tag')}")
language_switch()
technical = nav.url_path in {p.url_path for p in pages[t("sec_tech")]}
apply_style(rtl=(lang() == "ar" and not technical))
nav.run()
