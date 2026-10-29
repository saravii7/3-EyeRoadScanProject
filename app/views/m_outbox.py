"""Municipality: WhatsApp notifications sent to citizens (numbers always masked)."""
import pandas as pd
import streamlit as st

from i18n import lang, t
from notify import (SANDBOX_NUMBER, configured, load_outbox, normalise_phone, send_text,
                    twilio_installed)
from utils import metric_card

ar = lang() == "ar"
st.title("📲 " + t("p_outbox"))
st.caption("رسائل واتساب التلقائية للمواطنين: عند استلام البلاغ، والجدولة، وبدء التنفيذ، والإصلاح."
           if ar else "Automatic WhatsApp messages to citizens: on receipt, scheduling, start "
           "of work and repair.")

if configured():
    st.success(("🟢 Twilio متصل (WhatsApp Sandbox). الرسائل تُرسل فعلياً." if ar else
                "🟢 Twilio connected (WhatsApp Sandbox). Messages are really sent."))
elif not twilio_installed():
    st.warning(("🔴 مكتبة twilio غير مثبتة على هذا الجهاز." if ar else
                "🔴 The twilio library is not installed."))
    if st.button("⬇️ ثبّت مكتبة twilio الآن" if ar else "⬇️ Install twilio now", type="primary"):
        import importlib
        import subprocess
        import sys
        with st.spinner("جارٍ التثبيت... (دقيقة تقريباً)" if ar else "Installing..."):
            res = subprocess.run([sys.executable, "-m", "pip", "install", "twilio"],
                                 capture_output=True, text=True)
        importlib.invalidate_caches()
        if res.returncode == 0:
            st.rerun()
        st.error(("فشل التثبيت:" if ar else "Install failed:") + "\n\n" +
                 (res.stderr or res.stdout)[-600:])
else:
    st.warning(("🔴 ملف .env غير موجود أو ناقص بجانب Home.py. الرسائل تُسجَّل هنا فقط "
                "(not_sent)." if ar else
                "🔴 .env is missing or incomplete next to Home.py. Messages are only logged."))

box = load_outbox()
ok = sum(e.get("status") not in ("failed", "not_sent") for e in box)
c1, c2, c3 = st.columns(3)
with c1:
    metric_card("الرسائل" if ar else "Messages", len(box))
with c2:
    metric_card("أُرسلت" if ar else "Sent", ok, "#43A878")
with c3:
    metric_card("لم تُرسل" if ar else "Not sent", len(box) - ok, "#DE6D64")

if box:
    df = pd.DataFrame(box[::-1])
    df["report"] = df["report"].apply(lambda r: f"RS-{int(r):04d}" if pd.notna(r) else "—")
    cols = [c for c in ["time", "report", "kind", "to", "status", "info", "body"] if c in df]
    st.dataframe(df[cols], hide_index=True, width="stretch")
else:
    st.info("لا توجد رسائل بعد. فعّل خيار واتساب عند رفع بلاغ." if ar else
            "No messages yet. Tick the WhatsApp option when reporting.")

with st.expander("🧪 رسالة تجربة" if ar else "🧪 Test message"):
    raw = st.text_input("رقم الجوال" if ar else "Mobile", placeholder="05XXXXXXXX")
    phone = normalise_phone(raw)
    if st.button("إرسال" if ar else "Send", disabled=not phone):
        sent, info = send_text(phone, "👁️ 3-Eye | رسالة تجربة من نظام بلاغات الطرق.")
        (st.success if sent else st.error)(info if not sent else ("تم الإرسال ✅" if ar else "Sent ✅"))
    st.caption((f"قبل العرض: كل جوال يرسل join <الكود> إلى {SANDBOX_NUMBER} مرة واحدة، ثم أي "
                "رسالة خلال آخر 24 ساعة. اسم المرسل يظهر «Twilio Sandbox» لأنها بيئة تجريبية." if ar
                else f"Before the demo: each phone sends join <code> to {SANDBOX_NUMBER} once, "
                "then any message within the last 24 h. Sender shows 'Twilio Sandbox' (demo)."))
