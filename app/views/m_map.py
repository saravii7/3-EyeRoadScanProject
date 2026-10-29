"""Municipality: open reports on a map, coloured by status, sized by priority."""
import folium
import streamlit as st
from streamlit_folium import st_folium

from i18n import OPEN_STATUSES, STATUSES, STATUS_COLOR, lang, ref, status_label, t
from reports import all_reports

ar = lang() == "ar"
st.title("🗺️ " + t("p_map"))

df = all_reports()
if df.empty:
    st.info(t("no_reports"))
    st.stop()
status_f = st.multiselect(t("status"), STATUSES, default=OPEN_STATUSES, format_func=status_label)
d = df[df["status"].isin(status_f)]
geo = d.dropna(subset=["lat", "lon"])
missing = len(d) - len(geo)

if geo.empty:
    st.info("لا توجد بلاغات بإحداثيات." if ar else "No reports with coordinates.")
else:
    m = folium.Map(location=[geo["lat"].mean(), geo["lon"].mean()], zoom_start=13,
                   attributionControl=False)
    for _, r in geo.iterrows():
        folium.CircleMarker(
            [r["lat"], r["lon"]], radius=7 + r["priority"] / 9, color=STATUS_COLOR[r["status"]],
            fill=True, fill_opacity=.85,
            tooltip=f"{ref(r['id'])} · {r['priority']:.0f}",
            popup=folium.Popup(f"<b>{ref(r['id'])}</b><br>{status_label(r['status'])}<br>"
                               f"{t('priority')}: {r['priority']:.0f}<br>{r['classes']}<br>"
                               f"{r['address'] or ''}", max_width=260)).add_to(m)
    st_folium(m, height=520, key="m_map", returned_objects=[])
    legend = " ".join(f'<span class="chip" style="background:{STATUS_COLOR[s]}22;'
                      f'color:{STATUS_COLOR[s]}">● {status_label(s)}</span>' for s in status_f)
    st.markdown(legend, unsafe_allow_html=True)
    st.caption("حجم الدائرة = الأولوية · Map data © OpenStreetMap contributors" if ar else
               "Circle size = priority · Map data © OpenStreetMap contributors")
if missing:
    st.warning((f"{missing} بلاغ بدون إحداثيات (لا تظهر على الخريطة)." if ar else
                f"{missing} report(s) without coordinates are not on the map."))
