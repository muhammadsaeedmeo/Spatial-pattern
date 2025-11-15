import streamlit as st
import pandas as pd
import pycountry
import plotly.express as px
import unicodedata

# ============================================================
# 1. HARD NORMALIZATION + Turkey override
# ============================================================

def normalize_country(name: str):
    # Remove hidden unicode garbage and normalize string
    clean = unicodedata.normalize("NFKD", str(name)).strip()
    clean = clean.replace("\u200b", "").replace("\uFEFF", "")
    clean = clean.replace("\xa0", " ")  # non-breaking space
    clean = clean.strip()

    # Turkey forcing – catches every version
    if clean.lower() in ["turkey", "türkiye", "turkiye"]:
        return "TUR"

    # Otherwise do ISO lookup
    try:
        return pycountry.countries.lookup(clean).alpha_3
    except:
        return None

# ============================================================
# 2. Streamlit interface
# ============================================================
st.title("Choropleth Map for Country-Level Variables")

file = st.file_uploader("Upload CSV or Excel containing a 'country' column")

if file:
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    if "country" not in df.columns:
        st.error("Dataset must contain a column named 'country'.")
        st.stop()

    # Resolve ISO3
    df["iso3"] = df["country"].apply(normalize_country)

    unresolved = df[df["iso3"].isna()]["country"].unique().tolist()
    if unresolved:
        st.warning(f"Unrecognized country names: {unresolved}")

    df_clean = df.dropna(subset=["iso3"])

    numeric_cols = df_clean.select_dtypes(include=["float64", "int64"]).columns.tolist()
    variable = st.selectbox("Select variable to map:", numeric_cols)

    # ============================================================
    # 3. Choropleth with very high-contrast color scale
    # ============================================================
    fig = px.choropleth(
        df_clean,
        locations="iso3",
        color=variable,
        hover_name="country",
        projection="natural earth",
        color_continuous_scale="Inferno",   # sharp contrast
    )

    fig.update_geos(
        showcountries=True,
        countrycolor="black",
        showcoastlines=True,
        coastlinecolor="gray",
    )

    # Add country labels
    for _, row in df_clean.iterrows():
        fig.add_scattergeo(
            locations=[row["iso3"]],
            text=row["country"],
            mode="text",
            textposition="middle center",
            showlegend=False
        )

    st.plotly_chart(fig, use_container_width=True)

    # ============================================================
    # 4. Interpretation Note
    # ============================================================
    st.markdown(
        f"""
        ### Interpretation Note  
        The color scale represents the relative magnitude of **{variable}** across countries.  
        Darker and more intense colors indicate **higher values**, while lighter shades reflect **lower levels**.  
        This allows visual identification of spatial concentration, disparities, and regional clustering in the variable.
        """
    )
