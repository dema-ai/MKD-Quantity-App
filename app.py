import os
import pandas as pd
from mkd.utils.reliability import retry
from mkd.reporting.exporters import export_boq

@retry()
def build_dataframe():
    return pd.DataFrame([{"Item": "Concrete", "Qty": 25}, {"Item": "Steel", "Qty": 10}])

def main():
    df = build_dataframe()
    base = os.path.join("outputs", "BoQ_Demo")
    out = export_boq(df, base)
    print(f"✅ Output written: {out}")

if __name__ == "__main__":
    main()
