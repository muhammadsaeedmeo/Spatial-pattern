import streamlit as st
import pandas as pd
import pycountry
import plotly.express as px
import plotly.graph_objects as go
import unicodedata
import numpy as np
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
    
    clean = unicodedata.normalize("NFKD", str(name)).strip()
    clean = clean.replace("\u200b", "").replace("\uFEFF", "").replace("\xa0", " ")
    clean = " ".join(clean.split())
    
    clean_lower = clean.lower()
    
    # Try exact pycountry lookup
    try:
        country = pycountry.countries.lookup(clean)
        return country.alpha_3, country.alpha_2, country.name
    except:
        pass
    
    # Fuzzy matching with all country names
    best_match = None
    best_score = 0
    
    for country in pycountry.countries:
        score = fuzz.ratio(clean_lower, country.name.lower())
        if score > best_score:
            best_score = score
            best_match = country
        
        if hasattr(country, 'common_name'):
            score = fuzz.ratio(clean_lower, country.common_name.lower())
            if score > best_score:
                best_score = score
                best_match = country
    
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
# DATA CLEANING FUNCTION
# ============================================================
def clean_numeric_data(df, variable):
    """Ensure numeric data is properly formatted"""
    df_clean = df.copy()
    
    # Convert variable to numeric, handling errors
    df_clean[variable] = pd.to_numeric(df_clean[variable], errors='coerce')
    
    # Remove any infinite values
    df_clean = df_clean[~df_clean[variable].isin([np.inf, -np.inf])]
    
    # Remove NaN values in the variable
    df_clean = df_clean.dropna(subset=[variable])
    
    return df_clean

# ============================================================
# SIMPLE AGGREGATION FUNCTIONS
# ============================================================
def simple_aggregate_data(df, variable, aggregation_method):
    """
    Simple and reliable aggregation
    """
    st.write("🔍 **DEBUG: Starting aggregation**")
    st.write(f"Data shape: {df.shape}")
    st.write(f"Variable: {variable}")
    st.write(f"Method: {aggregation_method}")
    
    # Show sample of raw data
    st.write("**Sample of raw data:**")
    st.dataframe(df[['country', variable]].head(10))
    
    if aggregation_method == "Total Sum":
        # Simple groupby and sum
        result = df.groupby('country')[variable].sum().reset_index()
        result = result.rename(columns={variable: f'{variable}_total'})
        st.write("**DEBUG: After aggregation**")
        st.dataframe(result.head(10))
        return result, f'{variable}_total'
    
    elif aggregation_method == "Average":
        result = df.groupby('country')[variable].mean().reset_index()
        result = result.rename(columns={variable: f'{variable}_avg'})
        return result, f'{variable}_avg'
    
    elif aggregation_method == "Maximum Value":
        result = df.groupby('country')[variable].max().reset_index()
        result = result.rename(columns={variable: f'{variable}_max'})
        return result, f'{variable}_max'
    
    elif aggregation_method == "Latest Year":
        time_col = [col for col in df.columns if col.lower() in ['year', 'time', 'date', 'period']][0]
        result = df.loc[df.groupby('country')[time_col].idxmax()].reset_index(drop=True)
        return result, variable

# ============================================================
# MANUAL CALCULATION VERIFICATION
# ============================================================
def manual_calculation_check(df, variable, country_name="France"):
    """
    Manual calculation to verify results
    """
    country_data = df[df['country'] == country_name]
    
    if country_data.empty:
        return f"No data found for {country_name}", pd.DataFrame()
    
    # Manual calculations
    manual_sum = country_data[variable].sum()
    manual_avg = country_data[variable].mean()
    manual_max = country_data[variable].max()
    manual_min = country_data[variable].min()
    count_years = len(country_data)
    
    # Show detailed breakdown
    detailed_data = country_data[['year', variable]].copy() if 'year' in country_data.columns else country_data[[variable]].copy()
    detailed_data = detailed_data.sort_values('year' if 'year' in detailed_data.columns else variable)
    
    result_text = f"""
    **MANUAL CALCULATION FOR {country_name.upper()}**
    
    **Raw Values:**
    {detailed_data.to_string(index=False)}
    
    **Calculations:**
    - Sum: {manual_sum:,.2f}
    - Average: {manual_avg:,.2f} 
    - Maximum: {manual_max:,.2f}
    - Minimum: {manual_min:,.2f}
    - Count: {count_years} years
    
    **Formula:** Sum = {manual_sum:,.2f} / Count = {manual_avg:,.2f}
    """
    
    return result_text, detailed_data

