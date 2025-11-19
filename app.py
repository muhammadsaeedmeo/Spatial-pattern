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
# AGGREGATION FUNCTIONS
# ============================================================
def aggregate_data(df, variable, aggregation_method):
    """
    Aggregate data based on selected method
    """
    if aggregation_method == "Total Sum":
        aggregated = df.groupby('country', as_index=False).agg({
            variable: 'sum',
        })
        # Get the first occurrence of each country for additional info
        first_occurrence = df.groupby('country').first().reset_index()
        aggregated = pd.merge(aggregated, first_occurrence[['country']], on='country', how='left')
        aggregated.rename(columns={variable: f'{variable}_total'}, inplace=True)
        return aggregated, f'{variable}_total'
    
    elif aggregation_method == "Average":
        aggregated = df.groupby('country', as_index=False).agg({
            variable: 'mean',
        })
        first_occurrence = df.groupby('country').first().reset_index()
        aggregated = pd.merge(aggregated, first_occurrence[['country']], on='country', how='left')
        aggregated.rename(columns={variable: f'{variable}_avg'}, inplace=True)
        return aggregated, f'{variable}_avg'
    
    elif aggregation_method == "Maximum Value":
        aggregated = df.groupby('country', as_index=False).agg({
            variable: 'max',
        })
        first_occurrence = df.groupby('country').first().reset_index()
        aggregated = pd.merge(aggregated, first_occurrence[['country']], on='country', how='left')
        aggregated.rename(columns={variable: f'{variable}_max'}, inplace=True)
        return aggregated, f'{variable}_max'
    
    elif aggregation_method == "Latest Year":
        # Get the most recent year for each country
        time_col = [col for col in df.columns if col.lower() in ['year', 'time', 'date', 'period']][0]
        latest_years = df.groupby('country')[time_col].max().reset_index()
        aggregated = pd.merge(latest_years, df, on=['country', time_col], how='left')
        return aggregated, variable

