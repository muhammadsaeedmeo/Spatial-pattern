# Spatial pattern map for a variable (e.g., Green Finance) across countries
# Requirements: geopandas, matplotlib, pandas

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt

# -------------------------------------------------------------
# 1. Load world shapefile
# -------------------------------------------------------------
world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))

# -------------------------------------------------------------
# 2. Example dataset: Replace with your actual data
# Your CSV should have: Country, GF
# Example:
# Country,GF
# China,12.5
# India,4.3
# United States,15.8
# -------------------------------------------------------------
# df = pd.read_csv("your_data.csv")

# Example toy data
example_data = {
    "Country": ["China", "India", "United States", "Brazil", "France", "Australia", "South Africa"],
    "GF": [12.5, 4.3, 15.8, 7.1, 9.5, 5.2, 3.4]
}

df = pd.DataFrame(example_data)

# -------------------------------------------------------------
# 3. Merge shapefile with data
# -------------------------------------------------------------
merged = world.merge(df, left_on="name", right_on="Country", how="left")

# -------------------------------------------------------------
# 4. Plot
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(12, 6))
merged.plot(column="GF", cmap="viridis", linewidth=0.8, ax=ax, edgecolor="0.8", legend=True)

ax.set_title("Spatial Pattern of Green Finance Across Countries", fontsize=14)
ax.axis("off")

plt.tight_layout()
plt.show()

# --- SPATIAL MAP GENERATOR FOR G7 COUNTRIES ---

import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

st.title("Spatial Pattern of Variables for G7 Countries")

uploaded = st.file_uploader("Upload CSV or Excel with columns: Country, Value", type=["csv", "xlsx", "xls"])

if uploaded:
    if uploaded.name.endswith("csv"):
        df = pd.read_csv(uploaded)
    else:
        df = pd.read_excel(uploaded)

    required = {"Country", "Value"}
    if not required.issubset(df.columns):
        st.error("Dataset must contain columns: Country, Value")
    else:
        world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))

        g7 = [
            "United States of America", "Canada", "United Kingdom", "France",
            "Germany", "Italy", "Japan"
        ]

        df["Country"] = df["Country"].replace({
            "US": "United States of America",
            "U.S": "United States of America",
            "UK": "United Kingdom",
            "U.K": "United Kingdom",
            "England": "United Kingdom"
        })

        merged = world.merge(df, how="left", left_on="name", right_on="Country")
        merged = merged[merged["name"].isin(g7)]

        fig, ax = plt.subplots(1, 1, figsize=(10, 6))
        merged.plot(
            column="Value",
            cmap="autumn_r",
            legend=True,
            linewidth=0.5,
            edgecolor="black",
            ax=ax
        )
        ax.set_title("Spatial Pattern Across G7 Countries", fontsize=16)
        ax.axis("off")

        st.pyplot(fig)
