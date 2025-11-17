import streamlit as st
import pandas as pd
import pycountry
import plotly.express as px
import plotly.graph_objects as go
import unicodedata

# ============================================================
# PASSWORD PROTECTION
# ============================================================
def check_password():
    """Returns `True` if the user has entered the correct password."""
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == "1992":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password
        st.text_input(
            "Enter Password to Access", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        st.info("Please enter the password to access the application.")
        return False
    elif not st.session_state["password_correct"]:
        # Password incorrect, show input + error
        st.text_input(
            "Enter Password to Access", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        st.error("😕 Password incorrect. Please try again.")
        return False
    else:
        # Password correct
        return True

if not check_password():
    st.stop()

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
st.title("🌍 Professional Choropleth Map for Country-Level Analysis")
st.markdown("---")

file = st.file_uploader("📁 Upload CSV or Excel file with a 'country' column", type=['csv', 'xlsx', 'xls'])

if file:
    # Load file
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)
    
    # Basic validation
    if "country" not in df.columns:
        st.error("❌ Dataset must contain a 'country' column.")
        st.stop()
    
    # Resolve ISO3
    df["iso3"] = df["country"].apply(normalize_country)
    unresolved = df[df["iso3"].isna()]["country"].unique().tolist()
    if unresolved:
        st.warning(f"⚠️ Unrecognized country names: {unresolved}")
    
    # Drop rows without valid ISO3
    df_clean = df.dropna(subset=["iso3"])
    
    # Select numeric variable
    numeric_cols = df_clean.select_dtypes(include=["float64", "int64"]).columns.tolist()
    
    col1, col2 = st.columns([3, 1])
    with col1:
        variable = st.selectbox("📊 Select variable to map:", numeric_cols)
    with col2:
        color_scale = st.selectbox("🎨 Color Scale:", 
                                   ["Viridis", "Inferno", "Plasma", "Blues", "Reds", "YlOrRd", "RdYlGn"])
    
    # ============================================================
    # Enhanced Choropleth with Legend
    # ============================================================
    fig = px.choropleth(
        df_clean,
        locations="iso3",
        color=variable,
        hover_name="country",
        hover_data={variable: ':.2f', 'iso3': False},
        projection="natural earth",
        color_continuous_scale=color_scale,
        labels={variable: variable.replace('_', ' ').title()}
    )
    
    # Enhanced styling for professional look
    fig.update_geos(
        showcountries=True,
        countrycolor="rgba(0,0,0,0.3)",
        showcoastlines=True,
        coastlinecolor="rgba(100,100,100,0.5)",
        showland=True,
        landcolor="rgba(243,243,243,0.8)",
        showocean=True,
        oceancolor="rgba(230,245,255,0.8)",
        projection_type="natural earth"
    )
    
    # Update layout for HD quality and professional appearance
    fig.update_layout(
        height=700,
        margin=dict(l=0, r=0, t=50, b=0),
        font=dict(family="Arial, sans-serif", size=14, color="#2c3e50"),
        title=dict(
            text=f"<b>Global Distribution of {variable.replace('_', ' ').title()}</b>",
            x=0.5,
            xanchor='center',
            font=dict(size=20, color="#2c3e50")
        ),
        coloraxis_colorbar=dict(
            title=dict(
                text=variable.replace('_', ' ').title(),
                font=dict(size=14, color="#2c3e50")
            ),
            thickness=20,
            len=0.7,
            x=1.02,
            tickfont=dict(size=12, color="#2c3e50"),
            outlinewidth=1,
            outlinecolor="rgba(0,0,0,0.2)"
        ),
        paper_bgcolor='white',
        plot_bgcolor='white'
    )
    
    # ============================================================
    # Add Legend Inside Plot at Bottom
    # ============================================================
    # Sort by variable value for legend
    df_sorted = df_clean.sort_values(by=variable, ascending=False).reset_index(drop=True)
    
    # Create color mapping
    min_val = df_sorted[variable].min()
    max_val = df_sorted[variable].max()
    
    import plotly.colors as pc
    colors = pc.sample_colorscale(color_scale, 
                                  [(val - min_val) / (max_val - min_val) 
                                   for val in df_sorted[variable]])
    
    # Create legend text with colors
    legend_items = []
    for idx, row in df_sorted.iterrows():
        legend_items.append(f"<span style='color:{colors[idx]}'>●</span> {row['country']} ({row[variable]:.2f})")
    
    # Split into multiple lines if too many countries
    items_per_line = 6
    legend_lines = []
    for i in range(0, len(legend_items), items_per_line):
        legend_lines.append(" | ".join(legend_items[i:i+items_per_line]))
    
    legend_text = "<br>".join(legend_lines)
    
    # Add annotation at bottom of plot for legend
    fig.add_annotation(
        text=f"<b>Country Legend:</b><br>{legend_text}",
        xref="paper", yref="paper",
        x=0.5, y=-0.15,
        xanchor="center", yanchor="top",
        showarrow=False,
        font=dict(size=10, color="#2c3e50"),
        align="center",
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor="#ccc",
        borderwidth=1,
        borderpad=10
    )
    
    # Adjust layout to accommodate legend
    fig.update_layout(
        margin=dict(l=0, r=0, t=50, b=150)  # Increased bottom margin for legend
    )
    
    # Display the main map
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True, 'displaylogo': False})
    
    # ============================================================
    # Statistical Summary
    # ============================================================
    st.markdown("---")
    st.subheader("📈 Statistical Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Maximum", f"{df_clean[variable].max():.2f}", 
                 delta=None, delta_color="normal")
    with col2:
        st.metric("Mean", f"{df_clean[variable].mean():.2f}", 
                 delta=None, delta_color="normal")
    with col3:
        st.metric("Median", f"{df_clean[variable].median():.2f}", 
                 delta=None, delta_color="normal")
    with col4:
        st.metric("Minimum", f"{df_clean[variable].min():.2f}", 
                 delta=None, delta_color="normal")
    
    # ============================================================
    # Detailed Interpretation for All Countries
    # ============================================================
    st.markdown("---")
    st.subheader("🔍 Detailed Country-by-Country Interpretation")
    
    # Sort by variable value
    df_sorted = df_clean.sort_values(by=variable, ascending=False).reset_index(drop=True)
    
    # Create comprehensive interpretation
    interpretation_lines = []
    
    # Highest contributor
    max_row = df_sorted.iloc[0]
    interpretation_lines.append(
        f"**{max_row['country']}** leads with the highest value of **{max_row[variable]:.2f}**, "
        f"representing the strongest performance in {variable.replace('_', ' ')} among all countries analyzed."
    )
    
    # High contributors (2nd to 25th percentile if exists)
    high_threshold = int(len(df_sorted) * 0.25)
    if len(df_sorted) > 1 and high_threshold > 1:
        high_countries = df_sorted.iloc[1:high_threshold]
        if len(high_countries) > 0:
            high_names = ", ".join([f"**{row['country']}** ({row[variable]:.2f})" 
                                   for _, row in high_countries.iterrows()])
            interpretation_lines.append(
                f"Following closely, {high_names} demonstrate high levels of {variable.replace('_', ' ')}, "
                f"indicating strong performance in this metric."
            )
    
    # Medium contributors (25th to 75th percentile)
    medium_start = high_threshold
    medium_end = int(len(df_sorted) * 0.75)
    if medium_end > medium_start:
        medium_countries = df_sorted.iloc[medium_start:medium_end]
        if len(medium_countries) > 0:
            medium_names = ", ".join([f"**{row['country']}** ({row[variable]:.2f})" 
                                     for _, row in medium_countries.iterrows()])
            interpretation_lines.append(
                f"In the moderate range, {medium_names} show average levels of {variable.replace('_', ' ')}, "
                f"maintaining steady performance."
            )
    
    # Low contributors (75th percentile to second-last)
    if medium_end < len(df_sorted) - 1:
        low_countries = df_sorted.iloc[medium_end:-1]
        if len(low_countries) > 0:
            low_names = ", ".join([f"**{row['country']}** ({row[variable]:.2f})" 
                                  for _, row in low_countries.iterrows()])
            interpretation_lines.append(
                f"Towards the lower end, {low_names} exhibit relatively lower values of {variable.replace('_', ' ')}, "
                f"suggesting areas for potential improvement."
            )
    
    # Lowest contributor
    min_row = df_sorted.iloc[-1]
    interpretation_lines.append(
        f"Finally, **{min_row['country']}** records the lowest value at **{min_row[variable]:.2f}**, "
        f"indicating the weakest performance in {variable.replace('_', ' ')} among the countries studied."
    )
    
    # Display interpretation
    for line in interpretation_lines:
        st.markdown(line)
        st.markdown("")  # Add spacing
    
    # Additional interpretation
    st.markdown(
        f"""
        **Color Scale Interpretation:**  
        The color gradient represents the magnitude of **{variable.replace('_', ' ').title()}**.  
        - **Darker/warmer tones** → Higher values  
        - **Lighter/cooler tones** → Lower values  
        
        Hover over any country on the map to see detailed values.
        """
    )
    
    # Download option
    st.markdown("---")
    csv = df_clean.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Processed Data",
        data=csv,
        file_name=f"{variable}_country_data.csv",
        mime="text/csv",
    )

else:
    st.info("👆 Please upload a CSV or Excel file to get started.")
    st.markdown("""
    ### Requirements:
    - File must contain a **'country'** column
    - At least one numeric variable for mapping
    - Supported formats: CSV, XLSX, XLS
    """)
