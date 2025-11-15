import streamlit as st
import geopandas as gpd
import pandas as pd
import pycountry
import plotly.express as px

st.title("Spatial Pattern Visualizer")

# -----------------------------------------------------------
# Upload data
# -----------------------------------------------------------
uploaded = st.file_uploader("Upload your dataset (CSV or Excel)", type=["csv", "xlsx"])

if uploaded is not None:
    # Load file
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
    # Convert to ISO-3
    # -----------------------------------------------------------
    def to_iso(x):
        try:
            return pycountry.countries.lookup(x).alpha_3
        except:
            return None

    df["ISO"] = df["__country_clean__"].apply(to_iso)

    # Report bad names
    bad = df[df["ISO"].isna()][country_col].unique()

    if len(bad) > 0:
        st.error("These country names could not be recognized:")
        st.write(list(bad))
        st.stop()

    # -----------------------------------------------------------
    # Load world geometry
    # -----------------------------------------------------------
    world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
    world = world[["iso_a3", "geometry"]]

    # -----------------------------------------------------------
    # Merge
    # -----------------------------------------------------------
    merged = world.merge(df, left_on="iso_a3", right_on="ISO", how="left")

    # -----------------------------------------------------------
    # Choropleth map
    # -----------------------------------------------------------
    st.subheader("Spatial Pattern Map")

    fig = px.choropleth(
        merged,
        geojson=merged.geometry,
        locations=merged.index,
        color=value_col,
        projection="natural earth",
        hover_name="__country_clean__",
        color_continuous_scale="Viridis",
    )
    fig.update_geos(fitbounds="locations", visible=False)

    st.plotly_chart(fig, use_container_width=True)
