import streamlit as st
import pandas as pd

st.title("Panel Data Viewer and Variable Selector")

uploaded = st.file_uploader("Upload CSV or Excel panel dataset", type=["csv", "xlsx", "xls"])

data = None
if uploaded:
    if uploaded.name.endswith("csv"):
        data = pd.read_csv(uploaded)
    else:
        data = pd.read_excel(uploaded)

    st.write("### Preview of Data")
    st.dataframe(data.head())

    vars_available = list(data.columns)
    choice = st.selectbox("Select a variable", vars_available)

    st.write(f"### Summary of {choice}")
    st.write(data[choice].describe())


