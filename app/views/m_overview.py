"""Home: the 3-Eye control dashboard (brand look). Every number comes from the stored reports."""
import html

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from i18n import OPEN_STATUSES, STATUS_COLOR, lang, ref, status_label, t
from reports import all_reports, as_data_uri, get_report, thumb_path
from utils import brand_logo_uri

ar = lang() == "ar"
NAVY, PANEL, LINE, TEAL, AMBER, RED, GREEN, MIST, PAPER = (
    "#082B36", "#0E3440", "#1B4A57", "#1EC7B6", "#F3B548", "#D95B55", "#43A878", "#A6BBC0",
    "#F4F6F5")
PRIO = {"Urgent": (RED, "عالية" if ar else "High", "⚠️"),
        "Schedule": (AMBER, "متوسطة" if ar else "Medium", "⚠️"),
        "Monitor": (GREEN, "منخفضة" if ar else "Low", "✅")}

# ---------- page look: dark control-room canvas, only on this page ----------
st.markdown(f"""
<style>
[data-testid="stMain"], [data-testid="stAppViewContainer"] {{background: {NAVY};}}
[data-testid="stMain"] h1, [data-testid="stMain"] h2, [data-testid="stMain"] h3,
[data-testid="stMain"] p, [data-testid="stMain"] label {{color: {PAPER};}}
.dash-hello h1 {{font-size: 2.1rem; margin: 0; color: {PAPER};}}
.dash-hello p {{color: {MIST}; margin: .3rem 0 0;}}
.kpi {{background: white; border-radius: 16px; padding: 1rem 1.1rem; display: flex;
      align-items: center; gap: .9rem; height: 100%; box-shadow: 0 10px 28px rgba(0,0,0,.18);}}
.kpi .ic {{width: 54px; height: 54px; border-radius: 50%; display: flex; align-items: center;
          justify-content: center; font-size: 1.5rem; flex: none;}}
.kpi .lbl {{color: #4B5563; font-size: .92rem;}}
.kpi .val {{color: #111827; font-size: 1.9rem; font-weight: 700; line-height: 1.1;}}
.kpi .sub {{color: #6B7280; font-size: .8rem;}}
.panel {{background: {PANEL}; border: 1px solid {LINE}; border-radius: 16px; padding: 1rem 1.1rem;}}
.panel-title {{color: {PAPER}; font-weight: 700; font-size: 1.1rem; margin-bottom: .2rem;}}
.panel-sub {{color: {MIST}; font-size: .82rem; margin-bottom: .6rem;}}
.ex-img {{width: 100% !important; height: 340px; object-fit: cover; border-radius: 12px; display: block;}}
[data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] {{background: {PANEL};
       border: 1px solid {LINE} !important; border-radius: 16px;}}
.tag {{display: inline-block; padding: .18rem .7rem; border-radius: 999px; font-size: .82rem;
       font-weight: 600; margin: .15rem;}}
.tbl {{width: 100%; border-collapse: separate; border-spacing: 0; background: white;
       border-radius: 12px; overflow: hidden; font-size: .9rem;}}
.tbl th {{background: #EEF2F3; color: #374151; font-weight: 600; padding: .6rem .7rem;
          text-align: right;}}
.tbl td {{color: #111827; padding: .5rem .7rem; border-top: 1px solid #E5E7EB;
          vertical-align: middle;}}
.tbl img {{width: 64px; height: 42px; object-fit: cover; border-radius: 6px; display: block;}}
.leg span {{color: {MIST}; font-size: .8rem; margin-inline-end: .9rem;}}
[data-testid="stMain"] .stButton button {{background: transparent; color: {TEAL};
       border: 1px solid {TEAL}; border-radius: 10px;}}
</style>
""", unsafe_allow_html=True)

df = all_reports()

# ---------- header + KPI cards ----------
def how_it_works():
    st.markdown(f'<div class="panel-title" style="margin:1rem 0 .5rem">'
                f'{"كيف يعمل؟" if ar else "How it works"}</div>', unsafe_allow_html=True)
    s1, s2, s3 = st.columns(3)
    s1.info(("**١. صوّر**\n\nصورة واضحة للضرر من الرصيف، والموقع مفعّل في الكاميرا." if ar else
             "**1. Photograph**\n\nA clear photo from the pavement, with location on."))
    s2.warning(("**٢. التحليل**\n\nنموذجنا يحدد نوع الضرر من 4 أنواع: D00 و D10 و D20 و D40، "
                "ويحسب الأولوية من 0 إلى 100، ويتأكد إن البلاغ مو مكرر." if ar else
                "**2. Analysis**\n\nOur model finds the damage type (D00-D40), scores priority "
                "0-100 and checks for duplicates."))
    s3.success(("**٣. المتابعة**\n\nتتابع حالة بلاغك: جديد ← مراجعة ← مجدول ← تم الإصلاح." if ar
                else "**3. Follow-up**\n\nTrack your report: new → review → scheduled → repaired."))
    st.caption(("لا تصوّر أثناء القيادة. تُغبَّش الوجوه واللوحات تلقائياً. " if ar else
                "Never photograph while driving. Faces and plates are blurred automatically. ")
               + t("ai_note"))


