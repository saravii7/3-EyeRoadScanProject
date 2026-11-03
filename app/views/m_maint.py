"""Municipality: maintenance board by team. Start and finish work items."""
import datetime as dt

import streamlit as st

from i18n import STATUS_COLOR, TEAMS, lang, ref, status_label, t
from reports import all_reports, update_report
from utils import chip

ar = lang() == "ar"
st.title("🛠️ " + t("p_maint"))
st.caption("البلاغات المجدولة وقيد التنفيذ، مقسّمة حسب الفريق." if ar else
           "Scheduled and in-progress work, by team.")

df = all_reports()
work = df[df["status"].isin(["scheduled", "in_progress"])] if not df.empty else df
if work.empty:
    st.info("لا توجد أعمال صيانة مجدولة. افتح بلاغاً من القائمة وأسنده لفريق." if ar else
            "No scheduled work. Open a report from the queue and assign a team.")
    st.page_link("views/m_queue.py", label=t("p_queue"), icon="📋")
    st.stop()


def _start(rid):
    update_report(rid, event="status:in_progress", status="in_progress")


def _done(rid):
    update_report(rid, event="status:repaired", status="repaired",
                  repaired_at=dt.datetime.now().strftime("%Y-%m-%d %H:%M"))


teams = TEAMS  # only real teams (no "Unassigned" column)
cols = st.columns(len(teams))
for col, team in zip(cols, teams):
    with col:
        items = work[work["team"].fillna("—") == team].sort_values("priority", ascending=False)
        st.markdown(f"#### {team if team != '—' else ('بدون فريق' if ar else 'Unassigned')}")
        st.caption(f"{len(items)} " + ("عمل" if ar else "items"))
        for _, r in items.iterrows():
            with st.container(border=True):
                st.markdown(f"**{ref(r['id'])}** · {r['priority']:.0f} " +
                            chip(status_label(r["status"]), STATUS_COLOR[r["status"]]),
                            unsafe_allow_html=True)
                st.caption(f"{r['classes']} · {r['address'] or '—'}")
                st.caption(("الموعد: " if ar else "Date: ") + (r["scheduled_for"] or "—"))
                if r["status"] == "scheduled":
                    st.button("بدء العمل" if ar else "Start", key=f"s{r['id']}",
                              on_click=_start, args=(r["id"],))
                else:
                    st.button("تم الإصلاح ✓" if ar else "Mark repaired ✓", key=f"d{r['id']}",
                              on_click=_done, args=(r["id"],), type="primary")
