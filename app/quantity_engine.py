COMPANY_NAME = "MKD Construction"
PROJECT_NAME = "Demo BoQ – Addis Ababa"
LOGO_PATH = r"C:\Users\hp\Desktop\your_logo.png"  # optional; leave "" if none

import os
import pandas as pd
from datetime import date, datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle

# App metadata
COMPANY_NAME = "MKD Construction"
PROJECT_NAME = "Demo BoQ – Addis Ababa"
LOGO_PATH = r"C:\Users\hp\Desktop\your_logo.png"  # optional; "" if none

# --- safe import of assumptions helper ---
try:
    from app.assumptions import generate_assumptions
except ImportError:
    def generate_assumptions(output_dir, meta):
        """Placeholder: writes assumptions to text file."""
        path = os.path.join(output_dir, "assumptions.txt")
        with open(path, "w", encoding="utf-8") as f:
            for k, v in meta.items():
                f.write(f"{k}: {v}\n")
        return path

# -------- Governance --------
def validate_rate_table(df):
    issues = []
    required_cols = {"item_code", "rate_ETB", "effective_date"}
    if not required_cols.issubset(df.columns):
        issues.append("Missing required columns.")
    if df["rate_ETB"].isnull().any():
        issues.append("Null rates present.")
    if (df["rate_ETB"] <= 0).any():
        issues.append("Non-positive rates found.")
    if issues:
        raise ValueError(f"Rate table validation failed: {issues}")
    return True

# -------- Core Calcs --------
def calc_wall_area(length_m, height_m, openings_area_m2=0.0, wastage_factor=0.0):
    gross_area = length_m * height_m
    net_area = gross_area - openings_area_m2
    return round(net_area + net_area * (wastage_factor / 100), 3)

def calc_volume(area_m2, thickness_m):
    return round(area_m2 * thickness_m, 3)

def calc_cost(quantity, rate):
    return round(quantity * rate, 2)

# -------- Rate Table Loader --------
def load_rate_table(path):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        pd.DataFrame([
            {"item_code": "W001", "description": "230mm Brick Wall", "unit": "m3", "rate_ETB": 4200, "effective_date": "2025-07-01"},
            {"item_code": "S001", "description": "150mm Concrete Slab", "unit": "m3", "rate_ETB": 3500, "effective_date": "2025-07-01"}
        ]).to_csv(path, index=False)
    df = pd.read_csv(path)
    validate_rate_table(df)
    return df

# -------- BoQ Generator --------
def generate_boq(records, rate_table):
    boq_df = pd.DataFrame(records)
    boq_df = boq_df.merge(rate_table, on="item_code", how="left")
    boq_df["total_ETB"] = boq_df.apply(lambda r: calc_cost(r["qty"], r["rate_ETB"]), axis=1)
    boq_df["date"] = date.today().isoformat()
    return boq_df

# -------- Exports --------
def export_excel(boq_df, folder):
    from xlsxwriter import Workbook
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    path = os.path.join(folder, f"BoQ_{ts}.xlsx")
    with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
        boq_df.to_excel(writer, sheet_name="BoQ", index=False, startrow=1)
        wb = writer.book
        ws = writer.sheets["BoQ"]
        header_fmt = wb.add_format({"bold": True, "bg_color": "#E6E6E6", "border": 1})
        for col, col_name in enumerate(boq_df.columns):
            ws.write(0, col, col_name, header_fmt)
        etb_fmt = wb.add_format({"num_format": "#,##0.00"})
        qty_fmt = wb.add_format({"num_format": "#,##0.000"})
        ws.set_column("D:D", 12, qty_fmt)
        ws.set_column("E:F", 14, etb_fmt)
        total_row = len(boq_df) + 2
        ws.write(total_row, 4, "Grand Total (ETB):", header_fmt)
        ws.write_formula(total_row, 5, f"=SUM(F2:F{len(boq_df) + 1})", etb_fmt)
        ws.write(total_row + 2, 0, "Disclosure: AI-assisted; professional review required.")
    print(f"Excel exported: {path}")

def export_pdf(boq_df, folder):
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    path = os.path.join(folder, f"BoQ_{ts}.pdf")
    c = canvas.Canvas(path, pagesize=A4)
    if LOGO_PATH and os.path.exists(LOGO_PATH):
        try:
            c.drawImage(LOGO_PATH, 450, 755, width=100, height=40, preserveAspectRatio=True, mask='auto')
        except:
            pass
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 800, COMPANY_NAME)
    c.setFont("Helvetica", 12)
    c.drawString(50, 780, PROJECT_NAME)
    c.setFont("Helvetica", 10)
    c.drawString(50, 765, f"Generated: {date.today().isoformat()}")
    data = [list(boq_df.columns)] + boq_df.values.tolist()
    table = Table(data, colWidths=[70, 160, 40, 50, 50, 60, 50])
    style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (3, 1), (-1, -1), "RIGHT")
    ])
    table.setStyle(style)
    table.wrapOn(c, 50, 650)
    table.drawOn(c, 50, 600 - (len(data) * 18))
    c.save()
    print(f"PDF exported: {path}")

# -------- Main Runner --------
def run_engine(input_data=None, rate_path=None):
    if input_data is None:
        sample_data = [
            {"item_code": "W001", "description": "230mm Brick Wall", "unit": "m3",
             "length_m": 4.0, "height_m": 3.0, "thickness_mm": 230, "openings_area_m2": 1.2, "wastage_factor": 5},
            {"item_code": "S001", "description": "150mm Concrete Slab", "unit": "m3",
             "length_m": 5.0, "width_m": 2.5, "thickness_m": 0.15, "wastage_factor": 3}
        ]
    else:
        df_in = pd.read_csv(input_data) if input_data.endswith(".csv") else pd.read_excel(input_data)
        sample_data = df_in.to_dict(orient="records")

    rate_file = rate_path or os.path.join("app", "rate_tables", "RateTables-YYYYMMDD.csv")
    rates = load_rate_table(rate_file)

    calculated = []
    for item in sample_data:
        if item["item_code"].startswith("W"):
            area = calc_wall_area(item["length_m"], item["height_m"], item.get("openings_area_m2", 0.0),
                                  item.get("wastage_factor", 0.0))
            qty = calc_volume(area, item["thickness_mm"] / 1000)
        elif item["item_code"].startswith("S"):
            area = item["length_m"] * item["width_m"]
            qty = calc_volume(area, item["thickness_m"] + (item["thickness_m"] * item.get("wastage_factor", 0.0) / 100))
        else:
            qty