hello, logo = st.columns([3, 1])
with hello:
    st.markdown(f"""<div class="dash-hello"><h1>{"مرحباً بك" if ar else "Welcome"}</h1>
    <p>{"طرق أذكى، تنقّل أكثر أماناً. صوّر الضرر، ونحن نحدّد نوعه وأولويته ونرسله لفريق البلدية."
        if ar else "Smarter roads, safer journeys. Photograph the damage; we detect it, score "
        "its priority and send it to the municipal team."}</p></div>""", unsafe_allow_html=True)
    b1, b2, _ = st.columns([1, 1, 2])
    b1.page_link("views/c_report.py", label=t("p_report"), icon="📸")
    b2.page_link("views/c_mine.py", label=t("p_mine"), icon="🧾")
with logo:
    st.markdown(f'<img src="{brand_logo_uri()}" style="width:100%;max-width:220px;'
                f'border-radius:18px;display:block;margin-inline-start:auto">',
                unsafe_allow_html=True)
st.write("")

if df.empty:
    st.info(t("no_reports"))
    how_it_works()
    st.stop()

open_ = df[df["status"].isin(OPEN_STATUSES)]
today = pd.Timestamp.now().normalize()
added = pd.to_datetime(df["added"], errors="coerce")
week = int((added >= today - pd.Timedelta(days=7)).sum())
kpis = [
    ("إجمالي البلاغات" if ar else "Total reports", len(df), "🛣️", "#E6F7F5",
     (f"{week} خلال آخر 7 أيام" if ar else f"{week} in the last 7 days")),
    ("عالية الأولوية" if ar else "High priority", int((open_["decision"] == "Urgent").sum()), "⚠️",
     "#FBE9E8", "تحتاج إلى معالجة عاجلة" if ar else "Need urgent repair"),
    ("قيد المعالجة" if ar else "In progress",
     int(df["status"].isin(["review", "scheduled", "in_progress"]).sum()), "⏱️", "#FDF3E1",
     "مراجعة أو مجدولة أو قيد التنفيذ" if ar else "Review, scheduled or under repair"),
    ("تمت المعالجة" if ar else "Repaired", int((df["status"] == "repaired").sum()), "✅",
     "#E3F4EA", "بلاغات أُغلقت بالإصلاح" if ar else "Closed as repaired"),
]
cols = st.columns(4)
for col, (label, value, icon, bg, sub) in zip(cols, kpis):
    col.markdown(f"""<div class="kpi"><div class="ic" style="background:{bg}">{icon}</div>
    <div><div class="lbl">{label}</div><div class="val">{value:,}</div>
    <div class="sub">{sub}</div></div></div>""", unsafe_allow_html=True)

st.write("")

# ---------- AI example + map ----------
a, b = st.columns([1.35, 1])
with a, st.container(border=True):
    shown = df[df["id"].map(lambda i: thumb_path(i) is not None)].sort_values(
        "priority", ascending=False).head(5)
    st.markdown(f'<div class="panel-title">'
                f'{"مثال من تحليل الصور بالذكاء الاصطناعي" if ar else "AI image analysis example"}'
                f'</div>', unsafe_allow_html=True)
    if shown.empty:
        st.markdown('<div class="panel-sub">—</div>', unsafe_allow_html=True)
    else:
        i = st.session_state.get("dash_ex", 0) % len(shown)
        r = shown.iloc[i]
        rep = get_report(r["id"]) or {}
        tags = "".join(
            f'<span class="tag" style="background:{TEAL}22;color:{TEAL};border:1px solid {TEAL}66">'
            f'{b_["cls"]} · {t(b_["cls"])} · {b_.get("conf", 0):.2f}</span>'
            for b_ in rep.get("boxes", [])[:4])
        where = html.escape(r["address"] or ("موقع غير متوفر" if ar else "No location"))
        st.markdown(f"""<div class="panel-sub">{ref(r['id'])} · 📍 {where} · {r['added']}</div>
        <img class="ex-img" src="{as_data_uri(thumb_path(r['id']))}">
        <div style="margin-top:.5rem">{tags}</div>""", unsafe_allow_html=True)
        p1, p2, p3 = st.columns([1, 2, 1])
        if p1.button("‹", key="ex_prev", width="stretch"):
            st.session_state["dash_ex"] = i - 1
            st.rerun()
        p2.markdown(f"<p style='text-align:center;color:{MIST}'>{i + 1} / {len(shown)}</p>",
                    unsafe_allow_html=True)
        if p3.button("›", key="ex_next", width="stretch"):
            st.session_state["dash_ex"] = i + 1
            st.rerun()

