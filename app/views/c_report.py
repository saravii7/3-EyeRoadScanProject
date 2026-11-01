"""Citizen: report road damage. Real team model, location, duplicate check, then submit."""
import streamlit as st

from i18n import lang, ref, t
from location import location_section
from pipeline import analyse, crops, open_matches, save_new
from reports import crop_path, link_duplicate, thumb_path
from utils import PHOTO_TYPES, chip, team_model

ar = lang() == "ar"
st.title("📸 " + t("p_report"))
st.caption("صوّر الضرر من مكان آمن. نموذج فريق \u20663-Eye\u2069 يحلل الصورة مباشرة." if ar else
           "Photograph the damage from a safe place. The 3-Eye team model analyses it directly.")

st.info(("📷 **نصيحة لنتيجة أدق:** نرجو منك تصوير الضرر عن قُرب، وأن يكون في منتصف الصورة "
         "وظاهراً بالكامل، مع إضاءة واضحة قدر الإمكان. شاكرين لك حرصك وتعاونك 🌷") if ar else
        ("📷 **For a more accurate result:** please photograph the damage up close, centred and "
         "fully in frame, in good light if possible. Thank you for your help 🌷"))
steps_box = st.empty()  # usage steps: shown until the citizen chooses a photo
uploaded = st.file_uploader("صورة الضرر" if ar else "Damage photo", type=PHOTO_TYPES)
if not uploaded:
    steps = ([("📷", "صوّر الضرر", "من مكان آمن، عن قُرب وفي منتصف الصورة، والموقع مفعّل في الكاميرا."),
              ("⬆️", "ارفع الصورة", "اضغط زر «Upload» تحت واختر الصورة. يحلّلها نموذجنا خلال ثوانٍ."),
              ("📍", "أكّد الموقع", "يُقرأ من الصورة أو من جهازك، أو اختره على الخريطة داخل المملكة."),
              ("✅", "أرسل وتابع", "وافق وأرسل، وتابع حالة بلاغك برقمه من صفحة «بلاغاتي».")]
             if ar else
             [("📷", "Take the photo", "From a safe place, close up and centred, with location on."),
              ("⬆️", "Upload it", "Press “Upload” below. Our model analyses it in seconds."),
              ("📍", "Confirm location", "Read from the photo or your device, or pick it on the map."),
              ("✅", "Send and track", "Agree and send, then follow your report in “My reports”.")])
    cards = "".join(
        f'<div style="flex:1;min-width:180px;background:#0E3440;border:1px solid #1B4A57;'
        f'border-radius:16px;padding:1rem 1.1rem">'
        f'<div style="display:flex;align-items:center;gap:.6rem;margin-bottom:.4rem">'
        f'<span style="background:#1EC7B6;color:#082B36;font-weight:700;border-radius:50%;'
        f'width:30px;height:30px;display:inline-flex;align-items:center;justify-content:center">'
        f'{i}</span><span style="font-size:1.4rem">{icon}</span>'
        f'<b style="color:#F4F6F5">{title}</b></div>'
        f'<div style="color:#A6BBC0;font-size:.92rem">{text}</div></div>'
        for i, (icon, title, text) in enumerate(steps, 1))
    steps_box.markdown(
        f'<div style="margin:.4rem 0 1rem"><div style="color:#F4F6F5;font-weight:700;'
        f'font-size:1.15rem;margin-bottom:.6rem">{"خطوات رفع البلاغ" if ar else "How to report"}'
        f'</div><div style="display:flex;gap:.8rem;flex-wrap:wrap">{cards}</div></div>',
        unsafe_allow_html=True)
    st.stop()

model, conf = team_model()  # loaded only once a photo is chosen, so the page opens fast
if model is None:
    st.stop()

with st.spinner("جارٍ تحليل الصورة..." if ar else "Analysing the photo..."):
    A = analyse(uploaded, model, conf)
if A is None:
    st.stop()

key = f"{uploaded.name}-{uploaded.size}"
done = st.session_state.setdefault("citizen_done", {})

left, right = st.columns([3, 2])
left.image(A["annotated"], width="stretch",
           caption="نتيجة التحليل (الوجوه واللوحات مغبّشة)" if ar else "Result (faces and plates blurred)")
