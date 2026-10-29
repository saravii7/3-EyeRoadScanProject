"""Municipality: system health. Which real components are loaded and how fast they run."""
import hashlib
import json
import platform

import streamlit as st

from i18n import lang, t
from reports import REPORTS_DIR
from utils import MODEL_CONF, MODELS_DIR, available_models, model_info

ar = lang() == "ar"
st.title("🩺 " + t("p_health"))
st.caption("حالة المكوّنات الحقيقية المستخدمة في التطبيق." if ar else
           "Status of the real components used by the app.")


@st.cache_data(show_spinner=False)
def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def row(name, ok, detail):
    icon = "🟢" if ok else "🔴"
    st.markdown(f"{icon} **{name}** · {detail}")


names = available_models()
current = st.session_state.get("model_name") or (names[0] if names else None)
if current:
    info = model_info(current)
    conf = MODEL_CONF.get(current)
    digest = sha256(str(MODELS_DIR / current))
    row("YOLO" + (" (نموذج الفريق)" if ar and info["ours"] else " (team model)" if info["ours"] else ""),
        True, f"{info['label']} · conf {conf if conf is not None else 0.25} · "
              f"SHA-256 {digest[:12]}…")
    if current.startswith("run17") and digest != \
            "25b412ff18c05e2607f4bc61b872f39826e8d53ffdc7647654c1f419e355d15f":
        st.error("SHA-256 does not match the run-17 release (25b412ff…d15f).")
else:
    row("YOLO", False, "no weights in models/")

try:
    import faiss  # noqa: F401
    meta = REPORTS_DIR / "meta.json"
    n_vec = len(json.loads(meta.read_text())) if meta.exists() else 0
    row("FAISS", True, f"{n_vec} " + ("بصمة محفوظة" if ar else "stored fingerprints"))
except Exception as e:  # noqa: BLE001
    row("FAISS", False, str(e))

try:
    import transformers
    row("DINOv2-small", True, f"transformers {transformers.__version__} · "
                              + ("يُحمَّل عند أول مقارنة" if ar else "loads on first comparison"))
except Exception as e:  # noqa: BLE001
    row("DINOv2-small", False, str(e))

try:
    from privacy import blur_available
    import cv2
    row("Face / plate blur", blur_available(), f"OpenCV {cv2.__version__}" +
        ("" if blur_available() else " · pip install \"opencv-python<5\""))
except Exception as e:  # noqa: BLE001
    row("Face / plate blur", False, str(e))

try:
    from location import SAUDI  # noqa: F401
    row("Saudi border check", True, "Natural Earth 1:10m")
except Exception as e:  # noqa: BLE001
    row("Saudi border check", False, str(e))

try:
    from notify import configured, twilio_installed
    row("WhatsApp (Twilio Sandbox)", configured(),
        "متصل" if configured() else "twilio غير مثبتة" if not twilio_installed()
        else "ملف .env ناقص")
except Exception as e:  # noqa: BLE001
    row("WhatsApp (Twilio Sandbox)", False, str(e))

st.caption(f"Python {platform.python_version()} · {platform.system()}")
st.caption("العنوان المقروء يحتاج إنترنت (OpenStreetMap)؛ بدونه تظهر الإحداثيات فقط." if ar else
           "Readable addresses need internet (OpenStreetMap); offline, coordinates are shown.")