with b, st.container(border=True):
    st.markdown(f'<div class="panel-title">'
                f'{"توزيع البلاغات على الخريطة" if ar else "Reports on the map"}</div>'
                f'<div class="leg"><span>🔴 {PRIO["Urgent"][1]}</span><span>🟠 '
                f'{PRIO["Schedule"][1]}</span><span>🟢 {PRIO["Monitor"][1]}</span></div>',
                unsafe_allow_html=True)
    geo = open_.dropna(subset=["lat", "lon"])
    if geo.empty:
        st.markdown(f'<div class="panel-sub">{"لا توجد بلاغات مفتوحة بموقع." if ar else "No open reports with a location."}</div>',
                    unsafe_allow_html=True)
    else:
        m = folium.Map(location=[geo["lat"].mean(), geo["lon"].mean()], zoom_start=12,
                       attributionControl=False)
        colors = {"Urgent": "red", "Schedule": "orange", "Monitor": "green"}
        for _, g in geo.iterrows():
            folium.Marker([g["lat"], g["lon"]], tooltip=f"{ref(g['id'])} · {g['priority']:.0f}",
                          icon=folium.Icon(color=colors.get(g["decision"], "gray"),
                                           icon="exclamation-sign")).add_to(m)
        if len(geo) > 1:
            m.fit_bounds([[geo["lat"].min(), geo["lon"].min()], [geo["lat"].max(), geo["lon"].max()]])
        st_folium(m, height=420, key="dash_map", returned_objects=[])
        st.markdown('<div class="panel-sub">Map data © OpenStreetMap contributors</div>',
                    unsafe_allow_html=True)
        st.page_link("views/m_map.py", label="عرض الكل" if ar else "View all", icon="🗺️")

st.write("")

# ---------- maintenance queue ----------
st.markdown(f'<div class="panel-title" style="margin:.4rem 0 .6rem">'
            f'{"قائمة الصيانة والمعالجة" if ar else "Maintenance and repair queue"}</div>',
            unsafe_allow_html=True)
q = open_.sort_values("priority", ascending=False).head(6)
if q.empty:
    st.markdown(f'<div class="panel-sub">{"لا توجد بلاغات مفتوحة." if ar else "No open reports."}</div>',
                unsafe_allow_html=True)
else:
    heads = (["", "رقم البلاغ", "الموقع", "نوع الضرر", "الأولوية", "الثقة", "الحالة"] if ar else
             ["", "Report", "Location", "Damage", "Priority", "Confidence", "Status"])
    rows = []
    for _, r in q.iterrows():
        rep = get_report(r["id"]) or {}
        confs = [b_.get("conf", 0) for b_ in rep.get("boxes", [])]
        pc, plabel, picon = PRIO.get(r["decision"] or "Monitor", PRIO["Monitor"])
        sc = STATUS_COLOR.get(r["status"], MIST)
        img = as_data_uri(thumb_path(r["id"]))
        img_tag = f'<img src="{img}">' if img else ""
        kinds = "، ".join(t(c) for c in (r["classes"] or "").split(", ") if c) or "—"
        rows.append(
            f"<tr><td>{img_tag}</td>"
            f"<td><b>{ref(r['id'])}</b></td>"
            f"<td>{html.escape(r['address'] or '—')}</td><td>{kinds}</td>"
            f'<td><span class="tag" style="background:{pc}22;color:{pc};border:1px solid {pc}66">'
            f"{picon} {plabel} · {r['priority']:.0f}</span></td>"
            f"<td>{(sum(confs) / len(confs)) if confs else 0:.2f}</td>"
            f'<td><span class="tag" style="background:{sc}22;color:{sc};border:1px solid {sc}66">'
            f"{status_label(r['status'])}</span></td></tr>")
    st.markdown('<table class="tbl"><thead><tr>' + "".join(f"<th>{h}</th>" for h in heads) +
                "</tr></thead><tbody>" + "".join(rows) + "</tbody></table>",
                unsafe_allow_html=True)
    st.write("")
    pick = st.selectbox("فتح بلاغ" if ar else "Open a report", list(q["id"]), format_func=ref)
    if st.button("عرض التفاصيل" if ar else "View details"):
        st.session_state["detail_id"] = int(pick)
        st.switch_page("views/m_detail.py")
how_it_works()
