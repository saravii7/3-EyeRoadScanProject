"""Municipality: the report queue, highest priority first, with filters and export."""
import streamlit as st

from i18n import OPEN_STATUSES, STATUSES, lang, ref, status_label, t
from reports import all_reports, as_data_uri, clear_all, thumb_path, to_geojson

ar = lang() == "ar"
st.title("📋 " + t("p_queue"))
st.caption("مرتبة حسب الأولوية. المكرر يُربط بالبلاغ الأصلي ولا يُنشئ بلاغاً جديداً." if ar else
           "Sorted by priority. Repeats are linked to the original report, not duplicated.")

df = all_reports()
if df.empty:
    st.info(t("no_reports"))
    st.page_link("views/c_report.py", label=t("p_report"), icon="📸")
    st.stop()

f1, f2, f3, f4 = st.columns([2, 2, 2, 3])
status_f = f1.multiselect(t("status"), STATUSES, default=OPEN_STATUSES, format_func=status_label)
dec_f = f2.multiselect(t("decision"), ["Urgent", "Schedule", "Monitor"],
                       default=["Urgent", "Schedule", "Monitor"], format_func=t)
cls_f = f3.multiselect(t("classes"), ["D00", "D10", "D20", "D40"], format_func=lambda c: f"{c} {t(c)}")
search = f4.text_input("بحث (رقم أو موقع)" if ar else "Search (reference or place)")

q = df[df["status"].isin(status_f) & df["decision"].fillna("Monitor").isin(dec_f)]
if cls_f:
    q = q[q["classes"].apply(lambda s: any(c in s for c in cls_f))]
if search.strip():
    s = search.strip().lower()
    q = q[q.apply(lambda r: s in ref(r["id"]).lower() or s in str(r["address"]).lower(), axis=1)]
q = q.sort_values(["priority", "times_reported"], ascending=False).reset_index(drop=True)
q.insert(0, "rank", range(1, len(q) + 1))

view = q.assign(
    photo=[as_data_uri(thumb_path(i)) for i in q["id"]],
    reference=[ref(i) for i in q["id"]],
    status_txt=[status_label(s) for s in q["status"]],
    decision_txt=[t(d or "Monitor") for d in q["decision"]],
    address=q["address"].fillna("—"), team=q["team"].fillna("—"))
event = st.dataframe(
    view[["rank", "photo", "reference", "priority", "decision_txt", "status_txt", "classes",
          "times_reported", "team", "address", "added"]],
    hide_index=True, width="stretch", row_height=70, on_select="rerun",
    selection_mode="single-row",
    column_config={
        "rank": st.column_config.NumberColumn("#", width="small"),
        "photo": st.column_config.ImageColumn("📷", width="small"),
        "reference": t("ref"),
        "priority": st.column_config.ProgressColumn(t("priority"), min_value=0, max_value=100,
                                                    format="%.0f"),
        "decision_txt": t("decision"), "status_txt": t("status"), "classes": t("classes"),
        "times_reported": t("reported_times"), "team": t("team"), "address": t("address"),
        "added": t("added")})
st.caption("اختر صفاً لفتح تفاصيل البلاغ." if ar else "Select a row to open the report.")
rows = event.selection.rows if event and event.selection else []
if rows:
    rid = int(q.iloc[rows[0]]["id"])
    if st.button(("فتح تفاصيل " if ar else "Open ") + ref(rid), type="primary"):
        st.session_state["detail_id"] = rid
        st.switch_page("views/m_detail.py")

e1, e2 = st.columns(2)
e1.download_button("⬇️ CSV", q.to_csv(index=False), "3eye_queue.csv", "text/csv")
e2.download_button("⬇️ GeoJSON (GIS)", to_geojson(q.drop(columns=["rank"])), "3eye_queue.geojson",
                   "application/geo+json")

with st.expander("تصفير القائمة (للعرض)" if ar else "Reset the queue (for a demo)"):
    sure = st.checkbox("نعم، احذف كل البلاغات" if ar else "Yes, delete every report")
    if st.button("حذف الكل" if ar else "Delete all", disabled=not sure):
        clear_all()
        for k in ("saved_reports", "last_added", "my_reports", "citizen_done", "detail_id"):
            st.session_state.pop(k, None)
        st.rerun()
