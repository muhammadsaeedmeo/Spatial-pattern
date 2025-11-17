import streamlit as st
import pandas as pd
import pycountry
import plotly.express as px
import unicodedata
import altair as alt

# --- CONFIGURATION ---
PASSWORD = "1992"

# ============================================================
# ISO NORMALIZATION + Turkey override
# ============================================================
def normalize_country(name: str):
    clean = unicodedata.normalize("NFKD", str(name)).strip()
    clean = clean.replace("\u200b", "").replace("\uFEFF", "")
    clean = clean.replace("\xa0", " ")
    clean = clean.strip()
    # Hard override for all Turkey/Türkiye variants
    if clean.lower() in ["turkey", "türkiye", "turkiye"]:
        return "TUR"
    try:
        return pycountry.countries.lookup(clean).alpha_3
    except:
        return None

# ============================================================
# STREAMLIT APP
# ============================================================
st.title("🌎 Choropleth Map for Country-Level Variables")

# --- 1. PASSWORD PROTECTION ---
password_input = st.sidebar.text_input(
    "🔑 Enter Password to Access:",
    type="password"
)

if password_input != PASSWORD:
    if password_input:
        st.error("Access Denied. Please enter the correct password.")
    st.stop()

# --- MAIN APP CONTENT ---
st.sidebar.success("Access Granted!")
file = st.file_uploader("Upload CSV or Excel with a 'country' column")

if file:
    # Load file
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    # Basic validation
    if "country" not in df.columns:
        st.error("Dataset must contain a 'country' column.")
        st.stop()

    # Resolve ISO3
    df["iso3"] = df["country"].apply(normalize_country)
    unresolved = df[df["iso3"].isna()]["country"].unique().tolist()
    if unresolved:
        st.warning(f"Unrecognized country names: {unresolved}")

    # Drop rows without valid ISO3
    df_clean = df.dropna(subset=["iso3"])

    # Select numeric variable
    numeric_cols = df_clean.select_dtypes(include=["float64", "int64"]).columns.tolist()
    variable = st.selectbox("Select variable to map:", numeric_cols)

    # --- Prepare Interpretation Data ---
    df_sorted = df_clean.sort_values(by=variable, ascending=False).reset_index(drop=True)
    max_row = df_sorted.iloc[0]
    min_row = df_sorted.iloc[-1]
    
    # ============================================================
    # Choropleth
    # ============================================================
    st.subheader(f"Map Visualization of **{variable}**")
    
    # Set up a dynamic subtitle/caption for the plot
    caption_text = (
        f"**Color Interpretation:** Darker tones (high values) peak at **{max_row['country']}** "
        f"(Value: {max_row[variable]:.2f}), and lighter tones (low values) bottom out at **{min_row['country']}** "
        f"(Value: {min_row[variable]:.2f})."
    )

    fig = px.choropleth(
        df_clean,
        locations="iso3",
        color=variable,
        hover_name="country",
        projection="natural earth",
        color_continuous_scale="Viridis",
        template="plotly_white",
        height=600,
        # Add the caption/legend text as a subtitle to the figure
        title=f"Geographical Distribution of {variable}<br><sup>{caption_text}</sup>"
    )

    fig.update_geos(
        showcountries=True,
        countrycolor="black",
        showcoastlines=True,
        coastlinecolor="gray",
        oceancolor="aliceblue"
    )
    
    # Adjust title position to look better as a combined title/subtitle
    fig.update_layout(
        title={
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        }
    )

    st.plotly_chart(fig, use_container_width=True)
    
    # ============================================================
    # 3. Country Data Table (Sidebar)
    # ============================================================
    st.sidebar.header("Country Data Table")
    st.sidebar.markdown(f"**Sorted values for: {variable}**")
    st.sidebar.dataframe(
        df_sorted[['country', variable]].rename(columns={variable: "Value"}),
        use_container_width=True,
        hide_index=True
    )

    # ============================================================
    # 4. Clearer Interpretation (Research Article Perspective)
    # ============================================================
    st.markdown("---")
    st.header("🔍 Interpretation of Results")
    
    st.markdown("### Research Article Perspective (Discussion/Results Section)")
    
    st.markdown(
        f"""
        The choropleth map provides compelling evidence regarding the spatial distribution of **{variable}**. 
        From a research standpoint, the color gradation—where **darker tones correlate with higher values** and **lighter tones with lower values**—reveals distinct regional clusters. 
        
        * **Maximum Observation:** The highest value for **{variable}** is observed in **{max_row['country']}** (represented by the **darkest shade**).
        * **Minimum Observation:** The lowest value is observed in **{min_row['country']}** (represented by the **lightest shade**).
        
        * **Hypothesis Generation:** The strong visual contrast between these extremes suggests that geographical, economic, or policy factors may be significantly driving the variance in **{variable}**. 
        * **Future Work:** Further statistical analysis (e.g., spatial autocorrelation or regression) is warranted to test for significant regional dependencies and to formally assess the drivers of the observed high-value clusters.
        """
    )
    
    st.markdown(
        f"""
        ### Color Scale Guide  
        The color scale reflects the magnitude of **{variable}**. The scale used is **'Viridis'**, a perceptually uniform colormap:  
        * **Darker Tones:** Indicate **Higher Values**.  
        * **Lighter Tones:** Indicate **Lower Values**.  
        """
    )
