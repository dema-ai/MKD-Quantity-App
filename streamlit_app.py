import streamlit as st
import pandas as pd

st.set_page_config(page_title="MKD Quantity App", layout="wide")

st.title("📐 MKD Quantity App")
st.write("Upload your BOQ/quantity Excel or CSV file to process and analyze.")

uploaded_file = st.file_uploader("Upload file", type=["csv", "xlsx"])

if uploaded_file:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.success("File uploaded successfully ✅")
        st.dataframe(df)

        st.write("### Quick Summary")
        st.write(f"Rows: {df.shape[0]} | Columns: {df.shape[1]}")

        if st.button("Download as CSV"):
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="processed_quantities.csv",
                mime="text/csv",
            )
    except Exception as e:
        st.error(f"Error processing file: {e}")
else:
    st.info("Please upload a CSV or Excel file to continue.")
