import streamlit as st
import pandas as pd

st.title("Panel Data Viewer and Variable Selector")

uploaded = st.file_uploader(
    "Upload CSV or Excel panel dataset",
    type=["csv", "xlsx", "xls"]
)

data = None

if uploaded:
    if uploaded.name.endswith("csv"):
        data = pd.read_csv(uploaded)
    else:
        data = pd.read_excel(uploaded)

    st.write("### Preview of Data")
    st.dataframe(data.head())

    variables = list(data.columns)
    selected_var = st.selectbox("Select a variable", variables)

    st.write(f"### Summary statistics of {selected_var}")
    st.write(data[selected_var].describe())
