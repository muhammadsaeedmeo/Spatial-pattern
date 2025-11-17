import streamlit as st
import pandas as pd
import pycountry
import plotly.express as px
import unicodedata
import altair as alt # Added for the custom legend

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

    # Color picker for country name labels for visibility
    label_color = st.color_picker("Select country label color:", "#FFFFFF")
    
    # ============================================================
    # Choropleth (with HD/Fine-Tune adjustments)
    # ============================================================
    st.subheader(f"Map Visualization of **{variable}**")
    
    fig = px.choropleth(
        df_clean,
        locations="iso3",
        color=variable,
        hover_name="country",
        projection="natural earth",
        # --- 2. HD/Fine-Tune: Changed color scale and template ---
        color_continuous_scale="Viridis", # Perceptually uniform for better quality
        template="plotly_white", # Clean, high-contrast background
        height=600, # Increased height for better visibility
    )

    fig.update_geos(
        showcountries=True,
        countrycolor="black",
        showcoastlines=True,
        coastlinecolor="gray",
        # Added outline to ocean for a cleaner look
        oceancolor="aliceblue"
    )

    # Country text labels
    for _, row in df_clean.iterrows():
        fig.add_scattergeo(
            locations=[row["iso3"]],
            text=row["country"],
            mode="text",
            textposition="middle center",
            textfont=dict(color=label_color, size=10, family='Arial'), # Adjusted font size/family
            showlegend=False
        )

    st.plotly_chart(fig, use_container_width=True)
    
    # ============================================================
    # 3. Country-Color Legend
    # ============================================================
    st.sidebar.header("Country Color Legend")
    st.sidebar.markdown(f"**Color represents the value of: {variable}**")

    # Create a small scatter plot in sidebar to act as a legend
    # Altair is often clearer for custom legends
    chart_legend = alt.Chart(df_clean).mark_point().encode(
        y=alt.Y('country', title="Country"),
        color=alt.Color(variable, scale=alt.Scale(range=px.colors.sequential.Viridis)),
        tooltip=['country', variable]
    ).properties(height=200).interactive()
    
    st.sidebar.altair_chart(chart_legend, use_container_width=True)
    
    # Also provide a simplified list for quick reference
    df_sorted = df_clean.sort_values(by=variable, ascending=False).reset_index(drop=True)
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
    
    # --- Automatic Interpretation ---
    max_row = df_clean.loc[df_clean[variable].idxmax()]
    min_row = df_clean.loc[df_clean[variable].idxmin()]
    
    st.markdown("### Geographical Distribution Summary")
    st.info(
        f"The visualization clearly indicates a significant geographical disparity in **{variable}**. "
        f"**{max_row['country']}** (Value: **{max_row[variable]:.2f}**) exhibits the highest concentration or level of this variable, "
        f"represented by the **darkest shade** on the map. "
        f"Conversely, **{min_row['country']}** (Value: **{min_row[variable]:.2f}**) records the lowest value, "
        f"marked by the **lightest shade**, highlighting a crucial point of minimum observation in the dataset."
    )
    
    # --- Research Article Perspective ---
    st.markdown("### Research Article Perspective (Discussion/Results Section)")
    
    st.markdown(
        """
        The choropleth map provides compelling evidence regarding the spatial distribution of **{variable}**. 
        From a research standpoint, the color gradation—where **darker tones correlate with higher values** and **lighter tones with lower values**—reveals distinct regional clusters. 
        
        * **Hypothesis Generation:** The strong visual contrast between the maximum and minimum values (e.g., between {max_row['country']} and {min_row['country']}) suggests that geographical, economic, or policy factors may be significantly driving the variance in **{variable}**. 
        * **Future Work:** Further statistical analysis (e.g., spatial autocorrelation or regression) is warranted to test for significant regional dependencies and to formally assess the drivers of the observed high-value clusters.
        """
    )
    
    st.markdown(
        f"""
        ### Color Scale Guide  
        The color scale reflects the magnitude of **{variable}**. The scale used is **'Viridis'**, a perceptually uniform colormap:  
        * **Darker Tones:** Indicate **Higher Values** of **{variable}**.  
        * **Lighter Tones:** Indicate **Lower Values** of **{variable}**.  
        """
    )
