import streamlit as st
import pandas as pd
import pycountry
import plotly.express as px
import unicodedata

# Set the correct password
CORRECT_PASSWORD = "1992"

# ============================================================
# ISO NORMALIZATION + Turkey override
# Returns alpha_3 for mapping and alpha_2 for short labels
# ============================================================
def normalize_country(name: str):
    """
    Cleans and standardizes country names. 
    Returns a tuple: (alpha_3 code for map, alpha_2 code for labels).
    """
    clean = unicodedata.normalize("NFKD", str(name)).strip()
    clean = clean.replace("\u200b", "").replace("\uFEFF", "")
    clean = clean.replace("\xa0", " ")
    clean = clean.strip()
    
    # Check for hard override first
    if clean.lower() in ["turkey", "türkiye", "turkiye"]:
        return "TUR", "TR"
        
    try:
        country = pycountry.countries.lookup(clean)
        # Return both the 3-letter code (for location) and the 2-letter code (for text)
        return country.alpha_3, country.alpha_2
    except:
        return None, None

# ============================================================
# PASSWORD CHECK FUNCTION
# ============================================================
def check_password():
    """Returns True if the user enters the correct password, False otherwise."""
    st.title("🔐 Choropleth Map Access")
    
    password_placeholder = st.empty()
    
    password = password_placeholder.text_input(
        "Enter password to access the app:", 
        type="password", 
        key="password_input"
    )
    
    if password == CORRECT_PASSWORD:
        password_placeholder.empty()
        return True
    elif password:
        st.error("🚨 Incorrect password.")
    
    return False

# ============================================================
# STREAMLIT APP LOGIC
# ============================================================
if check_password():
    st.title("🗺️ Choropleth Map for Country-Level Variables")
    
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

        # Resolve ISO3 and ISO2
        # Apply the function and unpack the tuple results into two new columns
        df[['iso3', 'iso2_label']] = df["country"].apply(
            lambda x: pd.Series(normalize_country(x))
        )
        
        unresolved = df[df["iso3"].isna()]["country"].unique().tolist()

        if unresolved:
            st.warning(f"Unrecognized country names: {unresolved}")

        # Drop rows without valid ISO3
        df_clean = df.dropna(subset=["iso3"])

        # Select numeric variable
        numeric_cols = df_clean.select_dtypes(include=["float64", "int64"]).columns.tolist()
        
        if not numeric_cols:
            st.error("No numeric columns found to map.")
            st.stop()
            
        variable = st.selectbox("Select variable to map:", numeric_cols)

        # Color picker for country name labels for visibility
        label_color = st.color_picker("Select country label color:", "#FFFFFF")

        ---
        
        ## 🌍 Choropleth Map Display

        # ============================================================
        # Choropleth
        # ============================================================
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

        # Country text labels (using the new 'iso2_label' column)
        for _, row in df_clean.iterrows():
            fig.add_scattergeo(
                locations=[row["iso3"]],
                # Use the short ISO-2 code for the on-map text
                text=row["iso2_label"], 
                mode="text",
                textposition="middle center",
                textfont=dict(color=label_color, size=10), # Reduced font size for better fit
                showlegend=False
            )

        st.plotly_chart(fig, use_container_width=True)

        ---
        
        ## 💡 Interpretation

        # ============================================================
        # Automatic one-line interpretation
        # ============================================================
        if not df_clean.empty and variable in df_clean.columns:
            # Note: idxmax/idxmin might return the first max/min if duplicates exist
            max_row = df_clean.loc[df_clean[variable].idxmax()]
            min_row = df_clean.loc[df_clean[variable].idxmin()]

            auto_note = (
                f"{max_row['country']} exhibits the **highest** level of **{variable}**, "
                f"while {min_row['country']} shows the **lowest** value among the countries."
            )

            st.markdown(f"**Auto-Interpretation:** {auto_note}")

        # ============================================================
        # Interpretation note for the color scale
        # ============================================================
        st.markdown(
            f"""
            The color scale reflects the magnitude of **{variable}**.  
            **Darker tones** (closer to yellow/white) indicate **higher values**, whereas **lighter tones** (closer to black/purple) indicate **lower values** in the 'Inferno' color scale.  
            """
        )