with right:
    st.markdown(f"### {t('priority')}: **{A['score']:.0f} / 100**")
    st.markdown(chip(t(A["label"]), A["color"]), unsafe_allow_html=True)
    if A["dets"]:
        st.markdown("**" + ("الأضرار المكتشفة" if ar else "Damage found") + "**")
        for d in sorted(A["dets"], key=lambda d: -d["conf"]):
            st.markdown(f"- {d['cls']} · {t(d['cls'])} · "
                        f"{'الثقة' if ar else 'confidence'} {d['conf']:.2f}")
    else:
        st.info("لم يكتشف النموذج ضرراً واضحاً. يمكنك إرسال البلاغ للمراجعة اليدوية." if ar else
                "The model found no clear damage. You can still send it for manual review.")

st.divider()
location = location_section(uploaded)
lat, lon = location if location else (None, None)

if key in done:
    kind, rid = done[key]
    if kind == "added":
        st.success((f"تم استلام بلاغك برقم **{ref(rid)}**. تابعه من صفحة «بلاغاتي»." if ar else
                    f"Report received: **{ref(rid)}**. Track it in My reports."))
    else:
        st.success((f"شكراً! هذا الضرر مبلّغ عنه مسبقاً برقم **{ref(rid)}**، وأضفنا بلاغك إليه "
                    "لرفع أهميته." if ar else
                    f"Thanks! This damage is already reported as **{ref(rid)}**; your report was "
                    "added to it."))
    st.page_link("views/c_mine.py", label=t("p_mine"), icon="🧾")
    st.stop()

matches, _ = open_matches(A["image"], A["dets"], lat, lon)
desc = st.text_area("وصف إضافي (اختياري)" if ar else "Extra details (optional)",
                    placeholder="مثال: الحفرة في المسار الأيمن قرب الإشارة" if ar else
                    "e.g. pothole in the right lane near the signal")
consent = st.checkbox("أوافق على إرسال الصورة (بعد التغبيش) والموقع إلى البلدية." if ar else
                      "I agree to send the (blurred) photo and location to the municipality.")

blocked = not consent


def _submit():
    rid = save_new(uploaded, A, location, "citizen", desc)
    done[key] = ("added", rid)
    st.session_state.setdefault("my_reports", []).append(rid)


def _link(rid):
    link_duplicate(rid)
    done[key] = ("linked", rid)
    st.session_state.setdefault("my_reports", []).append(rid)


if matches:
    m = matches[0]
    where = (f"، على بعد {m['distance_m']:.0f} م" if ar else f", {m['distance_m']:.0f} m away") \
        if m["distance_m"] is not None else ""
    st.warning((f"يبدو أن هذا الضرر مبلّغ عنه مسبقاً: **{ref(m['id'])}** "
                f"(تشابه {m['similarity']:.2f}{where})." if ar else
                f"This damage may already be reported: **{ref(m['id'])}** "
                f"(similarity {m['similarity']:.2f}{where})."))
    e1, e2 = st.columns(2)
    new_crop = next((c for cls, c in crops(A["shown"], A["dets"])
                     if cls == m["cls"]), None)
    if new_crop is not None:
        e1.image(new_crop, caption="صورتك" if ar else "Your photo", width="stretch")
    old = crop_path(m["id"], m["cls"]) or thumb_path(m["id"])
    if old:
        e2.image(str(old), caption=ref(m["id"]), width="stretch")
    b1, b2 = st.columns(2)
    b1.button("نفس الضرر: أضف بلاغي إليه" if ar else "Same damage: add my report to it",
              on_click=_link, args=(m["id"],), type="primary", disabled=blocked)
    b2.button("ضرر مختلف: أرسل بلاغاً جديداً" if ar else "Different damage: send a new report",
              on_click=_submit, disabled=blocked)
else:
    st.button("إرسال البلاغ" if ar else "Send report", on_click=_submit, type="primary",
              disabled=blocked)
if not consent:
    st.caption("فعّل الموافقة لإرسال البلاغ." if ar else "Tick the consent box to send.")
st.caption(t("ai_note"))
