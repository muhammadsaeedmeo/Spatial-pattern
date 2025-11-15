import streamlit as st
import pandas as pd
import pycountry
import plotly.express as px

st.title("Spatial Pattern Visualizer (No GeoPandas Required)")

# -----------------------------------------------------------
# Upload data
# -----------------------------------------------------------
uploaded = st.file_uploader("Upload your dataset (CSV or Excel)", type=["csv", "xlsx"])

if uploaded is not None:
    if uploaded.name.endswith(".csv"):
        df = pd.read_csv(uploaded)
    else:
        df = pd.read_excel(uploaded)

    st.subheader("Raw Data Preview")
    st.write(df.head())

    # -----------------------------------------------------------
    # Select columns
    # -----------------------------------------------------------
    country_col = st.selectbox("Select country column", df.columns)
    value_col = st.selectbox("Select value column to map", df.columns)

    # -----------------------------------------------------------
    # Clean country names
    # -----------------------------------------------------------
    df["__country_clean__"] = (
        df[country_col]
        .astype(str)
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
        .str.replace(r"[.]", "", regex=True)
        .str.title()
    )

    # -----------------------------------------------------------
    # Convert names to ISO-3
    # -----------------------------------------------------------
    def to_iso(x):
        try:
            return pycountry.countries.lookup(x).alpha_3
        except:
            return None

    df["iso_code"] = df["__country_clean__"].apply(to_iso)

    bad = df[df["iso_code"].isna()][country_col].unique()
    if len(bad) > 0:
        st.error("These country names could not be recognized:")
        st.write(list(bad))
        st.stop()

    # -----------------------------------------------------------
    # Plotly world choropleth (built-in geometry)
    # -----------------------------------------------------------
    fig = px.choropleth(
        df,
        locations="iso_code",
        color=value_col,
        hover_name="__country_clean__",
        projection="natural earth",
        color_continuous_scale="Viridis"
    )

    st.subheader("Spatial Pattern Map")
    st.plotly_chart(fig, use_container_width=True)
