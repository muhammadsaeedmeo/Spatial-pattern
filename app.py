import streamlit as st
import pandas as pd
import pycountry
import plotly.express as px
import plotly.graph_objects as go
import unicodedata
from fuzzywuzzy import fuzz

# Set the correct password
CORRECT_PASSWORD = "1992"

# ============================================================
# ENHANCED COUNTRY NORMALIZATION WITH FUZZY MATCHING
# ============================================================
def normalize_country(name: str):
    """
    Enhanced country name normalization with fuzzy matching.
    Returns: (alpha_3, alpha_2, official_name)
    """
    if pd.isna(name) or str(name).strip() == "":
        return None, None, None
    
    # 1. Clean the input
    clean = unicodedata.normalize("NFKD", str(name)).strip()
    clean = clean.replace("\u200b", "").replace("\uFEFF", "").replace("\xa0", " ")
    clean = " ".join(clean.split())  # Remove extra whitespace
    
    # 2. Hard overrides for common variations
    overrides = {
        "turkey": "TUR", "türkiye": "TUR", "turkiye": "TUR",
        "usa": "USA", "us": "USA", "united states": "USA",
        "uk": "GBR", "united kingdom": "GBR", "britain": "GBR",
        "south korea": "KOR", "korea": "KOR", "rok": "KOR",
        "north korea": "PRK", "dprk": "PRK",
        "russia": "RUS", "russian federation": "RUS", "ussr": "RUS",
        "china": "CHN", "prc": "CHN",
        "vietnam": "VNM", "viet nam": "VNM",
        "czech republic": "CZE", "czechia": "CZE",
        "uae": "ARE", "united arab emirates": "ARE",
        "drc": "COD", "dr congo": "COD", "democratic republic of the congo": "COD",
        "congo": "COG", "republic of the congo": "COG",
        "ivory coast": "CIV", "cote d'ivoire": "CIV",
        "myanmar": "MMR", "burma": "MMR",
        "palestine": "PSE", "palestinian territory": "PSE",
        "tanzania": "TZA", "united republic of tanzania": "TZA",
        "bolivia": "BOL", "plurinational state of bolivia": "BOL",
        "venezuela": "VEN", "bolivarian republic of venezuela": "VEN",
        "iran": "IRN", "islamic republic of iran": "IRN",
        "syria": "SYR", "syrian arab republic": "SYR",
        "laos": "LAO", "lao people's democratic republic": "LAO",
        "moldova": "MDA", "republic of moldova": "MDA",
        "macedonia": "MKD", "north macedonia": "MKD",
        "netherlands": "NLD", "holland": "NLD",
        "swaziland": "SWZ", "eswatini": "SWZ"
    }
    
    clean_lower = clean.lower()
    if clean_lower in overrides:
        try:
            country = pycountry.countries.get(alpha_3=overrides[clean_lower])
            return country.alpha_3, country.alpha_2, country.name
        except:
            pass
    
    # 3. Try exact pycountry lookup
    try:
        country = pycountry.countries.lookup(clean)
        return country.alpha_3, country.alpha_2, country.name
    except:
        pass
    
    # 4. Fuzzy matching with all country names
    best_match = None
    best_score = 0
    
    for country in pycountry.countries:
        # Check official name
        score = fuzz.ratio(clean_lower, country.name.lower())
        if score > best_score:
            best_score = score
            best_match = country
        
        # Check common name if available
        if hasattr(country, 'common_name'):
            score = fuzz.ratio(clean_lower, country.common_name.lower())
            if score > best_score:
                best_score = score
                best_match = country
    
    # Accept matches with 80%+ similarity
    if best_match and best_score >= 80:
        return best_match.alpha_3, best_match.alpha_2, best_match.name
    
    return None, None, None

# ============================================================
# PASSWORD CHECK
# ============================================================
def check_password():
    """Password authentication."""
    st.title("🔐 Spatial Distribution Pattern Access")
    password = st.text_input("Enter password:", type="password", key="password_input")
    
    if password == CORRECT_PASSWORD:
        return True
    elif password:
        st.error("🚨 Incorrect password.")
    return False

