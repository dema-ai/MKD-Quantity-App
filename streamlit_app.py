import streamlit as st
from app import quantity_engine  # adjust if your module path is different
import pandas as pd

st.set_page_config(page_title="MKD Quantity App", layout="wide")
st.title("MKD Quantity App 🚧 Quantity Takeoff")

st.sidebar.header("Upload & Settings")

# File upload
uploaded_file = st.sidebar.file_uploader(
    "Upload your plan (PDF or Image)", type=["pdf", "png", "jpg", "jpeg"]
)

# Units selection
unit = st.sidebar.selectbox("Select units", ["m", "ft"])
st.sidebar.write(f"Current units: {unit}")

# DPI (for PDF rendering if needed)
dpi = st.sidebar.slider("PDF Render DPI", min_value=100, max_value=400, value=220, step=20)

# Page number input for PDFs
page_index = st.sidebar.number_input("Page number (0-based)", min_value=0, value=0, step=1)

# Initialize session state
if "measures" not in st.session_state:
    st.session_state.measures = []

st.header("Plan / Canvas")

# Display uploaded file
canvas_img = None
if uploaded_file is not None:
    try:
        if uploaded_file.type == "application/pdf":
            pdf_bytes = uploaded_file.read()
            uploaded_file.seek(0)
            # Use your quantity_engine function to render PDF to image
            canvas_img = quantity_engine.render_pdf_page(pdf_bytes, page_index, dpi=dpi)
        else:
            from PIL import Image
            canvas_img = Image.open(uploaded_file).convert("RGB")
    except Exception as e:
        st.error(f"Error opening file: {e}")

if canvas_img is not None:
    import numpy as np
    from streamlit_drawable_canvas import st_canvas

    # Scale canvas for display
    disp_w = st.slider("Canvas width (px)", 600, 1800, 1100, step=50)
    scale = disp_w / float(canvas_img.width)
    disp_h = int(canvas_img.height * scale)

    tool = st.radio("Tool", ["Calibrate", "Length", "Area", "Count"], horizontal=True)
    label = st.text_input("Label / Category", value="General")
    stroke_width = st.slider("Stroke width", 1, 8, 3)
    st.slider("Point marker size", 1, 10, 4, key="point_radius")

    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.2)",
        stroke_width=stroke_width,
        background_image=canvas_img.resize((disp_w, disp_h)),
        update_streamlit=True,
        height=disp_h,
        width=disp_w,
        drawing_mode="freedraw",
        key=f"canvas_{tool}",
    )

    shapes = []
    if canvas_result.json_data is not None:
        shapes = canvas_result.json_data.get("objects", [])

    def get_last_path_points():
        for obj in reversed(shapes):
            if obj.get("type") == "path" and obj.get("path"):
                pts = []
                for seg in obj["path"]:
                    if len(seg) >= 3 and seg[0] in ("M", "L"):
                        try:
                            x, y = float(seg[1]), float(seg[2])
                        except Exception:
                            continue
                        pts.append((x, y))
                return pts
        return []

    pts = get_last_path_points()

    if "calibration" not in st.session_state:
        st.session_state.calibration = quantity_engine.Calibration()

    calib = st.session_state.calibration

    def save_measure(kind, value, value_units):
        m = quantity_engine.Measurement(
            kind=kind, label=label or kind, value_units=value_units, value=value, page=page_index
        )
        st.session_state.measures.append(m)
        st.success(f"Saved {kind}: {value:.3f} {value_units}")

    if tool == "Calibrate":
        real_len = st.number_input(f"Known length ({unit})", min_value=0.0, value=1.0, step=0.1, format="%0.3f")
        if st.button("Set Calibration"):
            if len(pts) >= 2:
                px_len = quantity_engine.polyline_length_px(pts)
                if px_len > 0:
                    pixels_per_unit = px_len / max(real_len, 1e-9)
                    calib.pixels_per_unit = pixels_per_unit
                    st.success(f"Calibrated: {pixels_per_unit:.3f} px per {unit}")
                else:
                    st.warning("Draw a line first.")
            else:
                st.warning("Draw a line over known dimension first.")

    elif tool == "Length":
        if st.button("Save last polyline as LENGTH"):
            if len(pts) >= 2:
                px_len = quantity_engine.polyline_length_px(pts)
                val = quantity_engine.px_to_units(px_len, calib)
                save_measure("length", val, unit)
            else:
                st.warning("Draw a polyline first.")

    elif tool == "Area":
        if st.button("Save last polygon as AREA"):
            if len(pts) >= 3:
                if pts[0] != pts[-1]:
                    pts.append(pts[0])
                area_px = quantity_engine.polygon_area_px(pts)
                val = quantity_engine.px2_area_units(area_px, calib)
                save_measure("area", val, f"{unit}^2")
            else:
                st.warning("Draw a closed polygon first.")

    else:
        count_n = st.number_input("How many points to save from last blob?", min_value=1, value=1, step=1)
        if st.button("Save COUNT"):
            save_measure("count", float(count_n), "ea")

st.header("Measurements & Totals")

if st.session_state.measures:
    df = pd.DataFrame([m.__dict__ for m in st.session_state.measures])
    st.dataframe(df, use_container_width=True)
    total_lengths = df.loc[df["kind"] == "length", "value"].sum()
    total_areas = df.loc[df["kind"] == "area", "value"].sum()
    total_counts = df.loc[df["kind"] == "count", "value"].sum()
    st.markdown(
        f"**Totals**\n- Length: {total_lengths:.3f} {unit}\n- Area: {total_areas:.3f} {unit}^2\n- Count: {total_counts:.0f} ea"
    )
    if st.button("Clear all measurements"):
        st.session_state.measures = []
        st.info("Cleared.")
else:
    st.info("No measurements yet.")
