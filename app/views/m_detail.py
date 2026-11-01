"""Municipality: one report. Evidence, location, and the actions that move it to repair."""
import datetime as dt

import folium
import streamlit as st
from streamlit_folium import st_folium

from i18n import STATUSES, STATUS_COLOR, TEAMS, event_text, lang, ref, status_label, t
from reports import add_note, all_reports, crop_path, get_report, thumb_path, update_report
from utils import chip, metric_card

ar = lang() == "ar"
st.title("🔎 " + t("p_detail"))

df = all_reports()
if df.empty:
    st.info(t("no_reports"))
    st.stop()
ids = list(df.sort_values("priority", ascending=False)["id"])
current = st.session_state.get("detail_id", ids[0])
rid = st.selectbox(t("ref"), ids, index=ids.index(current) if current in ids else 0, format_func=ref)
st.session_state["detail_id"] = rid
r = get_report(rid)
status = r.get("status", "new")

st.markdown(f"## {ref(rid)} " + chip(status_label(status), STATUS_COLOR[status]) +
            chip(t(r.get("decision") or "Monitor"), "#D95B55" if r.get("decision") == "Urgent"
                 else "#F3B548" if r.get("decision") == "Schedule" else "#43A878"),
            unsafe_allow_html=True)

k1, k2, k3, k4 = st.columns(4)
with k1:
    metric_card(t("priority"), f"{r.get('priority', 0):.0f}")
with k2:
    metric_card("عدد الأضرار" if ar else "Damages", r.get("damages", 0))
with k3:
    metric_card(t("reported_times"), r.get("times_reported", 1), "#8E7BD1")
with k4:
    metric_card(t("team"), r.get("team") or "—", "#F4F6F5")

left, right = st.columns([3, 2])
with left:
    tp = thumb_path(rid)
    if tp:
        st.image(str(tp), caption=("صورة البلاغ مع الكشف (مغبّشة)" if ar else
                                   "Report photo with detections (blurred)"), width="stretch")
    crops = [(c, crop_path(rid, c)) for c in r.get("classes", [])]
    crops = [(c, p) for c, p in crops if p]
    if crops:
        cc = st.columns(len(crops))
        for col, (c, p) in zip(cc, crops):
            col.image(str(p), caption=f"{c} · {t(c)}", width="stretch")
with right:
    st.markdown(f"**{t('address')}:** {r.get('address') or '—'}")
    if r.get("lat") is not None:
        m = folium.Map(location=(r["lat"], r["lon"]), zoom_start=16, attributionControl=False)
        folium.Marker((r["lat"], r["lon"]), icon=folium.Icon(color="red", icon="exclamation-sign")
                      ).add_to(m)
        st_folium(m, height=260, key=f"detail_map_{rid}", returned_objects=[])
        st.markdown(f"[Google Maps](https://www.google.com/maps?q={r['lat']:.6f},{r['lon']:.6f})")
    if r.get("description"):
        st.markdown(f"**{'وصف المواطن' if ar else 'Citizen note'}:** {r['description']}")
    boxes = r.get("boxes", [])
    if boxes:
        st.markdown("**" + ("الكشف" if ar else "Detections") + "**")
        for b in boxes:
            st.markdown(f"- {b['cls']} · {t(b['cls'])} · {b.get('conf', 0):.2f}")
    st.caption(f"{'النموذج' if ar else 'Model'}: {r.get('model') or '—'} · "
               f"{r.get('seconds') or '—'} s")

st.divider()
st.subheader("الإجراءات" if ar else "Actions")
with st.form(f"actions_{rid}"):
    a1, a2, a3 = st.columns(3)
    new_status = a1.selectbox(t("status"), STATUSES, index=STATUSES.index(status),
                              format_func=status_label)
    team_opts = ["—"] + TEAMS
    new_team = a2.selectbox(t("team"), team_opts,
                            index=team_opts.index(r["team"]) if r.get("team") in team_opts else 0)
    old_date = r.get("scheduled_for")
    new_date = a3.date_input("موعد الصيانة" if ar else "Repair date",
                             value=dt.date.fromisoformat(old_date) if old_date else None)
    note = st.text_area("ملاحظة داخلية" if ar else "Internal note")
    if st.form_submit_button("حفظ" if ar else "Save", type="primary"):
        if new_team != (r.get("team") or "—"):
            update_report(rid, event=f"team:{new_team}", team=None if new_team == "—" else new_team)
        if new_date and str(new_date) != old_date:
            update_report(rid, event=f"scheduled:{new_date}", scheduled_for=str(new_date))
        if new_status != status:
            extra = {"repaired_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M")} \
                if new_status == "repaired" else {}
            update_report(rid, event=f"status:{new_status}", status=new_status, **extra)
        if note.strip():
            add_note(rid, note)
            update_report(rid, event="note")
        st.rerun()

n1, n2 = st.columns(2)
with n1:
    st.subheader("السجل" if ar else "Timeline")
    for h in reversed(r.get("history", [])):
        st.markdown(f"- `{h['time']}` · {event_text(h.get('event', ''))}")
with n2:
    st.subheader("ملاحظات داخلية" if ar else "Internal notes")
    notes = r.get("notes", [])
    if not notes:
        st.caption("لا توجد ملاحظات." if ar else "No notes.")
    for n in reversed(notes):
        st.markdown(f"- `{n['time']}` · {n['text']}")
st.caption(t("ai_note"))
