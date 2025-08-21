import streamlit as st
import app.quantity_engine as qe

# If quantity_engine has a main() function, call it
if hasattr(qe, "main"):
    qe.main()
else:
    st.warning("No main() function found in app/quantity_engine.py")
    # Just run the file so Streamlit can display UI code inside it
    with open("app/quantity_engine.py", "r", encoding="utf-8") as f:
        exec(f.read())
