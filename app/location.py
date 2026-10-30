"""Where was the photo taken? Photo GPS first, then the device, then a map click.
Only locations inside Saudi Arabia are accepted (border: Natural Earth 1:10m, public domain).
Coordinates are turned into a readable place name with OpenStreetMap (Nominatim)."""
import json
import math
import os

import folium
import requests
import streamlit as st
from PIL import Image
from shapely.geometry import Point, shape
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation

ABHA = (18.2164, 42.5053)  # default map centre for the demo

_here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_here, "saudi.geojson"), encoding="utf-8") as f:
    SAUDI = shape(json.load(f)["features"][0]["geometry"])


def in_saudi(lat, lon):
    return SAUDI.contains(Point(lon, lat))  # shapely order: lon first, then lat


try:  # lets Image.open read GPS from iPhone HEIC photos
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass


def read_gps(file):
    """(lat, lon) from the photo's EXIF, or None."""
    file.seek(0)  # the page already read the file once
    gps = Image.open(file).getexif().get_ifd(34853)
    file.seek(0)
    if not gps or 2 not in gps or 4 not in gps:
        return None

    def dec(dms, ref):
        d, m, s = [float(x) for x in dms]
        v = d + m / 60 + s / 3600
        return -v if ref in ("S", "W") else v

    return dec(gps[2], gps.get(1, "N")), dec(gps[4], gps.get(3, "E"))


HEADERS = {"User-Agent": "RoadScan-3Eye-capstone/1.0"}
DISTRICT_KEYS = ("neighbourhood", "suburb", "quarter", "city_district", "district",
                 "residential", "hamlet")


def _distance_m(a, b):
    lat1, lon1, lat2, lon2 = map(math.radians, (*a, *b))
    h = (math.sin((lat2 - lat1) / 2) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2)
    return 6_371_000 * 2 * math.asin(math.sqrt(h))


def _nominatim(lat, lon, zoom):
    r = requests.get(
        "https://nominatim.openstreetmap.org/reverse",
        params={"lat": round(lat, 6), "lon": round(lon, 6), "format": "jsonv2",
                "zoom": zoom, "addressdetails": 1, "accept-language": "ar"},
        headers=HEADERS, timeout=5)
    r.raise_for_status()
    return r.json().get("address", {})


def _nearest_district(lat, lon, radius_m=3000):
    """Closest named district (place=neighbourhood/suburb/quarter) around the point."""
    q = (f'[out:json][timeout:8];'
         f'nwr(around:{radius_m},{lat},{lon})[place~"^(neighbourhood|suburb|quarter)$"][name];'
         f'out center tags;')
    r = requests.post("https://overpass-api.de/api/interpreter", data={"data": q},
                      headers=HEADERS, timeout=10)
    r.raise_for_status()
    best = None
    for e in r.json().get("elements", []):
        c = (e.get("lat"), e.get("lon")) if "lat" in e else (
            e.get("center", {}).get("lat"), e.get("center", {}).get("lon"))
        if c[0] is None:
            continue
        tags = e.get("tags", {})
        name = tags.get("name:ar") or tags.get("name")
        d = _distance_m((lat, lon), c)
        if name and (best is None or d < best[1]):
            best = (name, d)
    return best


@st.cache_data(show_spinner=False, ttl=24 * 3600)
def place_details(lat, lon):
    """{'road','district','district_near_m','city','region'} from OpenStreetMap, or None offline."""
    try:
        a = _nominatim(lat, lon, 18)
    except Exception:
        return None
    district = next((a[k] for k in DISTRICT_KEYS if a.get(k)), None)
    near_m = None
    if not district:
        try:
            a14 = _nominatim(lat, lon, 14)
            district = next((a14[k] for k in DISTRICT_KEYS if a14.get(k)), None)
        except Exception:
            pass
    if not district:
        try:
            found = _nearest_district(lat, lon)
            if found:
                district, near_m = found[0], round(found[1])
        except Exception:
            pass
    return {
        "road": a.get("road"),
        "district": district,
        "district_near_m": near_m,
        "city": a.get("city") or a.get("town") or a.get("village") or a.get("county"),
        "region": a.get("state"),
    }


