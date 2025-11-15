import streamlit as st
import pandas as pd
import plotly.express as px

st.title("Spatial Pattern for G7 Countries")

uploaded = st.file_uploader("Upload CSV or Excel with columns: Country, Value", 
                             type=["csv", "xlsx", "xls"])

if uploaded:
    if uploaded.name.endswith("csv"):
        df = pd.read_csv(uploaded)
    else:
        df = pd.read_excel(uploaded)

    st.write("### Data Preview")
    st.dataframe(df.head())

    mapping = {
        "United States": "USA",
        "United States of America": "USA",
        "US": "USA",
        "U.S": "USA",

        "United Kingdom": "GBR",
        "UK": "GBR",
        "U.K": "GBR",

        "Canada": "CAN",
        "France": "FRA",
        "Germany": "DEU",
        "Italy": "ITA",
        "Japan": "JPN",
    }

    df["ISO"] = df["Country"].map(mapping)

    missing = df[df["ISO"].isna()]
    if len(missing) > 0:
        st.error("Some country names are not recognized. Fix them:")
        st.write(missing)
    else:
        fig = px.choropleth(
            df,
            locations="ISO",
            color="Value",
            hover_name="Country",
            color_continuous_scale="YlOrRd",
            projection="natural earth",
            title="Spatial Pattern Across G7 Countries"
        )
        st.plotly_chart(fig, use_container_width=True)
