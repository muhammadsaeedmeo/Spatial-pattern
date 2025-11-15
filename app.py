import streamlit as st
import pandas as pd
import plotly.express as px
import pycountry

st.title("Spatial Pattern Mapper for Panel Variables")

uploaded = st.file_uploader(
    "Upload CSV or Excel with a 'Country' column and at least one numeric variable",
    type=["csv", "xlsx", "xls"]
)

def to_iso3(name):
    try:
        return pycountry.countries.lookup(name).alpha_3
    except:
        return None

if uploaded:
    # Load input
    if uploaded.name.endswith("csv"):
        df = pd.read_csv(uploaded)
    else:
        df = pd.read_excel(uploaded)

    st.write("### Data Preview")
    st.dataframe(df.head())

    # Clean country names
    df["Country"] = (
        df["Country"].astype(str)
        .str.strip()
        .str.replace(r"[.]", "", regex=True)
        .str.replace(r"\s+", " ", regex=True)
        .str.title()
    )

    # Convert to ISO3 dynamically
    df["ISO"] = df["Country"].apply(to_iso3)

    # Unmatched check
    missing = df[df["ISO"].isna()]
    if len(missing) > 0:
        st.error("These country names could not be recognized:")
        st.dataframe(missing)
        st.stop()

    # Let user select variable to map
    numeric_vars = df.select_dtypes(include="number").columns.tolist()
    if len(numeric_vars) == 0:
        st.error("No numeric variables found to plot.")
        st.stop()

    var = st.selectbox("Select variable to map", numeric_vars)

    # Plot
    fig = px.choropleth(
        df,
        locations="ISO",
        color=var,
        hover_name="Country",
        color_continuous_scale="YlOrRd",
        projection="natural earth",
        title=f"Spatial Pattern of {var}"
    )
    st.plotly_chart(fig, use_container_width=True)
