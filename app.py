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
# Helper function to categorize color intensity
# ============================================================
def get_color_intensity(value, min_val, max_val):
    if pd.isna(value):
        return "N/A"
    
    # Normalize value between 0 and 1
    if max_val == min_val:
        normalized = 0.5
    else:
        normalized = (value - min_val) / (max_val - min_val)

    # Viridis scale: 1 (highest value) is yellow/lightest; 0 (lowest value) is deep purple/darkest
    # Since higher value (1) is generally interpreted as "more intense" or "darker" in data, 
    # and Viridis is perceptually uniform, we will use the following categorization:
    if normalized >= 0.8:
        return "🔥 High Value (Yellow/Lightest)"
    elif normalized >= 0.6:
        return "🟡 Upper Mid-tone"
    elif normalized >= 0.4:
        return "🟢 Mid-tone"
    elif normalized >= 0.2:
        return "🔵 Lower Mid-tone"
    else:
        return "🌑 Low Value (Deep Purple/Darkest)"

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
    
    # Calculate min/max for color hint function
    min_val = df_clean[variable].min()
    max_val = df_clean[variable].max()

    # ============================================================
    # Choropleth
    # ============================================================
    st.subheader(f"Map Visualization of **{variable}**")
    
    # Set up a dynamic subtitle/caption for the plot
    caption_text = (
        f"**Color Interpretation:** High values (yellow/lightest) peak at **{max_row['country']}** "
        f"(Value: {max_row[variable]:.2f}), and low values (deep purple/darkest) bottom out at **{min_row['country']}** "
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
    # 3. Full Country Color and Name List (Below Plot)
    # ============================================================
    st.markdown("---")
    st.header("📋 Full Country Value and Color Guide")
    st.markdown(
        """
        The table below provides the **country name** and its **corresponding value** for the variable, 
        sorted by magnitude. The **Color Intensity** column offers a quick visual cue, 
        linking the value to its shade on the map (using the **Viridis** scale).
        """
    )

    # Add the color intensity column
    df_sorted['Color Intensity'] = df_sorted[variable].apply(
        lambda x: get_color_intensity(x, min_val, max_val)
    )

    # Display the full list in the main area
    st.dataframe(
        df_sorted[['country', variable, 'Color Intensity']].rename(
            columns={'country': 'Country Name', variable: 'Value'}
        ),
        use_container_width=True,
        hide_index=True
    )
    st.markdown("---")

    # ============================================================
    # 4. Clearer Interpretation (Research Article Perspective)
    # ============================================================
    st.header("🔍 Research Article Interpretation")
    
    st.markdown("### Discussion/Results Section Summary")
    
    st.markdown(
        f"""
        The choropleth map provides compelling evidence regarding the spatial distribution of **{variable}**. 
        From a research standpoint, the color gradation—where **lighter tones (yellow) correlate with higher values** and **darker tones (purple) with lower values**—reveals distinct regional clusters. 
        
        * **Maximum Observation:** The highest value for **{variable}** is observed in **{max_row['Country Name']}** (Value: {max_row['Value']:.2f}).
        * **Minimum Observation:** The lowest value is observed in **{min_row['Country Name']}** (Value: {min_row['Value']:.2f}).
        
        Further statistical analysis (e.g., spatial autocorrelation or regression) is warranted to test for significant regional dependencies and to formally assess the drivers of the observed high-value clusters.
        """
    )
