"""Arabic-first text for the citizen and municipality pages, with an English switch."""
import streamlit as st

TEXT = {
    # app shell
    "app_tag": ("ذكاء الطرق للبلديات", "Road intelligence for municipalities"),
    "language": ("English", "العربية"),
    "sec_citizen": ("المواطن", "Citizen"),
    "sec_city": ("البلدية", "Municipality"),
    "sec_tech": ("التقني (للجنة)", "Technical (for the panel)"),
    # pages
    "p_home": ("الرئيسية", "Home"),
    "p_report": ("رفع بلاغ", "Report damage"),
    "p_mine": ("بلاغاتي", "My reports"),
    "p_overview": ("نظرة عامة", "Overview"),
    "p_queue": ("قائمة البلاغات", "Report queue"),
    "p_detail": ("تفاصيل بلاغ", "Report details"),
    "p_map": ("خريطة الأضرار", "Damage map"),
    "p_maint": ("الصيانة", "Maintenance"),
    "p_analytics": ("التحليلات", "Analytics"),
    "p_health": ("صحة النظام", "System health"),
    "p_outbox": ("إشعارات واتساب", "WhatsApp notifications"),
    # statuses
    "st_new": ("جديد", "New"),
    "st_review": ("قيد المراجعة", "Under review"),
    "st_scheduled": ("مجدول للصيانة", "Scheduled"),
    "st_in_progress": ("قيد التنفيذ", "In progress"),
    "st_repaired": ("تم الإصلاح", "Repaired"),
    "st_rejected": ("مرفوض / مكرر", "Rejected / duplicate"),
    # decisions
    "Urgent": ("عاجل", "Urgent"),
    "Schedule": ("يُجدول", "Schedule"),
    "Monitor": ("مراقبة", "Monitor"),
    # classes
    "D00": ("شق طولي", "Longitudinal crack"),
    "D10": ("شق عرضي", "Transverse crack"),
    "D20": ("تشقق تمساحي", "Alligator crack"),
    "D40": ("حفرة", "Pothole"),
    # common words
    "priority": ("الأولوية", "Priority"),
    "status": ("الحالة", "Status"),
    "team": ("الفريق", "Team"),
    "address": ("الموقع", "Location"),
    "classes": ("نوع الضرر", "Damage type"),
    "added": ("تاريخ البلاغ", "Reported"),
    "reported_times": ("عدد المبلّغين", "Times reported"),
    "ref": ("رقم البلاغ", "Reference"),
    "decision": ("القرار", "Decision"),
    "no_reports": ("لا توجد بلاغات بعد.", "No reports yet."),
    "ai_note": ("الذكاء الاصطناعي يقترح الأولوية، والقرار يبقى للبلدية.",
                "AI suggests the priority; the municipality makes the decision."),
}

STATUSES = ["new", "review", "scheduled", "in_progress", "repaired", "rejected"]
OPEN_STATUSES = ["new", "review", "scheduled", "in_progress"]
STATUS_COLOR = {"new": "#19B8A6", "review": "#8E7BD1", "scheduled": "#E7A83F",
                "in_progress": "#3B82F6", "repaired": "#43A878", "rejected": "#758199"}
TEAMS = ["فريق الصيانة 1 · أبها", "فريق الصيانة 2 · خميس مشيط", "فريق الطوارئ"]


def lang():
    return st.session_state.get("lang", "ar")


def t(key):
    pair = TEXT.get(key)
    if pair is None:
        return key
    return pair[0] if lang() == "ar" else pair[1]


def status_label(code):
    return t(f"st_{code}")


def ref(report_id):
    return f"RS-{int(report_id):04d}"


def language_switch():
    """Sidebar button that flips Arabic / English."""
    if st.sidebar.button(f"🌐 {t('language')}", width="stretch"):
        st.session_state["lang"] = "en" if lang() == "ar" else "ar"
        st.rerun()


def event_text(ev):
    """History event code -> readable text."""
    ar = lang() == "ar"
    if ev == "created":
        return "تم استلام البلاغ" if ar else "Report received"
    if ev == "repeat_report":
        return "بلّغ مواطن آخر عن نفس الضرر" if ar else "Another citizen reported the same damage"
    kind, _, val = ev.partition(":")
    if kind == "status":
        return ("تغيّرت الحالة إلى: " if ar else "Status changed to: ") + status_label(val)
    if kind == "team":
        return ("أُسند إلى: " if ar else "Assigned to: ") + val
    if kind == "scheduled":
        return ("موعد الصيانة: " if ar else "Repair date: ") + val
    if kind == "note":
        return "أُضيفت ملاحظة داخلية" if ar else "Internal note added"
    return ev
