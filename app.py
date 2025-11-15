import streamlit as st
import pandas as pd
import pycountry
import plotly.express as px

# -------------------------------------------------------------------
# 1. Custom country name mappings (extend freely)
# -------------------------------------------------------------------
CUSTOM_MAP = {
    "Turkey": "Turkey",
    "Türkiye": "Turkey",
    "Russia": "Russian Federation",
    "Iran": "Iran, Islamic Republic of",
    "Vietnam": "Viet Nam",
    "South Korea": "Korea, Republic of",
    "North Korea": "Korea, Democratic People's Republic of",
}

# -------------------------------------------------------------------
# 2. Safe resolver: maps raw names to ISO3
# -------------------------------------------------------------------
def resolve_country(name: str):
    # Apply reconciling dictionary
    if name in CUSTOM_MAP:
        name = CUSTOM_MAP[name]

    try:
        return pycountry.countries.lookup(name).alpha_3
    except:
        return None

# -------------------------------------------------------------------
# 3. Streamlit App
# -------------------------------------------------------------------
st.title("Country-Level Choropleth (General & Geopandas-Free)")

# User uploads any file containing "country" and "value" columns
file = st.file_uploader("Upload your dataset (CSV/XLSX)")

if file:
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    if "country" not in df.columns:
        st.error("Your dataset must contain a column named 'country'.")
        st.stop()

    # Resolve ISO codes
    df["iso3"] = df["country"].apply(resolve_country)

    unresolved = df[df["iso3"].isna()]["country"].unique().tolist()

    if unresolved:
        st.warning(f"Unrecognized country names: {unresolved}")

    df_clean = df.dropna(subset=["iso3"])

    # User chooses variable to plot
    numeric_cols = df_clean.select_dtypes(include=["int64", "float64"]).columns.tolist()
    variable = st.selectbox("Select variable for shading:", numeric_cols)

    # -------------------------------------------------------------------
    # 4. Plotly choropleth
    # -------------------------------------------------------------------
    fig = px.choropleth(
        df_clean,
        locations="iso3",
        color=variable,
        hover_name="country",
        projection="natural earth",
        color_continuous_scale="Viridis",
    )

    fig.update_geos(showcountries=True, showcoastlines=True)
    st.plotly_chart(fig, use_container_width=True)
