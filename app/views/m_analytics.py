"""Municipality: analytics over all reports (real data saved by the app)."""
import pandas as pd
import plotly.express as px
import streamlit as st

from i18n import STATUS_COLOR, lang, status_label, t
from reports import all_reports
from utils import PLOT, metric_card

ar = lang() == "ar"
st.title("📈 " + t("p_analytics"))

df = all_reports()
if df.empty:
    st.info(t("no_reports"))
    st.stop()

df["added_dt"] = pd.to_datetime(df["added"], errors="coerce")
df["repaired_dt"] = pd.to_datetime(df["repaired_at"], errors="coerce")
fix_hours = (df["repaired_dt"] - df["added_dt"]).dt.total_seconds().div(3600).dropna()

k1, k2, k3, k4 = st.columns(4)
with k1:
    metric_card("متوسط الأولوية" if ar else "Mean priority", f"{df['priority'].mean():.0f}")
with k2:
    metric_card("نسبة الإصلاح" if ar else "Repair rate",
                f"{(df['status'] == 'repaired').mean() * 100:.0f}%", "#43A878")
with k3:
    metric_card("زمن الإصلاح (ساعة)" if ar else "Time to repair (h)",
                f"{fix_hours.median():.1f}" if len(fix_hours) else "—", "#F3B548")
with k4:
    secs = pd.to_numeric(df["seconds"], errors="coerce").dropna()
    metric_card("زمن التحليل (ث)" if ar else "Analysis time (s)",
                f"{secs.median():.2f}" if len(secs) else "—", "#3B82F6")

a, b = st.columns(2)
with a:
    st.subheader("البلاغات يومياً" if ar else "Reports per day")
    per_day = df.groupby(df["added_dt"].dt.date).size().reset_index(name="n")
    per_day.columns = ["day", "n"]
    fig = px.bar(per_day, x="day", y="n", color_discrete_sequence=["#1EC7B6"])
    fig.update_layout(height=300, xaxis_title="", yaxis_title="", **PLOT)
    st.plotly_chart(fig, width="stretch")
with b:
    st.subheader(t("status"))
    s = df["status"].value_counts().reset_index()
    s.columns = ["status", "n"]
    s["label"] = s["status"].map(status_label)
    fig = px.bar(s, x="n", y="label", orientation="h", color="status",
                 color_discrete_map=STATUS_COLOR)
    fig.update_layout(height=300, showlegend=False, xaxis_title="", yaxis_title="", **PLOT)
    st.plotly_chart(fig, width="stretch")

c, d = st.columns(2)
with c:
    st.subheader(t("classes"))
    cls = df["classes"].str.split(", ").explode().value_counts().reset_index()
    cls.columns = ["code", "n"]
    cls["label"] = cls["code"].map(lambda x: f"{x} · {t(x)}")
    fig = px.bar(cls, x="label", y="n", color_discrete_sequence=["#082B36"])
    fig.update_layout(height=300, xaxis_title="", yaxis_title="", **PLOT)
    st.plotly_chart(fig, width="stretch")
with d:
    st.subheader(t("decision"))
    dec = df["decision"].fillna("Monitor").value_counts().reset_index()
    dec.columns = ["decision", "n"]
    dec["label"] = dec["decision"].map(t)
    fig = px.bar(dec, x="label", y="n", color="decision",
                 color_discrete_map={"Urgent": "#D95B55", "Schedule": "#F3B548",
                                     "Monitor": "#43A878"})
    fig.update_layout(height=300, showlegend=False, xaxis_title="", yaxis_title="", **PLOT)
    st.plotly_chart(fig, width="stretch")
st.caption("كل الأرقام من بلاغات حقيقية حُفظت في التطبيق، وليست بيانات تجريبية." if ar else
           "All numbers come from reports saved in the app, not sample data.")
