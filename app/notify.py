"""WhatsApp notifications for citizens through Meta's official WhatsApp Cloud API.

For the demo we use Meta's free TEST phone number. Secrets live ONLY in a local `.env`
file next to Home.py (never on GitHub), or in Streamlit Cloud "Secrets":
    WHATSAPP_TOKEN=...              (access token from the Meta app's WhatsApp > API Setup)
    WHATSAPP_PHONE_NUMBER_ID=...    (the test number's "Phone number ID")

Test-number limits (Meta): messages reach only the recipient numbers added in the app
(up to 5); free text is allowed only within 24 h of that phone's last message to the test
number; the temporary token expires after about 24 h. A real municipality would register
its own verified WhatsApp number.

If WhatsApp is not configured, the app still works: messages are written to the outbox
with status "not_sent" so the municipality can see what would have been sent.
"""
import json
import os
import re
import time
from pathlib import Path

from reports import REPORTS_DIR, _write_extra, load_extra

APP_DIR = Path(__file__).resolve().parent
OUTBOX = REPORTS_DIR / "outbox.json"
API_VERSION = "v21.0"

# Read the secrets file by hand (works even if Notepad saved it as ".env.txt").
for name in (".env", ".env.txt"):
    env = APP_DIR / name
    if env.exists():
        for line in env.read_text(encoding="utf-8-sig").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        break


def _secret(key):
    v = os.getenv(key, "").strip()
    if not v:
        try:  # Streamlit Cloud: Settings > Secrets
            import streamlit as st
            v = str(st.secrets.get(key, "")).strip()
        except Exception:
            v = ""
    return v


TOKEN = _secret("WHATSAPP_TOKEN")
PHONE_ID = _secret("WHATSAPP_PHONE_NUMBER_ID")

ERRORS = {  # Meta error code -> short Arabic explanation
    131047: "مرت أكثر من 24 ساعة: يرسل صاحب الرقم أي رسالة للرقم التجريبي أولاً.",
    131030: "الرقم غير مضاف في قائمة المستلمين (لوحة Meta ← WhatsApp ← API Setup ← To).",
    190: "مفتاح الدخول (Token) منتهي أو غير صحيح: انسخ مفتاحاً جديداً إلى ملف .env.",
    100: "رقم الهاتف التجريبي (Phone number ID) غير صحيح في ملف .env.",
    131026: "الرسالة لم تصل: تأكد أن الرقم عليه واتساب.",
}


def configured():
    return bool(TOKEN and PHONE_ID)


def normalise_phone(text):
    """Saudi mobile in any common form -> +9665XXXXXXXX, or None if invalid."""
    digits = re.sub(r"\D", "", text or "")
    if digits.startswith("00"):
        digits = digits[2:]
    if digits.startswith("05") and len(digits) == 10:
        digits = "966" + digits[1:]
    elif digits.startswith("5") and len(digits) == 9:
        digits = "966" + digits
    if re.fullmatch(r"9665\d{8}", digits):
        return "+" + digits
    return None


def mask(phone):
    return phone[:4] + "•" * (len(phone) - 7) + phone[-3:] if phone else "—"


def _ref(rid):
    return f"RS-{int(rid):04d}"