# ============================================================
# MAIN APP
# ============================================================
if check_password():
    st.title("🗺️ Academic Spatial Distribution Analysis")
    st.markdown("### Professional Choropleth Mapping with Aggregate Analysis")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        show_labels = st.checkbox("Show country labels on map", value=False)
        if show_labels:
            label_color = st.color_picker("Label color:", "#FFFFFF")
            label_size = st.slider("Label size:", 6, 14, 8)
        
        st.markdown("---")
        st.markdown("**Tips:**")
        st.markdown("- Use aggregate analysis for cumulative metrics like investments")
        st.markdown("- Total Sum shows overall performance across all years")
        st.markdown("- Average shows consistent performance over time")
    
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
        
        # Select variable FIRST for all cases
        numeric_cols = df.select_dtypes(include=["float64", "int64"]).columns.tolist()
        numeric_cols = [col for col in numeric_cols if col not in ['iso3', 'iso2_label']]

        if not numeric_cols:
            st.error("❌ No numeric variables found for mapping.")
            st.stop()

        variable = st.selectbox("📊 Select variable to visualize:", numeric_cols)
        
        if is_panel:
            time_col = time_cols[0]
            st.info(f"📊 Panel data detected (Time variable: **{time_col}**)")
            
            # Show data summary
            year_range = f"{df[time_col].min()} to {df[time_col].max()}"
            st.write(f"**Time period:** {year_range} ({len(df[time_col].unique())} periods)")
            
            # AGGREGATION METHOD SELECTION
            st.markdown("### 📈 Aggregation Method")
            aggregation_method = st.radio(
                "Choose how to aggregate data across time:",
                ["Total Sum", "Average", "Maximum Value", "Latest Year"],
                help="""**Total Sum**: Cumulative total across all years (best for investments)
                       **Average**: Mean value per year
                       **Maximum Value**: Highest value achieved
                       **Latest Year**: Most recent year only"""
            )
            
            # Aggregate data based on selected method
            with st.spinner(f"🔄 Calculating {aggregation_method.lower()} for {variable}..."):
                df_aggregated, display_variable = aggregate_data(df, variable, aggregation_method)
                
            # Normalize countries on aggregated data
            with st.spinner("🔍 Normalizing country names..."):
                df_aggregated[['iso3', 'iso2_label', 'country_name_official']] = df_aggregated["country"].apply(
                    lambda x: pd.Series(normalize_country(x))
                )
            
            df_clean = df_aggregated.dropna(subset=["iso3"]).copy()
            
        else:
            # Cross-sectional data
            aggregation_method = "Single Period"
            display_variable = variable
            df_clean = df.copy()
            
            # Normalize countries
            with st.spinner("🔍 Normalizing country names..."):
                df_clean[['iso3', 'iso2_label', 'country_name_official']] = df_clean["country"].apply(
                    lambda x: pd.Series(normalize_country(x))
                )
            df_clean = df_clean.dropna(subset=["iso3"]).copy()

        # Check unresolved countries
        unresolved = df_clean[df_clean["iso3"].isna()]["country"].unique().tolist()
        if unresolved:
            with st.expander(f"⚠️ {len(unresolved)} Unrecognized Countries - Click to View"):
                st.warning("The following countries could not be matched:")
                for country in unresolved:
                    st.write(f"- {country}")
                st.info("💡 Tip: Check spelling or use standard country names")

        if df_clean.empty:
            st.error("No valid countries found after normalization.")
            st.stop()

        st.success(f"✅ Mapped {len(df_clean)} countries successfully")

        # Color scheme selection
        color_schemes = ['Viridis', 'Plasma', 'Inferno', 'Magma', 'Blues', 'Reds', 'YlOrRd', 'RdYlGn']
        color_scheme = st.selectbox("🎨 Color scheme:", color_schemes, index=2)

        st.markdown("---")

        # ============================================================
        # CHOROPLETH MAP
        # ============================================================
        st.markdown("## 🌍 Choropleth Map")
        
        # Create appropriate title based on aggregation method
        if is_panel:
            if aggregation_method == "Total Sum":
                title_suffix = f" - Cumulative Total ({df[time_col].min()}-{df[time_col].max()})"
            elif aggregation_method == "Average":
                title_suffix = f" - Annual Average ({df[time_col].min()}-{df[time_col].max()})"
            elif aggregation_method == "Maximum Value":
                title_suffix = f" - Peak Value ({df[time_col].min()}-{df[time_col].max()})"
            else:
                title_suffix = f" - Latest Year"
        else:
            title_suffix = ""
        
        fig = px.choropleth(
            df_clean,
            locations="iso3",
            color=display_variable,
            hover_name="country_name_official",
            hover_data={
                display_variable: ':.2f',
                'iso3': False,
            },
            projection="natural earth",
            color_continuous_scale=color_scheme,
            labels={display_variable: f"{variable.replace('_', ' ').title()} ({aggregation_method})"}
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
                'text': f'{variable.replace("_", " ").title()}{title_suffix}',
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
            st.metric("Mean", f"{df_clean[display_variable].mean():.2f}")
        with col2:
            st.metric("Median", f"{df_clean[display_variable].median():.2f}")
        with col3:
            st.metric("Std Dev", f"{df_clean[display_variable].std():.2f}")
        with col4:
            st.metric("Countries", len(df_clean))

        # ============================================================
        # INTERPRETATION
        # ============================================================
        st.markdown("## 💡 Academic Interpretation")
        
        if not df_clean.empty:
            max_row = df_clean.loc[df_clean[display_variable].idxmax()]
            min_row = df_clean.loc[df_clean[display_variable].idxmin()]

            if aggregation_method == "Total Sum":
                interpretation = f"""
                **Cumulative Performance Analysis:**
                
                The cumulative {variable.replace('_', ' ')} across all periods reveals long-term performance.
                **{max_row['country_name_official']}** leads with total {display_variable.split('_')[1]} of {max_row[display_variable]:.2f}, 
                while **{min_row['country_name_official']}** shows the lowest cumulative value ({min_row[display_variable]:.2f}). 
                This represents a {((max_row[display_variable] - min_row[display_variable]) / max_row[display_variable] * 100):.1f}% 
                difference between the highest and lowest performing countries.
                """
            elif aggregation_method == "Average":
                interpretation = f"""
                **Consistent Performance Analysis:**
                
                The average annual {variable.replace('_', ' ')} indicates consistent performance over time.
                **{max_row['country_name_official']}** demonstrates the highest average of {max_row[display_variable]:.2f} per period,
                while **{min_row['country_name_official']}** shows the lowest average ({min_row[display_variable]:.2f}). 
                This {((max_row[display_variable] - min_row[display_variable]) / max_row[display_variable] * 100):.1f}% 
                performance gap highlights significant disparities in sustained output.
                """
            elif aggregation_method == "Maximum Value":
                interpretation = f"""
                **Peak Performance Analysis:**
                
                The maximum achieved {variable.replace('_', ' ')} reveals peak capacity across countries.
                **{max_row['country_name_official']}** reached the highest single-period value of {max_row[display_variable]:.2f},
                while **{min_row['country_name_official']}** peaked at {min_row[display_variable]:.2f}. 
                The {((max_row[display_variable] - min_row[display_variable]) / max_row[display_variable] * 100):.1f}% 
                difference in peak performance indicates varying maximum capacities.
                """
            else:
                interpretation = f"""
                **Current Status Analysis:**
                
                The latest available data for {variable.replace('_', ' ')} shows current standings.
                **{max_row['country_name_official']}** leads with {max_row[display_variable]:.2f}, 
                while **{min_row['country_name_official']}** shows {min_row[display_variable]:.2f}. 
                This {((max_row[display_variable] - min_row[display_variable]) / max_row[display_variable] * 100):.1f}% 
                gap represents the current performance differential.
                """
            
            st.markdown(interpretation)

        # ============================================================
        # COMPLETE RANKINGS TABLE
        # ============================================================
        st.markdown("### 🏆 Complete Country Rankings")
        
        # Create complete ranking
        df_ranked = df_clean.sort_values(by=display_variable, ascending=False).reset_index(drop=True)
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
        display_df = df_display[['Rank', 'country_name_official', display_variable, 'iso2_label']].copy()
        display_df.columns = ['Rank', 'Country', f"{variable.replace('_', ' ').title()} ({aggregation_method})", 'ISO Code']
        display_df[display_df.columns[2]] = display_df[display_df.columns[2]].round(3)
        
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
        **Table Summary:** Showing {len(df_display)} of {len(df_ranked)} countries ranked by {variable.replace('_', ' ')} ({aggregation_method.lower()}).
        """)

        # Show bottom 5 in an expander
        if len(df_ranked) > 10:
            with st.expander("📉 View Bottom 5 Countries"):
                df_bottom = df_ranked.tail(5).copy()
                bottom_display = df_bottom[['Rank', 'country_name_official', display_variable, 'iso2_label']].copy()
                bottom_display.columns = ['Rank', 'Country', f"{variable.replace('_', ' ').title()} ({aggregation_method})", 'ISO Code']
                bottom_display[bottom_display.columns[2]] = bottom_display[bottom_display.columns[2]].round(3)
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
                x=display_variable,
                orientation='h',
                color=display_variable,
                color_continuous_scale=color_scheme,
                labels={display_variable: f"{variable.replace('_', ' ').title()} ({aggregation_method})",
                       'country_name_official': 'Country'},
                text=display_variable
            )
            
            fig_bar.update_traces(texttemplate='%{text:.2f}', textposition='outside')
            fig_bar.update_layout(
                yaxis={'categoryorder': 'total ascending'},
                height=max(400, n_bars * 30),
                showlegend=False,
                title={'text': f'Top {n_bars} Countries by {variable.replace("_", " ").title()} ({aggregation_method})',
                      'x': 0.5, 'xanchor': 'center'},
                xaxis_title=f"{variable.replace('_', ' ').title()} ({aggregation_method})",
                yaxis_title=''
            )
            
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with tab2:
            # Distribution histogram
            fig_hist = px.histogram(
                df_ranked,
                x=display_variable,
                nbins=30,
                color_discrete_sequence=['#636EFA'],
                labels={display_variable: f"{variable.replace('_', ' ').title()} ({aggregation_method})"}
            )
            
            fig_hist.update_layout(
                title={'text': f'Distribution of {variable.replace("_", " ").title()} ({aggregation_method}) Across Countries',
                      'x': 0.5, 'xanchor': 'center'},
                xaxis_title=f"{variable.replace('_', ' ').title()} ({aggregation_method})",
                yaxis_title='Frequency (Number of Countries)',
                height=400,
                showlegend=False
            )
            
            # Add vertical lines for mean and median
            mean_val = df_ranked[display_variable].mean()
            median_val = df_ranked[display_variable].median()
            
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
                file_name=f"spatial_data_{variable}_{aggregation_method.replace(' ', '_')}.csv",
                mime="text/csv"
            )
        
        with col2:
            # Download rankings (complete)
            ranking_csv = df_ranked[['Rank', 'country_name_official', display_variable, 'iso2_label']].to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Complete Rankings (CSV)",
                data=ranking_csv,
                file_name=f"complete_rankings_{variable}_{aggregation_method.replace(' ', '_')}.csv",
                mime="text/csv"
            )

        # Footer
        st.markdown("---")
        st.markdown(
            "<div style='text-align: center; color: gray; font-size: 12px;'>"
            "Academic Spatial Distribution Analysis Tool | Version 2.1"
            "</div>",
            unsafe_allow_html=True
        )