# ============================================================
# MAIN APP
# ============================================================
if check_password():
    st.title("🗺️ Academic Spatial Distribution Analysis")
    st.markdown("### Professional Choropleth Mapping with Panel Data Support")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        show_labels = st.checkbox("Show country labels on map", value=False)
        if show_labels:
            label_color = st.color_picker("Label color:", "#FFFFFF")
            label_size = st.slider("Label size:", 6, 14, 8)
        
        st.markdown("---")
        st.markdown("**Tips:**")
        st.markdown("- For many countries, disable labels for cleaner view")
        st.markdown("- Use hover info to identify countries")
        st.markdown("- Panel data: each country-year appears once in rankings")
    
    file = st.file_uploader("📁 Upload CSV or Excel (must contain 'country' column)", 
                            type=['csv', 'xlsx', 'xls'])

    if file:
        # Load data
        try:
            if file.name.endswith(".csv"):
                df = pd.read_csv(file, encoding='utf-8')
            else:
                df = pd.read_excel(file)
        except Exception as e:
            st.error(f"Error loading file: {e}")
            st.stop()

        # Check for country column (case-insensitive)
        country_col = None
        for col in df.columns:
            if col.lower() == 'country':
                country_col = col
                break
        
        if not country_col:
            st.error("❌ Dataset must contain a 'country' column.")
            st.stop()

        # Normalize country column name
        if country_col != 'country':
            df = df.rename(columns={country_col: 'country'})

        st.success(f"✅ Loaded {len(df)} observations")

        # Check if panel data (has year/time column)
        time_cols = [col for col in df.columns if col.lower() in ['year', 'time', 'date', 'period']]
        is_panel = len(time_cols) > 0
        
        if is_panel:
            time_col = time_cols[0]
            st.info(f"📊 Panel data detected (Time variable: **{time_col}**)")
            
            # Time period selector
            unique_periods = sorted(df[time_col].unique())
            selected_period = st.selectbox(
                "Select time period to visualize:",
                unique_periods,
                index=len(unique_periods)-1  # Default to latest
            )
            
            # Filter data for selected period
            df_period = df[df[time_col] == selected_period].copy()
            st.write(f"Showing data for: **{selected_period}** ({len(df_period)} countries)")
        else:
            df_period = df.copy()

        # Normalize countries
        with st.spinner("🔍 Normalizing country names..."):
            df_period[['iso3', 'iso2_label', 'country_name_official']] = df_period["country"].apply(
                lambda x: pd.Series(normalize_country(x))
            )
        
        # Check unresolved countries
        unresolved = df_period[df_period["iso3"].isna()]["country"].unique().tolist()
        if unresolved:
            with st.expander(f"⚠️ {len(unresolved)} Unrecognized Countries - Click to View"):
                st.warning("The following countries could not be matched:")
                for country in unresolved:
                    st.write(f"- {country}")
                st.info("💡 Tip: Check spelling or use standard country names")

        # Drop unresolved
        df_clean = df_period.dropna(subset=["iso3"]).copy()
        
        if df_clean.empty:
            st.error("No valid countries found after normalization.")
            st.stop()

        st.success(f"✅ Mapped {len(df_clean)} countries successfully")

        # Select variable
        numeric_cols = df_clean.select_dtypes(include=["float64", "int64"]).columns.tolist()
        # Remove ISO columns from selection
        numeric_cols = [col for col in numeric_cols if col not in ['iso3', 'iso2_label']]
        
        if not numeric_cols:
            st.error("❌ No numeric variables found for mapping.")
            st.stop()
            
        variable = st.selectbox("📊 Select variable to visualize:", numeric_cols)

        # Color scheme selection
        color_schemes = ['Viridis', 'Plasma', 'Inferno', 'Magma', 'Blues', 'Reds', 'YlOrRd', 'RdYlGn']
        color_scheme = st.selectbox("🎨 Color scheme:", color_schemes, index=2)

        st.markdown("---")

        # ============================================================
        # CHOROPLETH MAP
        # ============================================================
        st.markdown("## 🌍 Choropleth Map")
        
        fig = px.choropleth(
            df_clean,
            locations="iso3",
            color=variable,
            hover_name="country_name_official",
            hover_data={
                variable: ':.2f',
                'iso3': False,
                'country': True
            },
            projection="natural earth",
            color_continuous_scale=color_scheme,
            labels={variable: variable.replace('_', ' ').title()}
        )

        fig.update_geos(
            showcountries=True,
            countrycolor="lightgray",
            showcoastlines=True,
            coastlinecolor="darkgray",
            bgcolor='#f0f2f6'
        )

        # Add country labels only if requested
        if show_labels:
            for _, row in df_clean.iterrows():
                fig.add_scattergeo(
                    locations=[row["iso3"]],
                    text=row["iso2_label"],
                    mode="text",
                    textfont=dict(color=label_color, size=label_size),
                    showlegend=False,
                    hoverinfo='skip'
                )

        fig.update_layout(
            title={
                'text': f'{variable.replace("_", " ").title()} - Spatial Distribution',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20}
            },
            height=600,
            margin=dict(l=0, r=0, t=50, b=0)
        )

        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # ============================================================
        # STATISTICAL SUMMARY
        # ============================================================
        st.markdown("## 📊 Statistical Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Mean", f"{df_clean[variable].mean():.2f}")
        with col2:
            st.metric("Median", f"{df_clean[variable].median():.2f}")
        with col3:
            st.metric("Std Dev", f"{df_clean[variable].std():.2f}")
        with col4:
            st.metric("Countries", len(df_clean))

        # ============================================================
        # INTERPRETATION
        # ============================================================
        st.markdown("## 💡 Academic Interpretation")
        
        if not df_clean.empty:
            max_row = df_clean.loc[df_clean[variable].idxmax()]
            min_row = df_clean.loc[df_clean[variable].idxmin()]

            st.markdown(f"""
            **Spatial Distribution Analysis:**
            
            The spatial distribution of **{variable.replace('_', ' ')}** reveals significant 
            cross-country variation. **{max_row['country_name_official']}** exhibits the highest 
            value ({max_row[variable]:.2f}), while **{min_row['country_name_official']}** 
            demonstrates the lowest ({min_row[variable]:.2f}). This {((max_row[variable] - min_row[variable]) / min_row[variable] * 100):.1f}% 
            differential suggests substantial heterogeneity across the geographic units analyzed.
            """)

        # ============================================================
        # COMPLETE RANKINGS TABLE (Panel-Aware)
        # ============================================================
        st.markdown("### 🏆 Complete Country Rankings")
        
        # For panel data, ensure unique countries in ranking
        if is_panel:
            st.info(f"📅 Rankings for {selected_period} (each country appears once)")
        
        # Create complete ranking
        df_ranked = df_clean.sort_values(by=variable, ascending=False).reset_index(drop=True)
        df_ranked['Rank'] = range(1, len(df_ranked) + 1)
        
        # Display options
        col1, col2 = st.columns([3, 1])
        with col1:
            show_option = st.radio(
                "Display:",
                ["Top 10", "Top 20", "All Countries"],
                horizontal=True,
                key="display_option"
            )
        with col2:
            highlight_top = st.checkbox("Highlight Top 3", value=True)
        
        # Determine how many to show
        if show_option == "Top 10":
            df_display = df_ranked.head(10).copy()
        elif show_option == "Top 20":
            df_display = df_ranked.head(20).copy()
        else:
            df_display = df_ranked.copy()
        
        # Create a clean table with formatting
        display_df = df_display[['Rank', 'country_name_official', variable, 'iso2_label']].copy()
        display_df.columns = ['Rank', 'Country', variable.replace('_', ' ').title(), 'ISO Code']
        display_df[variable.replace('_', ' ').title()] = display_df[variable.replace('_', ' ').title()].round(3)
        
        # Style the dataframe with highlighting
        def highlight_ranks(row):
            if highlight_top and row['Rank'] == 1:
                return ['background-color: #FFD700; font-weight: bold'] * len(row)  # Gold
            elif highlight_top and row['Rank'] == 2:
                return ['background-color: #C0C0C0; font-weight: bold'] * len(row)  # Silver
            elif highlight_top and row['Rank'] == 3:
                return ['background-color: #CD7F32; font-weight: bold'] * len(row)  # Bronze
            else:
                return [''] * len(row)
        
        styled_df = display_df.style.apply(highlight_ranks, axis=1)
        
        st.dataframe(styled_df, hide_index=True, use_container_width=True, height=400)
        
        # Summary stats below table
        st.markdown(f"""
        **Table Summary:** Showing {len(df_display)} of {len(df_ranked)} countries ranked by {variable.replace('_', ' ')}.
        """)
        
        # Show bottom 5 in an expander
        if len(df_ranked) > 10:
            with st.expander("📉 View Bottom 5 Countries"):
                df_bottom = df_ranked.tail(5).copy()
                bottom_display = df_bottom[['Rank', 'country_name_official', variable, 'iso2_label']].copy()
                bottom_display.columns = ['Rank', 'Country', variable.replace('_', ' ').title(), 'ISO Code']
                bottom_display[variable.replace('_', ' ').title()] = bottom_display[variable.replace('_', ' ').title()].round(3)
                st.dataframe(bottom_display, hide_index=True, use_container_width=True)

        # ============================================================
        # DUAL VIEW: VISUAL COMPARISON
        # ============================================================
        st.markdown("### 📊 Visual Comparison")
        
        # Create tabs for different visualizations
        tab1, tab2 = st.tabs(["📊 Horizontal Bar Chart", "📈 Distribution Plot"])
        
        with tab1:
            # Horizontal bar chart for top countries
            n_bars = min(15, len(df_ranked))
            df_for_bar = df_ranked.head(n_bars).copy()
            
            fig_bar = px.bar(
                df_for_bar,
                y='country_name_official',
                x=variable,
                orientation='h',
                color=variable,
                color_continuous_scale=color_scheme,
                labels={variable: variable.replace('_', ' ').title(),
                       'country_name_official': 'Country'},
                text=variable
            )
            
            fig_bar.update_traces(texttemplate='%{text:.2f}', textposition='outside')
            fig_bar.update_layout(
                yaxis={'categoryorder': 'total ascending'},
                height=max(400, n_bars * 30),
                showlegend=False,
                title={'text': f'Top {n_bars} Countries by {variable.replace("_", " ").title()}',
                      'x': 0.5, 'xanchor': 'center'},
                xaxis_title=variable.replace('_', ' ').title(),
                yaxis_title=''
            )
            
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with tab2:
            # Distribution histogram
            fig_hist = px.histogram(
                df_ranked,
                x=variable,
                nbins=30,
                color_discrete_sequence=['#636EFA'],
                labels={variable: variable.replace('_', ' ').title()}
            )
            
            fig_hist.update_layout(
                title={'text': f'Distribution of {variable.replace("_", " ").title()} Across Countries',
                      'x': 0.5, 'xanchor': 'center'},
                xaxis_title=variable.replace('_', ' ').title(),
                yaxis_title='Frequency (Number of Countries)',
                height=400,
                showlegend=False
            )
            
            # Add vertical lines for mean and median
            mean_val = df_ranked[variable].mean()
            median_val = df_ranked[variable].median()
            
            fig_hist.add_vline(x=mean_val, line_dash="dash", line_color="red", 
                              annotation_text=f"Mean: {mean_val:.2f}", 
                              annotation_position="top")
            fig_hist.add_vline(x=median_val, line_dash="dash", line_color="green", 
                              annotation_text=f"Median: {median_val:.2f}", 
                              annotation_position="bottom")
            
            st.plotly_chart(fig_hist, use_container_width=True)

        st.markdown("---")

        # ============================================================
        # COUNTRY CODE LEGEND
        # ============================================================
        with st.expander("🗺️ Country Code Reference Guide"):
            st.markdown("**ISO-2 to Country Name Mapping**")
            
            legend_df = df_clean[["iso2_label", "country_name_official"]].drop_duplicates(
                subset=["iso2_label"]
            ).sort_values(by="country_name_official")
            
            # Create multi-column layout for legend
            n_cols = 3
            cols = st.columns(n_cols)
            
            for idx, (_, row) in enumerate(legend_df.iterrows()):
                col_idx = idx % n_cols
                cols[col_idx].write(f"**{row['iso2_label']}**: {row['country_name_official']}")

        # ============================================================
        # DOWNLOAD OPTIONS
        # ============================================================
        st.markdown("---")
        st.markdown("### 💾 Download Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Download cleaned data
            csv = df_clean.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Cleaned Data (CSV)",
                data=csv,
                file_name=f"spatial_data_{variable}.csv",
                mime="text/csv"
            )
        
        with col2:
            # Download rankings (complete)
            ranking_csv = df_ranked[['Rank', 'country_name_official', variable, 'iso2_label']].to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Complete Rankings (CSV)",
                data=ranking_csv,
                file_name=f"complete_rankings_{variable}_{selected_period if is_panel else 'all'}.csv",
                mime="text/csv"
            )

        # Footer
        st.markdown("---")
        st.markdown(
            "<div style='text-align: center; color: gray; font-size: 12px;'>"
            "Academic Spatial Distribution Analysis Tool | Version 2.0"
            "</div>",
            unsafe_allow_html=True
        )