def format_place(info):
    if not info:
        return None
    parts = []
    if info["road"]:
        parts.append(info["road"])
    if info["district"]:
        d = info["district"]
        if not d.startswith("حي"):
            d = "حي " + d
        if info["district_near_m"]:
            d = f"قرب {d} (حوالي {info['district_near_m']} م)"
        parts.append(d)
    for k in ("city", "region"):
        if info[k] and info[k] not in parts:
            parts.append(info[k])
    return "، ".join(parts) or None


def _ar():
    return st.session_state.get("lang", "ar") == "ar"


def get_location(file):
    """Returns (lat, lon, source) or None while the user is still choosing."""
    loc = read_gps(file)
    if loc:
        return loc[0], loc[1], "photo GPS"

    ar = _ar()
    st.info("الصورة بدون موقع. اختر طريقة تحديد الموقع:" if ar else
            "This photo has no GPS. Choose how to set the location:")
    device, pick = ("موقع جهازي", "أحدده على الخريطة") if ar else \
        ("Use my device location", "Pick on the map")
    choice = st.radio("مصدر الموقع" if ar else "Location source", [device, pick], horizontal=True)

    if choice == device:
        g = get_geolocation()
        if g and "coords" in g:
            return g["coords"]["latitude"], g["coords"]["longitude"], "device location"
        st.caption("اسمح للمتصفح بالوصول للموقع، أو حدده على الخريطة." if ar else
                   "Allow location access in the browser, or pick on the map.")
        return None

    m = _map(ABHA, 13)
    out = st_folium(m, height=350, key="pick_location")
    if out and out.get("last_clicked"):
        c = out["last_clicked"]
        return c["lat"], c["lng"], "picked on map"
    return None


def _map(center, zoom):
    """Folium map without the Leaflet/OSM credit on the map itself (credit is in the caption)."""
    m = folium.Map(location=center, zoom_start=zoom, attributionControl=False)
    m.get_root().header.add_child(folium.Element(
        "<style>.leaflet-control-attribution{display:none !important;}</style>"))
    return m


def show_place(lat, lon, source):
    """Readable place name + coordinates + a small map with a pin + a Google Maps link."""
    name = format_place(place_details(lat, lon))
    coords = f"{lat:.5f}° N، {lon:.5f}° E"
    if name:
        st.success(f"📍 **{name}**  \n{coords}")
    else:
        st.success(f"📍 {coords}  \n" + ("العنوان يحتاج اتصال بالإنترنت." if _ar() else
                                           "Address lookup needs internet."))
    gmaps = f"https://www.google.com/maps?q={lat:.6f},{lon:.6f}"
    src = {"photo GPS": "من الصورة", "device location": "من الجهاز",
           "picked on map": "محدد يدوياً"}.get(source, source) if _ar() else source
    st.caption(f"{'المصدر' if _ar() else 'Source'}: {src} · [Google Maps]({gmaps}) · "
               "Address and map data © OpenStreetMap")
    m = _map((lat, lon), 16)
    folium.Marker((lat, lon), tooltip=name or "Reported damage",
                  icon=folium.Icon(color="red", icon="exclamation-sign")).add_to(m)
    st_folium(m, height=280, key="show_location", returned_objects=[])


def location_section(file):
    """Draws the location block. Returns (lat, lon) inside Saudi Arabia, or None."""
    st.subheader("📍 " + ("الموقع" if _ar() else "Location"))
    loc = get_location(file)
    if loc is None:
        return None
    lat, lon, source = loc
    if not in_saudi(lat, lon):
        st.error("الموقع خارج المملكة العربية السعودية، ولا نستقبل إلا بلاغات داخل المملكة."
                 if _ar() else "This location is outside Saudi Arabia. "
                 "RoadScan only accepts reports inside the Kingdom.")
        return None
    show_place(lat, lon, source)
    return lat, lon
