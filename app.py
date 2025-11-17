import streamlit as st
import pandas as pd
import pycountry
import plotly.express as px
import unicodedata

# Set the correct password
CORRECT_PASSWORD = "1992"

# ============================================================
# ISO NORMALIZATION + Turkey override
# Returns alpha_3, alpha_2, and official country name
# ============================================================
def normalize_country(name: str):
    """
    Cleans and standardizes country names. 
    Returns a tuple: (alpha_3 code for map, alpha_2 code for labels, official country name).
    """
    # 1. Standardize and clean the input string
    clean = unicodedata.normalize("NFKD", str(name)).strip()
    clean = clean.replace("\u200b", "").replace("\uFEFF", "")
    clean = clean.replace("\xa0", " ")
    clean = clean.strip()
    
    # 2. Hard override for specific names
    if clean.lower() in ["turkey", "türkiye", "turkiye"]:
        return "TUR", "TR", "Turkey"
        
    # 3. Use pycountry to look up standard codes
    try:
        country = pycountry.countries.lookup(clean)
        # Return alpha_3, alpha_2, and the official name
        return country.alpha_3, country.alpha_2, country.name
    except:
        return None, None, None

# ============================================================
# PASSWORD CHECK FUNCTION
# ============================================================
def check_password():
    """Returns True if the user enters the correct password, False otherwise."""
    st.title("🔐 Spatial Distribution Pattern Access")
    
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
    st.title("🗺️ Spatial Distribution Pattern")
    
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

        # Resolve ISO3, ISO2, and Full Name
        # Apply the function and unpack the tuple results into three new columns
        df[['iso3', 'iso2_label', 'country_name_official']] = df["country"].apply(
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

        st.markdown("---") 
        
        st.markdown("## 🌍 Choropleth Map Display")

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

        # Country text labels (using the new 'iso2_label' column for shorter text)
        for _, row in df_clean.iterrows():
            fig.add_scattergeo(
                locations=[row["iso3"]],
                # Use the short ISO-2 code for the on-map text
                text=row["iso2_label"], 
                mode="text",
                textposition="middle center",
                textfont=dict(color=label_color, size=10),
                showlegend=False
            )

        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---") 
        
        ## 💡 Interpretation and Legend
        
        # ============================================================
        # 1. Automatic one-line interpretation (Highest and Lowest)
        # ============================================================
        st.markdown("## 💡 Interpretation")
        
        if not df_clean.empty and variable in df_clean.columns:
            # Find max and min
            max_row = df_clean.loc[df_clean[variable].idxmax()]
            min_row = df_clean.loc[df_clean[variable].idxmin()]

            auto_note = (
                f"**Highest/Lowest:** {max_row['country']} exhibits the **highest** level of **{variable}**, "
                f"while {min_row['country']} shows the **lowest** value among the countries."
            )

            st.markdown(f"**Overall Summary:** {auto_note}")

        # ============================================================
        # 2. Top N Interpretation (New Feature)
        # ============================================================
            st.markdown("### Top 5 Spatial Distribution")
            
            # Sort the data by the variable in descending order
            df_ranked = df_clean.sort_values(by=variable, ascending=False).reset_index(drop=True)
            df_top_5 = df_ranked.head(5).copy()
            
            # Add rank column
            df_top_5['Rank'] = df_top_5.index + 1
            
            # Display the top 5 countries and their values
            top_list = []
            for _, row in df_top_5.iterrows():
                # Format the value to 2 decimal places if it's a float
                val = f"{row[variable]:,.2f}" if isinstance(row[variable], float) else row[variable]
                top_list.append(f"**Rank {row['Rank']}:** {row['country']} ({val})")
                
            st.markdown("\n".join(top_list))

        # ============================================================
        # 3. Interpretation note for the color scale
        # ============================================================
        st.markdown("---")
        st.markdown("### Color Scale Note")
        st.markdown(
            f"""
            The color scale reflects the magnitude of **{variable}**.  
            **Darker tones** (closer to yellow/white) indicate **higher values**, whereas **lighter tones** (closer to black/purple) indicate **lower values** in the 'Inferno' color scale.  
            """
        )

        st.markdown("---") 

        # ============================================================
        # Country Code Legend (New Line Format)
        # ============================================================
        st.markdown("## 🗺️ Country Code Legend (Copy-Pasteable)")
        st.markdown("This legend translates the **2-Letter Codes** displayed on the map to the full country name.")
        
        # Create a clean DataFrame for the legend
        legend_df = df_clean[["iso2_label", "country_name_official"]].drop_duplicates(subset=["iso2_label"]).sort_values(by="country_name_official")
        
        # Generate the text block
        legend_text = []
        for _, row in legend_df.iterrows():
            legend_text.append(f"{row['iso2_label']}: {row['country_name_official']}")
            
        # Display the text in a code block for easy copy-pasting
        st.code("\n".join(legend_text), language="")
