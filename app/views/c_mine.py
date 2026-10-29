"""Citizen: track my reports (this browser session) or look one up by reference number."""
import streamlit as st

from i18n import STATUS_COLOR, event_text, lang, ref, status_label, t
from reports import get_report, thumb_path
from utils import chip

ar = lang() == "ar"
st.title("🧾 " + t("p_mine"))

mine = list(dict.fromkeys(st.session_state.get("my_reports", [])))
lookup = st.text_input("ابحث برقم البلاغ (مثل RS-0001)" if ar else "Look up by reference (e.g. RS-0001)")
if lookup.strip():
    digits = "".join(ch for ch in lookup if ch.isdigit())
    if digits:
        mine = [int(digits)] + [m for m in mine if m != int(digits)]

if not mine:
    st.info("لا توجد بلاغات في هذه الجلسة. ارفع بلاغاً أو ابحث برقمه." if ar else
            "No reports in this session. Send one or search by its reference.")
    st.page_link("views/c_report.py", label=t("p_report"), icon="📸")
    st.stop()

for rid in mine:
    r = get_report(rid)
    if not r:
        st.warning(f"{ref(rid)}: " + ("غير موجود" if ar else "not found"))
        continue
    status = r.get("status", "new")
    with st.container(border=True):
        a, b = st.columns([1, 3])
        tp = thumb_path(rid)
        if tp:
            a.image(str(tp), width="stretch")
        with b:
            st.markdown(f"#### {ref(rid)} " + chip(status_label(status), STATUS_COLOR[status]),
                        unsafe_allow_html=True)
            st.markdown(f"**{t('classes')}:** " + "، ".join(f"{c} {t(c)}" for c in r.get("classes", []))
                        if ar else f"**{t('classes')}:** " +
                        ", ".join(f"{c} {t(c)}" for c in r.get("classes", [])))
            st.markdown(f"**{t('address')}:** {r.get('address') or '—'}")
            st.markdown(f"**{t('priority')}:** {r.get('priority', 0):.0f} / 100 · {t(r.get('decision') or '')}")
            when = r.get("scheduled_for")
            st.markdown(f"**{'موعد الصيانة' if ar else 'Repair date'}:** " +
                        (when if when else ("لم يُحدد بعد" if ar else "not set yet")))
            # progress bar across the workflow
            steps = ["new", "review", "scheduled", "in_progress", "repaired"]
            pos = steps.index(status) + 1 if status in steps else 1
            st.progress(pos / len(steps), text=" ← ".join(status_label(s) for s in steps)
                        if ar else " → ".join(status_label(s) for s in steps))
            with st.expander("السجل" if ar else "Timeline"):
                for h in r.get("history", []):
                    if h.get("event", "").startswith("note"):
                        continue  # internal notes stay internal
                    st.markdown(f"- `{h['time']}` · {event_text(h.get('event', ''))}")
