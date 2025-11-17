import streamlit as st
import pandas as pd
import pycountry
import plotly.express as px
import unicodedata

# Set the correct password
CORRECT_PASSWORD = "1992"

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
# PASSWORD CHECK FUNCTION
# ============================================================
def check_password():
    """Returns True if the user enters the correct password, False otherwise."""
    st.title("Choropleth Map Access")
    
    # Use st.empty to hold the password input, allowing for clean removal/replacement
    password_placeholder = st.empty()
    
    # Password input field
    password = password_placeholder.text_input(
        "Enter password to access the app:", 
        type="password", 
        key="password_input"
    )
    
    if password == CORRECT_PASSWORD:
        # Clear the password input and message on successful login
        password_placeholder.empty()
        return True
    elif password: # Only show error if the user has actually typed something and it's wrong
        st.error("🚨 Incorrect password.")
    
    return False

# ============================================================
# STREAMLIT APP LOGIC (Only runs if password is correct)
# ============================================================
if check_password():
    st.title("🗺️ Choropleth Map for Country-Level Variables")
    
    # Use st.sidebar for file uploader to keep the main content clean initially
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
        
        if not numeric_cols:
            st.error("No numeric columns found to map.")
            st.stop()
            
        variable = st.selectbox("Select variable to map:", numeric_cols)

        # Color picker for country name labels for visibility
        label_color = st.color_picker("Select country label color:", "#FFFFFF")

        # ---
        
        ## 🌍 Choropleth Map

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

        # Country text labels
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

        # ---
        
        ## 💡 Interpretation

        # ============================================================
        # Automatic one-line interpretation
        # ============================================================
        if not df_clean.empty:
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