# ============================================================
# MAIN APP
# ============================================================
if check_password():
    st.title("🗺️ Academic Spatial Distribution Analysis")
    st.markdown("### **DEBUG VERSION - Calculation Verification**")
    
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

        # Check for country column
        country_col = None
        for col in df.columns:
            if col.lower() == 'country':
                country_col = col
                break
        
        if not country_col:
            st.error("❌ Dataset must contain a 'country' column.")
            st.stop()

        if country_col != 'country':
            df = df.rename(columns={country_col: 'country'})

        st.success(f"✅ Loaded {len(df)} observations")
        
        # Show data overview
        st.markdown("### 📊 Data Overview")
        st.write(f"Columns: {list(df.columns)}")
        st.write(f"Data types: {df.dtypes.to_dict()}")
        st.dataframe(df.head(10))

        # Check if panel data
        time_cols = [col for col in df.columns if col.lower() in ['year', 'time', 'date', 'period']]
        is_panel = len(time_cols) > 0
        
        # Select variable
        numeric_cols = df.select_dtypes(include=["float64", "int64"]).columns.tolist()
        if not numeric_cols:
            st.error("❌ No numeric variables found.")
            st.stop()

        variable = st.selectbox("📊 Select variable to analyze:", numeric_cols)
        
        # Clean data
        df = clean_numeric_data(df, variable)
        st.write(f"✅ Data cleaned. Remaining observations: {len(df)}")
        
        # MANUAL CALCULATION SECTION
        st.markdown("---")
        st.markdown("### 🔍 MANUAL CALCULATION VERIFICATION")
        
        selected_country = st.selectbox("Select country to verify:", df['country'].unique())
        
        manual_result, raw_data = manual_calculation_check(df, variable, selected_country)
        st.text_area("Manual Calculation Results:", manual_result, height=400)
        
        if not raw_data.empty:
            st.write("**Detailed Data:**")
            st.dataframe(raw_data)

        # AGGREGATION METHOD
        st.markdown("---")
        st.markdown("### 📈 Aggregation Method")
        
        if is_panel:
            time_col = time_cols[0]
            st.info(f"📊 Panel data detected (Time variable: **{time_col}**)")
            
            aggregation_method = st.radio(
                "Choose aggregation method:",
                ["Total Sum", "Average", "Maximum Value", "Latest Year"]
            )
            
            # Perform aggregation
            with st.spinner("Calculating..."):
                df_aggregated, display_variable = simple_aggregate_data(df, variable, aggregation_method)
        else:
            aggregation_method = "Single Period"
            display_variable = variable
            df_aggregated = df.copy()

        # Normalize countries
        with st.spinner("Normalizing country names..."):
            df_aggregated[['iso3', 'iso2_label', 'country_name_official']] = df_aggregated["country"].apply(
                lambda x: pd.Series(normalize_country(x))
            )
        
        df_clean = df_aggregated.dropna(subset=["iso3"]).copy()
        
        # Show aggregated results
        st.markdown("### 📋 AGGREGATED RESULTS")
        st.dataframe(df_clean[['country', 'country_name_official', display_variable]].head(20))
        
        # Verify France specifically
        if 'France' in df_clean['country'].values:
            france_final = df_clean[df_clean['country'] == 'France'][display_variable].iloc[0]
            st.warning(f"🚨 **FRANCE FINAL VALUE: {france_final:,.2f}**")
            
            # Compare with manual calculation
            france_manual_sum = df[df['country'] == 'France'][variable].sum()
            st.warning(f"🚨 **FRANCE MANUAL SUM: {france_manual_sum:,.2f}**")
            
            if abs(france_final - france_manual_sum) > 0.01:
                st.error(f"❌ **DISCREPANCY DETECTED! Difference: {france_final - france_manual_sum:,.2f}**")
            else:
                st.success("✅ Values match!")

        # Create visualization only if values are reasonable
        reasonable_threshold = 1000000  # Adjust based on your data scale
        
        if df_clean[display_variable].max() < reasonable_threshold:
            st.markdown("---")
            st.markdown("## 🌍 Choropleth Map")
            
            fig = px.choropleth(
                df_clean,
                locations="iso3",
                color=display_variable,
                hover_name="country_name_official",
                hover_data={display_variable: ':.2f'},
                projection="natural earth",
                color_continuous_scale="Viridis",
                labels={display_variable: f"{variable} ({aggregation_method})"}
            )

            fig.update_geos(showcountries=True, countrycolor="lightgray")
            fig.update_layout(height=600, margin=dict(l=0, r=0, t=50, b=0))

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("🚨 **VALUES TOO LARGE FOR VISUALIZATION - CHECK CALCULATIONS**")

        # Statistical Summary
        st.markdown("---")
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

        # Rankings
        st.markdown("### 🏆 Rankings")
        df_ranked = df_clean.sort_values(by=display_variable, ascending=False).reset_index(drop=True)
        df_ranked['Rank'] = range(1, len(df_ranked) + 1)
        
        display_df = df_ranked[['Rank', 'country_name_official', display_variable]].head(10)
        st.dataframe(display_df.style.format({display_variable: "{:,.2f}"}))

        # Footer
        st.markdown("---")
        st.markdown(
            "<div style='text-align: center; color: gray; font-size: 12px;'>"
            "DEBUG VERSION - Calculation Verification Tool"
            "</div>",
            unsafe_allow_html=True
        )
