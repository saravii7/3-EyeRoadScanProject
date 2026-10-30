"""Public home: what 3-Eye does, in Arabic first."""
import streamlit as st

from i18n import lang, t
from reports import all_reports
from utils import metric_card

ar = lang() == "ar"
st.markdown(
    f"""
    <div class="hero">
      <h1><span dir="ltr">👁️ 3-Eye</span></h1>
      <p>{"طرق أذكى، تنقّل أكثر أماناً. صوّر الضرر، ونحن نحدّد نوعه وأولويته ونرسله لفريق البلدية."
          if ar else "Smarter roads, safer journeys. Photograph the damage; we detect it, score "
          "its priority and send it to the municipal team."}</p>
    </div>
    """,
    unsafe_allow_html=True,
)

c1, c2 = st.columns(2)
c1.page_link("views/c_report.py", label=t("p_report"), icon="📸")
c2.page_link("views/c_mine.py", label=t("p_mine"), icon="🧾")

df = all_reports()
st.write("")
k1, k2, k3 = st.columns(3)
with k1:
    metric_card("بلاغات مستلمة" if ar else "Reports received", len(df))
with k2:
    metric_card("تم إصلاحها" if ar else "Repaired",
                int((df["status"] == "repaired").sum()) if len(df) else 0, "#43A878")
with k3:
    metric_card("قيد المعالجة" if ar else "In progress",
                int(df["status"].isin(["review", "scheduled", "in_progress"]).sum()) if len(df) else 0,
                "#E7A83F")

st.subheader("كيف يعمل؟" if ar else "How it works")
s1, s2, s3 = st.columns(3)
s1.info(("**١. صوّر**\n\nصورة واضحة للضرر من الرصيف، والموقع مفعّل في الكاميرا." if ar else
         "**1. Photograph**\n\nA clear photo from the pavement, with location on."))
s2.warning(("**٢. التحليل**\n\nنموذجنا يحدد نوع الضرر من 4 أنواع: D00 و D10 و D20 و D40، ويحسب الأولوية من 0 إلى 100، "
            "ويتأكد إن البلاغ مو مكرر." if ar else
            "**2. Analysis**\n\nOur model finds the damage type (D00-D40), scores priority 0-100 "
            "and checks for duplicates."))
s3.success(("**٣. المتابعة**\n\nتتابع حالة بلاغك: جديد ← مراجعة ← مجدول ← تم الإصلاح." if ar else
            "**3. Follow-up**\n\nTrack your report: new → review → scheduled → repaired."))
st.caption(("لا تصوّر أثناء القيادة. تُغبَّش الوجوه واللوحات تلقائياً. " if ar else
            "Never photograph while driving. Faces and plates are blurred automatically. ")
           + t("ai_note"))
