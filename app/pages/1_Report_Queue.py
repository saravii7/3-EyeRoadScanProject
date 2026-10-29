"""Open-report queue: every saved report, most urgent first, on a map, exportable as CSV and
GeoJSON. Repeat reports of the same damage are counted instead of duplicated."""
import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from reports import as_data_uri, clear_all, load_queue, remove_reports, thumb_path, to_geojson
from utils import apply_style, metric_card

st.title("📋 Report Queue")
st.caption("Open reports sorted by repair priority (highest first). New reports are added from "
           "the Image Analysis page; repeat reports of the same damage are linked, not duplicated.")

q = load_queue()
if q.empty:
    st.info("No open reports yet. Analyse a photo and press **Add to open reports**.")
    st.page_link("pages/1_Image_Analysis.py", label="Go to Image Analysis", icon="🔍")
    st.stop()

last = st.session_state.get("last_added")
if last is not None and last in set(q["id"]):
    pos = int(q.loc[q["id"] == last, "position"].iloc[0])
    st.success(f"Latest report #{last} is at position {pos} of {len(q)}.")

c1, c2, c3, c4 = st.columns(4)
with c1:
    metric_card("Open reports", len(q))
with c2:
    metric_card("Urgent", int((q["decision"] == "Urgent").sum()), "#E74C3C")
with c3:
    metric_card("Schedule", int((q["decision"] == "Schedule").sum()), "#F1C40F")
with c4:
    metric_card("Repeat reports", int((q["times_reported"] - 1).clip(lower=0).sum()), "#4FC3F7")

# --- table with thumbnails ---
view = q.copy()
view["photo"] = [as_data_uri(thumb_path(i)) for i in view["id"]]
view["report"] = "#" + view["id"].astype(str)
view["address"] = view["address"].fillna("No address (no GPS or offline)")
cols = ["position", "photo", "report", "priority", "decision", "classes", "damages",
        "times_reported", "address", "added"]
st.dataframe(
    view[cols], hide_index=True, width="stretch", row_height=70,
    column_config={
        "position": st.column_config.NumberColumn("#", width="small"),
        "photo": st.column_config.ImageColumn("Photo (blurred)", width="small"),
        "priority": st.column_config.ProgressColumn("Priority", min_value=0, max_value=100,
                                                    format="%.1f"),
        "times_reported": st.column_config.NumberColumn("Reported", help="How many citizens "
                                                        "reported this damage"),
    })

# --- map ---
geo = q.dropna(subset=["lat", "lon"])
if not geo.empty:
    st.subheader("Map")
    colors = {"Urgent": "red", "Schedule": "orange", "Monitor": "green"}
    m = folium.Map(location=[geo["lat"].mean(), geo["lon"].mean()], zoom_start=14,
                   attributionControl=False)
    for _, r in geo.iterrows():
        folium.Marker(
            [r["lat"], r["lon"]],
            tooltip=f"#{r['id']} · {r['priority']:.0f} · {r['decision']}",
            popup=folium.Popup(f"<b>Report #{r['id']}</b> (queue {r['position']})<br>"
                               f"Priority {r['priority']:.1f} · {r['decision']}<br>"
                               f"{r['classes']}<br>{r['address'] or ''}", max_width=260),
            icon=folium.Icon(color=colors.get(r["decision"], "gray"), icon="exclamation-sign"),
        ).add_to(m)
    st_folium(m, height=420, key="queue_map", returned_objects=[])
    st.caption("Map data © OpenStreetMap contributors")
else:
    st.caption("No report has a location yet, so the map is empty.")

# --- export ---
st.subheader("Export")
e1, e2 = st.columns(2)
export = q.drop(columns=[]).copy()
e1.download_button("⬇️ Work queue (CSV)", export.to_csv(index=False), "roadscan_queue.csv",
                   "text/csv", width="stretch")
e2.download_button("⬇️ Work queue (GeoJSON, for GIS)", to_geojson(q), "roadscan_queue.geojson",
                   "application/geo+json", width="stretch")

# --- maintenance actions ---
st.subheader("Maintenance")
done = st.multiselect("Mark as repaired (removes from the open queue)",
                      options=list(q["id"]), format_func=lambda i: f"#{i}")
if st.button("Remove selected", disabled=not done):
    remove_reports(done)
    st.rerun()

with st.expander("Reset the queue (for a demo)"):
    sure = st.checkbox("Yes, delete every open report")
    if st.button("Delete all reports", type="primary", disabled=not sure):
        clear_all()
        st.session_state.pop("saved_reports", None)
        st.session_state.pop("last_added", None)
        st.rerun()
