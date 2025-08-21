# streamlit_app.py
import streamlit as st
from importlib import import_module

st.set_page_config(page_title="MKD Quantity App", layout="wide")
st.title("MKD Quantity App")

try:
    mod = import_module("app.quantity_engine")
except Exception as e:
    st.error("Failed to import app.quantity_engine — check logs and requirements.")
    st.exception(e)
    st.stop()

# If the module defines a callable entry, call it (common patterns: main(), run())
for name in ("main", "run", "app", "start"):
    fn = getattr(mod, name, None)
    if callable(fn):
        try:
            fn()
        except Exception as e:
            st.error(f"Error while running {name}() from app.quantity_engine:")
            st.exception(e)
        break
