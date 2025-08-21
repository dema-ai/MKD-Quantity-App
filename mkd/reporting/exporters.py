import pandas as pd

def export_boq(df, path_base):
    try:
        with pd.ExcelWriter(f"{path_base}.xlsx", engine="openpyxl") as w:
            df.to_excel(w, index=False)
        return f"{path_base}.xlsx"
    except Exception:
        df.to_csv(f"{path_base}.csv", index=False, encoding="utf-8-sig")
        df.to_html(f"{path_base}.html", index=False)
        return f"{path_base}.csv"
