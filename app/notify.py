"""WhatsApp notifications for citizens (Twilio WhatsApp Sandbox, for the demo).

Secrets live ONLY in a local `.env` file next to Home.py (never on GitHub):
    TWILIO_ACCOUNT_SID=AC...
    TWILIO_AUTH_TOKEN=...
    TWILIO_WHATSAPP_FROM=whatsapp:+14155238886

Sandbox limits (Twilio): each phone must first send "join <code>" to the sandbox number;
free text is allowed only within 24 h of that phone's last message; the sender name is
"Twilio Sandbox". A real service would register its own WhatsApp sender.

If Twilio is not configured, the app still works: messages are written to the outbox
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

# Read the secrets file by hand (works even if Notepad saved it as ".env.txt").
for name in (".env", ".env.txt"):
    env = APP_DIR / name
    if env.exists():
        for line in env.read_text(encoding="utf-8-sig").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        break

SID = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886").strip()
SANDBOX_NUMBER = "+1 415 523 8886"

ERRORS = {  # Twilio error code -> short Arabic explanation
    63016: "خارج نافذة الـ24 ساعة: يجب أن يرسل صاحب الرقم أي رسالة للساندبوكس أولاً.",
    63015: "الرقم غير منضم للساندبوكس: يرسل join <الكود> إلى " + SANDBOX_NUMBER,
    63007: "رقم المرسل غير صحيح في ملف .env.",
    21211: "رقم الجوال غير صحيح.",
    20003: "بيانات Twilio غير صحيحة (SID أو Token).",
}


def twilio_installed():
    try:
        import twilio  # noqa: F401
        return True
    except ImportError:
        return False


def configured():
    return bool(SID.startswith("AC") and TOKEN and twilio_installed())


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
    head = "👁️ 3-Eye | "
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


CONTENT_FILE = REPORTS_DIR / "content_sid.json"


def _text_template():
    """A plain-text Content template '{{1}}' (created once, then reused). Lets the app send
    its own wording when the account requires a ContentSid. Within the 24-hour window a
    plain text template needs no WhatsApp approval."""
    if CONTENT_FILE.exists():
        sid = json.loads(CONTENT_FILE.read_text(encoding="utf-8")).get("sid")
        if sid:
            return sid
    import requests
    auth = (SID, TOKEN)
    url = "https://content.twilio.com/v1/Content"
    sid = None
    page = requests.get(url, auth=auth, params={"PageSize": 200}, timeout=20).json()
    for c in page.get("contents", []):
        if c.get("friendly_name") == "roadscan_text":
            sid = c["sid"]
    if not sid:
        r = requests.post(url, auth=auth, timeout=20, json={
            "friendly_name": "roadscan_text", "language": "ar",
            "variables": {"1": "3-Eye"},
            "types": {"twilio/text": {"body": "{{1}}"}}})
        r.raise_for_status()
        sid = r.json()["sid"]
    CONTENT_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONTENT_FILE.write_text(json.dumps({"sid": sid}), encoding="utf-8")
    return sid


def send_text(phone, body, rid=None, kind="test"):
    """Send one WhatsApp message. Never raises: returns (ok, info) and logs to the outbox."""
    entry = {"time": time.strftime("%Y-%m-%d %H:%M:%S"), "report": rid, "kind": kind,
             "to": mask(phone), "body": body}
    if not configured():
        entry.update(status="not_sent", info="Twilio غير مُعد (.env أو مكتبة twilio)")
        _log(entry)
        return False, entry["info"]
    try:
        from twilio.rest import Client
        client = Client(SID, TOKEN)
        try:
            msg = client.messages.create(from_=FROM, to=f"whatsapp:{phone}", body=body)
        except Exception as e:  # some new accounts only accept Content templates
            if "contentsid" not in str(getattr(e, "msg", e)).lower():
                raise
            msg = client.messages.create(from_=FROM, to=f"whatsapp:{phone}",
                                         content_sid=_text_template(),
                                         content_variables=json.dumps({"1": body},
                                                                      ensure_ascii=False))
        entry.update(status=msg.status or "queued", info=msg.sid)
        _log(entry)
        return True, msg.sid
    except Exception as e:  # network, auth, sandbox rules ...
        code = getattr(e, "code", None)
        entry.update(status="failed", code=code,
                     info=ERRORS.get(code, str(getattr(e, "msg", e))[:200]))
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
            time.sleep(1)  # sandbox: about one message per second at most
        results.append(send_text(p, body, rid, kind))
    return results


def on_event(rid, event):
    """Called by reports.update_report: status and schedule changes notify subscribers."""
    kind, _, val = (event or "").partition(":")
    if kind == "status" and val in ("review", "scheduled", "in_progress", "repaired", "rejected"):
        notify(rid, val)
    elif kind == "scheduled":
        notify(rid, "scheduled")