def message_text(rid, kind, report=None):
    r = report or load_extra().get(int(rid), {})
    head = "\u2066👁️ 3-Eye\u2069 | "  # isolate keeps "3-Eye" in order in RTL
    ref = _ref(rid)
    names = {"D00": "شق طولي", "D10": "شق عرضي", "D20": "تشقق تمساحي", "D40": "حفرة"}
    damage = "، ".join(names.get(c, c) for c in r.get("classes", [])) or "ضرر في الطريق"
    decision = {"Urgent": "عاجل", "Schedule": "يُجدول", "Monitor": "مراقبة"}.get(
        r.get("decision"), "")
    place = f" في {r['address']}" if r.get("address") else ""
    if kind == "received":
        return (f"{head}تم استلام بلاغك رقم {ref} ({damage}){place}. "
                f"تقييم الأولوية المبدئي: {decision}. سنرسل لك أي تحديث على حالته.")
    if kind == "linked":
        return (f"{head}شكراً لك! هذا الضرر مبلّغ عنه مسبقاً برقم {ref}، وأضفنا بلاغك إليه "
                "لرفع أهميته. سنرسل لك أي تحديث على حالته.")
    if kind == "review":
        return f"{head}بلاغك رقم {ref} قيد المراجعة من البلدية."
    if kind == "scheduled":
        when = f" بتاريخ {r['scheduled_for']}" if r.get("scheduled_for") else ""
        return f"{head}تمت جدولة صيانة البلاغ رقم {ref}{when}."
    if kind == "in_progress":
        return f"{head}بدأ فريق الصيانة العمل على البلاغ رقم {ref}."
    if kind == "repaired":
        return f"{head}✅ تم إصلاح الضرر في البلاغ رقم {ref}. شكراً لمساهمتك في سلامة الطرق!"
    if kind == "rejected":
        return f"{head}تمت مراجعة البلاغ رقم {ref} ولم يُعتمد للصيانة (مكرر أو غير واضح)."
    return f"{head}تحديث على البلاغ رقم {ref}."


def load_outbox():
    if OUTBOX.exists():
        try:
            return json.loads(OUTBOX.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return []
    return []


def _log(entry):
    box = load_outbox()
    box.append(entry)
    OUTBOX.parent.mkdir(parents=True, exist_ok=True)
    OUTBOX.write_text(json.dumps(box, ensure_ascii=False, indent=1), encoding="utf-8")


def send_text(phone, body, rid=None, kind="test"):
    """Send one WhatsApp message. Never raises: returns (ok, info) and logs to the outbox."""
    entry = {"time": time.strftime("%Y-%m-%d %H:%M:%S"), "report": rid, "kind": kind,
             "to": mask(phone), "body": body}
    if not configured():
        entry.update(status="not_sent", info="واتساب غير مُعد (ملف .env)")
        _log(entry)
        return False, entry["info"]
    try:
        import requests
        r = requests.post(
            f"https://graph.facebook.com/{API_VERSION}/{PHONE_ID}/messages",
            headers={"Authorization": f"Bearer {TOKEN}"}, timeout=20,
            json={"messaging_product": "whatsapp", "to": phone.lstrip("+"), "type": "text",
                  "text": {"preview_url": False, "body": body}})
        data = r.json()
        if r.ok and data.get("messages"):
            mid = data["messages"][0].get("id", "")
            entry.update(status="sent", info=mid)
            _log(entry)
            return True, mid
        err = data.get("error", {})
        code = err.get("code")
        entry.update(status="failed", code=code,
                     info=ERRORS.get(code, str(err.get("message", r.text))[:200]))
    except Exception as e:  # network problems
        entry.update(status="failed", info=str(e)[:200])
    _log(entry)
    return False, entry["info"]


def subscribe(rid, phone):
    """Remember that this phone wants updates on report rid (stored only on this computer)."""
    extra = load_extra()
    rid = int(rid)
    if rid in extra and phone:
        subs = extra[rid].setdefault("subscribers", [])
        if phone not in subs:
            subs.append(phone)
            _write_extra(extra)


def notify(rid, kind, only=None):
    """Send the message for `kind` to every subscriber of report rid (or just `only`)."""
    r = load_extra().get(int(rid))
    if not r:
        return []
    phones = [only] if only else r.get("subscribers", [])
    body = message_text(rid, kind, r)
    now = time.time()
    recent = {(e.get("report"), e.get("body")) for e in load_outbox()[-50:]
              if now - time.mktime(time.strptime(e["time"], "%Y-%m-%d %H:%M:%S")) < 120}
    if not only and (int(rid), body) in recent:
        return []  # same message already sent moments ago (status + date saved together)
    results = []
    for i, p in enumerate(phones):
        if i:
            time.sleep(1)  # be gentle with the API: one message per second
        results.append(send_text(p, body, rid, kind))
    return results


def on_event(rid, event):
    """Called by reports.update_report: status and schedule changes notify subscribers."""
    kind, _, val = (event or "").partition(":")
    if kind == "status" and val in ("review", "scheduled", "in_progress", "repaired", "rejected"):
        notify(rid, val)
    elif kind == "scheduled":
        notify(rid, "scheduled")
