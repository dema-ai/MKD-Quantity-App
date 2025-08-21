import io
import math
from dataclasses import dataclass, asdict
from typing import List, Tuple, Optional

import numpy as np
import pandas as pd
from PIL import Image
import streamlit as st
from streamlit_drawable_canvas import st_canvas

try:
    import fitz  # PyMuPDF
    _PYMUPDF_OK = True
except ImportError:
    _PYMUPDF_OK = False

try:
    from pdf2image import convert_from_bytes
    _PDF2IMAGE_OK = True
except ImportError:
    _PDF2IMAGE_OK = False

try:
    from PyPDF2 import PdfReader
    _PYPDF2_OK = True
except ImportError:
    _PYPDF2_OK = False

@dataclass
class Calibration:
    pixels_per_unit: float = 1.0
    unit: str = "m"

@dataclass
class Measurement:
    kind: str
    label: str
    value_units: str
    value: float
    page: int

def render_pdf_page(pdf_bytes: bytes, page_index: int, dpi: int = 200) -> Image.Image:
    if _PYMUPDF_OK:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page = doc[page_index]
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    if _PDF2IMAGE_OK:
        pages = convert_from_bytes(pdf_bytes, dpi=dpi, fmt="RGB")
        return pages[page_index]
    raise RuntimeError("No PDF backend available.")

def get_pdf_page_count(pdf_bytes: bytes) -> int:
    if _PYPDF2_OK:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        return len(reader.pages)
    if _PYMUPDF_OK:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        return len(doc)
    return 1

def dist_px(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])

def polyline_length_px(points: List[Tuple[float, float]]) -> float:
    return sum(dist_px(points[i], points[i+1]) for i in range(len(points)-1)) if len(points) > 1 else 0.0

def polygon_area_px(points: List[Tuple[float, float]]) -> float:
    n = len(points)
    if n < 3: return 0.0
    area = sum(points[i][0]*points[(i+1)%n][1] - points[i][1]*points[(i+1)%n][0] for i in range(n))
    return abs(area) * 0.5

def px_to_units(px: float, calib: Calibration) -> float:
    return px / max(calib.pixels_per_unit, 1e-12)

def px2_area_units(area_px: float, calib: Calibration) -> float:
    return area_px / (max(calib.pixels_per_unit, 1e-12)**2)

st.set_page_config(page_title="Open Takeoff", layout="wide")
st.title("Open Takeoff – Quantity Takeoff (Free & Local)")

if "calibration" not in st.session_state: st.session_state.calibration = Calibration()
if "measures" not in st.session_state: st.session_state.measures = []
if "current_page" not in st.session_state: st.session_state.current_page = 0
if "last_canvas_json" not in st.session_state: st.session_state.last_canvas_json = None

with st.sidebar:
    st.header("1) Upload Plan")
    allowed_types = ["png", "jpg", "jpeg"]
    if _PYMUPDF_OK or _PDF2IMAGE_OK: allowed_types.append("pdf")
    up = st.file_uploader("PDF or Image", type=allowed_types)
    dpi = st.slider("Render DPI (PDF)", 100, 400, 220, step=20)
    st.header("2) Units")
    unit = st.selectbox("Units", ["m", "ft"], index=0)
    st.session_state.calibration.unit = unit
    st.header("3) Page")
    page_idx = 0
    if up is not None and getattr(up, "type", "") == "application/pdf":
        pdf_bytes = up.read()
        page_count = get_pdf_page_count(pdf_bytes)
        page_idx = st.number_input("Page index (0-based)", min_value=0, max_value=max(0,page_count-1), value=st.session_state.current_page, step=1)
        st.session_state.current_page = page_idx

canvas_img: Optional[Image.Image] = None
if up:
    try:
        if getattr(up, "type", "") == "application/pdf":
            pdf_bytes = up.read()
            canvas_img = render_pdf_page(pdf_bytes, st.session_state.current_page, dpi=dpi)
        else:
            canvas_img = Image.open(up).convert("RGB")
    except Exception as e:
        st.error(f"Failed to load file: {e}")

col_left, col_right = st.columns([2,1], gap="large")

with col_left:
    st.subheader("Canvas")
    if canvas_img is None:
        st.info("Upload an image (PNG/JPG) or PDF to begin.")
    else:
        tool = st.radio("Tool", ["Calibrate", "Length", "Area", "Count"], horizontal=True)
        label = st.text_input("Label/Category", value="General")
        disp_w = st.slider("Canvas width (px)", 600, 1800, 1100, step=50)
        scale = disp_w / float(canvas_img.width)
        disp_h = int(canvas_img.height * scale)
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
            key=f"canvas_{st.session_state.current_page}_{tool}"
        )
        st.session_state.last_canvas_json = canvas_result.json_data
        shapes = canvas_result.json_data.get("objects", []) if canvas_result.json_data else []

        def get_last_path_points() -> List[Tuple[float,float]]:
            for obj in reversed(shapes):
                if obj.get("type")=="path" and obj.get("path"):
                    pts=[]
                    for seg in obj["path"]:
                        if len(seg)>=3 and seg[0] in ("M","L"):
                            pts.append((float(seg[1]), float(seg[2])))
                    return pts
            return []

        pts = get_last_path_points()
        calib = st.session_state.calibration
        def save_measure(kind: str, value: float, value_units: str):
            st.session_state.measures.append(Measurement(kind, label or kind, value_units, value, st.session_state.current_page))
            st.success(f"Saved {kind}: {value:.3f} {value_units}")

        if tool=="Calibrate":
            real_len = st.number_input(f"Known length ({unit})", min_value=0.0, value=1.0, step=0.1, format="%0.3f")
            if st.button("Set Calibration from last line") and len(pts)>=2:
                px_len = polyline_length_px(pts)
                if px_len>0: calib.pixels_per_unit = px_len / max(real_len,1e-9)
        elif tool=="Length":
            if st.button("Save last polyline as LENGTH") and len(pts)>=2:
                val = px_to_units(polyline_length_px(pts), calib)
                save_measure("length", val, unit)
        elif tool=="Area":
            if st.button("Save last polygon as AREA") and len(pts)>=3:
                if pts[0]!=pts[-1]: pts.append(pts[0])
                val = px2_area_units(polygon_area_px(pts), calib)
                save_measure("area", val, f"{unit}^2")
        else:
            count_n = st.number_input("How many points?", min_value=1, value=1, step=1)
            if st.button("Save COUNT"):
                save_measure("count", float(count_n), "ea")

with col_right:
    st.subheader("Calibration & Measurements")
    st.write(f"**Calibration:** {st.session_state.calibration.pixels_per_unit:.3f} px per {unit}")
    if st.session_state.measures:
        df=pd.DataFrame([asdict(m) for m in st.session_state.measures])
        st.dataframe(df,use_container_width=True)
        st.markdown(f"**Totals**\n- Length: {df.loc[df['kind']=='length','value'].sum():.3f} {unit}\n- Area: {df.loc[df['kind']=='area','value'].sum():.3f} {unit}^2\n- Count: {df.loc[df['kind']=='count','value'].sum():.0f} ea")
