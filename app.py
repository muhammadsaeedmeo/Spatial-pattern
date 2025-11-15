import streamlit as st
import pandas as pd
import pycountry
import plotly.express as px

# ============================================================
# 1. Custom resolvers (MANDATORY: forces Turkey to resolve)
# ============================================================
CUSTOM_MAP = {
    "Turkey": "Turkey",                # forces lookup to correct ISO3 (TUR)
    "Türkiye": "Turkey",
    "Russia": "Russian Federation",
    "Vietnam": "Viet Nam",
    "South Korea": "Korea, Republic of",
    "North Korea": "Korea, Democratic People's Republic of",
    "Iran": "Iran, Islamic Republic of",
}

def resolve_country(name: str):
    raw = name.strip()

    # Apply normalizer
    if raw in CUSTOM_MAP:
        raw = CUSTOM_MAP[raw]

    try:
        return pycountry.countries.lookup(raw).alpha_3
    except:
        return None


# ============================================================
# 2. App
# ============================================================
st.title("Choropleth Map for Country-Level Variables")

file = st.file_uploader("Upload CSV or Excel with 'country' column")

if file:
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    if "country" not in df.columns:
        st.error("Dataset must contain a column named 'country'.")
        st.stop()

    # ISO3 resolution
    df["iso3"] = df["country"].apply(resolve_country)

    unresolved = df[df["iso3"].isna()]["country"].unique().tolist()
    if unresolved:
        st.warning(f"Unrecognized country names: {unresolved}")

    df_clean = df.dropna(subset=["iso3"])

    # Select variable
    numeric_cols = df_clean.select_dtypes(include=["float64", "int64"]).columns.tolist()
    variable = st.selectbox("Select variable to shade:", numeric_cols)

    # ============================================================
    # 3. High-contrast map + country labels
    # ============================================================
    fig = px.choropleth(
        df_clean,
        locations="iso3",
        color=variable,
        hover_name="country",
        projection="natural earth",
        color_continuous_scale="Turbo",     # sharp, high-contrast
    )

    # add country borders
    fig.update_geos(
        showcountries=True,
        countrycolor="black",
        showcoastlines=True,
        coastlinecolor="gray"
    )

    # show labels (centroid approximation)
    for _, row in df_clean.iterrows():
        fig.add_scattergeo(
            locations=[row["iso3"]],
            text=row["country"],
            mode="text",
            textposition="middle center",
            showlegend=False
        )

    st.plotly_chart(fig, use_container_width=True)
