"""Municipality: today's operational signal."""
import plotly.express as px
import streamlit as st

from i18n import OPEN_STATUSES, STATUS_COLOR, lang, ref, status_label, t
from reports import all_reports
from utils import PLOT, chip, metric_card

ar = lang() == "ar"
st.title("🏛️ " + t("p_overview"))
st.caption("الإشارة التشغيلية لسلامة الطرق اليوم." if ar else "Today's road-safety signal.")

df = all_reports()
if df.empty:
    st.info(t("no_reports"))
    st.stop()

open_ = df[df["status"].isin(OPEN_STATUSES)]
cards = [("إجمالي البلاغات" if ar else "Total reports", len(df), "#111827"),
         ("تحتاج مراجعة" if ar else "Need review", int((df["status"] == "new").sum()), "#1EC7B6"),
         ("عاجلة مفتوحة" if ar else "Open urgent", int((open_["decision"] == "Urgent").sum()), "#D95B55"),
         ("مجدولة" if ar else "Scheduled", int((df["status"] == "scheduled").sum()), "#F3B548"),
         ("قيد التنفيذ" if ar else "In progress", int((df["status"] == "in_progress").sum()), "#3B82F6"),
         ("تم الإصلاح" if ar else "Repaired", int((df["status"] == "repaired").sum()), "#43A878"),
         ("بلاغات مكررة مربوطة" if ar else "Linked repeats",
          int((df["times_reported"] - 1).clip(lower=0).sum()), "#8E7BD1")]
cols = st.columns(4)
for i, (label, value, color) in enumerate(cards):
    with cols[i % 4]:
        metric_card(label, value, color)
    if i == 3:
        cols = st.columns(4)

st.write("")
a, b = st.columns(2)
with a:
    st.subheader("توزيع الأولوية" if ar else "Priority distribution")
    d = open_.assign(decision=open_["decision"].map(lambda x: t(x or "Monitor")))
    fig = px.histogram(d, x="priority", nbins=10, range_x=[0, 100],
                       color_discrete_sequence=["#1EC7B6"])
    fig.update_layout(height=280, bargap=.1, **PLOT)
    st.plotly_chart(fig, width="stretch")
with b:
    st.subheader("أنواع الأضرار" if ar else "Damage types")
    cls = df["classes"].str.split(", ").explode().value_counts().reset_index()
    cls.columns = ["code", "n"]
    cls["label"] = cls["code"].map(lambda c: f"{c} · {t(c)}")
    fig = px.bar(cls, x="n", y="label", orientation="h", color_discrete_sequence=["#082B36"])
    fig.update_layout(height=280, yaxis_title="", xaxis_title="", **PLOT)
    st.plotly_chart(fig, width="stretch")


def _open(rid):
    st.session_state["detail_id"] = int(rid)


c, d = st.columns(2)
with c:
    st.subheader("أعلى البلاغات أولوية" if ar else "Highest priority")
    for _, r in open_.sort_values("priority", ascending=False).head(5).iterrows():
        st.markdown(f"**{ref(r['id'])}** · {r['priority']:.0f} · " +
                    chip(status_label(r["status"]), STATUS_COLOR[r["status"]]) +
                    f" · {r['address'] or '—'}", unsafe_allow_html=True)
with d:
    st.subheader("أحدث البلاغات" if ar else "Most recent")
    for _, r in df.head(5).iterrows():
        st.markdown(f"**{ref(r['id'])}** · {r['added']} · " +
                    chip(status_label(r["status"]), STATUS_COLOR[r["status"]]),
                    unsafe_allow_html=True)
st.page_link("views/m_queue.py", label=t("p_queue"), icon="📋")
