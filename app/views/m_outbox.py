"""Municipality: WhatsApp notifications sent to citizens (numbers always masked)."""
import pandas as pd
import streamlit as st

from i18n import lang, t
from notify import configured, load_outbox, normalise_phone, send_text
from utils import metric_card

ar = lang() == "ar"
st.title("📲 " + t("p_outbox"))
st.caption("رسائل واتساب التلقائية للمواطنين: عند استلام البلاغ، والجدولة، وبدء التنفيذ، والإصلاح."
           if ar else "Automatic WhatsApp messages to citizens: on receipt, scheduling, start "
           "of work and repair.")

if configured():
    st.success(("🟢 واتساب متصل (Meta WhatsApp Cloud API · رقم تجريبي). الرسائل تُرسل فعلياً." if ar
                else "🟢 WhatsApp connected (Meta WhatsApp Cloud API, test number). "
                "Messages are really sent."))
else:
    st.warning(("🔴 واتساب غير مُعد بعد: أضف WHATSAPP_TOKEN و WHATSAPP_PHONE_NUMBER_ID في ملف "
                ".env بجانب Home.py. حتى ذلك الحين تُسجَّل الرسائل هنا فقط (not_sent)." if ar else
                "🔴 WhatsApp is not set up yet: add WHATSAPP_TOKEN and WHATSAPP_PHONE_NUMBER_ID "
                "to .env next to Home.py. Until then messages are only logged here."))

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
        sent, info = send_text(phone, "\u2066👁️ 3-Eye\u2069 | رسالة تجربة من نظام بلاغات الطرق.")
        (st.success if sent else st.error)(info if not sent else ("تم الإرسال ✅" if ar else "Sent ✅"))
    st.caption(("قبل العرض: أضف أرقام الفريق (حتى 5) في لوحة Meta، وليرسل كل جوال أي رسالة "
                "للرقم التجريبي خلال آخر 24 ساعة، وانسخ مفتاح دخول جديداً إلى .env في يوم العرض."
                if ar else "Before the demo: add the team's numbers (up to 5) in the Meta app, "
                "send any message from each phone to the test number within 24 h, and paste a "
                "fresh access token into .env on demo day."))
