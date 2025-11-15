import streamlit as st
import pandas as pd
import pycountry
import plotly.express as px
import unicodedata

# ============================================================
# ISO NORMALIZATION + Turkey override
# ============================================================
def normalize_country(name: str):
    clean = unicodedata.normalize("NFKD", str(name)).strip()
    clean = clean.replace("\u200b", "").replace("\uFEFF", "")
    clean = clean.replace("\xa0", " ")
    clean = clean.strip()

    if clean.lower() in ["turkey", "türkiye", "turkiye"]:
        return "TUR"

    try:
        return pycountry.countries.lookup(clean).alpha_3
    except:
        return None

# ============================================================
# STREAMLIT APP
# ============================================================
st.title("Choropleth Map for Country-Level Variables")

file = st.file_uploader("Upload CSV or Excel with a 'country' column")

if file:
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    if "country" not in df.columns:
        st.error("Dataset must contain a 'country' column.")
        st.stop()

    df["iso3"] = df["country"].apply(normalize_country)

    unresolved = df[df["iso3"].isna()]["country"].unique().tolist()
    if unresolved:
        st.warning(f"Unrecognized country names: {unresolved}")

    df_clean = df.dropna(subset=["iso3"])

    numeric_cols = df_clean.select_dtypes(include=["float64", "int64"]).columns.tolist()
    variable = st.selectbox("Select variable to map:", numeric_cols)

    # =============================================
    # COLOR PICKER for country name labels
    # =============================================
    label_color = st.color_picker("Select country label color:", "#FFFFFF")

    # =============================================
    # Choropleth
    # =============================================
    fig = px.choropleth(
        df_clean,
        locations="iso3",
        color=variable,
        hover_name="country",
        projection="natural earth",
        color_continuous_scale="Inferno",
    )

    fig.update_geos(
        showcountries=True,
        countrycolor="black",
        showcoastlines=True,
        coastlinecolor="gray",
    )

    # Label each country
    for _, row in df_clean.iterrows():
        fig.add_scattergeo(
            locations=[row["iso3"]],
            text=row["country"],
            mode="text",
            textposition="middle center",
            textfont=dict(color=label_color, size=12),
            showlegend=False
        )

    st.plotly_chart(fig, use_container_width=True)

    # Interpretation note
    st.markdown(
        f"""
        ### Interpretation  
        The color scale shows the relative magnitude of **{variable}** across countries.  
        Darker colors indicate higher values and lighter colors indicate lower values.
        """
    )
