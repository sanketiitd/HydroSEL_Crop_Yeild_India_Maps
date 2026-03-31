import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import branca.colormap as cm
import numpy as np

st.set_page_config(layout="wide")

st.title("🌾 India Crop Yield GIS Dashboard")

@st.cache_data
def load_crop_data():
    df = pd.read_csv("crop_climate_with_yield.csv")
    df = df[df["Area"] > 0]
    df["Yield"] = df["Production"] / df["Area"]
    df["Crop"] = df["Crop"].str.strip().str.title()
    df["Season"] = df["Season"].str.strip().str.title()
    df["District_Name"] = df["District_Name"].str.strip().str.upper()
    return df

df = load_crop_data()

st.sidebar.header("Map Filters")
year = st.sidebar.selectbox("Year", sorted(df["Crop_Year"].unique()))
crop = st.sidebar.selectbox("Crop", sorted(df["Crop"].unique()))
season = st.sidebar.selectbox("Season", sorted(df["Season"].unique()))

filtered = df[
    (df["Crop_Year"] == year) &
    (df["Crop"] == crop) &
    (df["Season"] == season)
]

st.sidebar.header("Map Style")
map_style = st.sidebar.selectbox(
    "Select Map Type",
    ["Street Map", "Light Map", "Dark Map", "Topographic", "Satellite", "Google Satellite"]
)

map_tiles = {
    "Street Map": "OpenStreetMap",
    "Light Map": "cartodbpositron",
    "Dark Map": "cartodbdark_matter",
    "Topographic": "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
    "Satellite": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    "Google Satellite": "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
}

@st.cache_resource
def load_shapefile():
    gdf = gpd.read_file("DISTRICT_BOUNDARY_small.shp")
    gdf = gdf.to_crs(epsg=4326)
    gdf["DISTRICT"] = gdf["DISTRICT"].str.strip().str.upper()
    gdf["geometry"] = gdf["geometry"].simplify(0.02)
    return gdf

gdf = load_shapefile()

map_df = gdf.merge(
    filtered,
    left_on="DISTRICT",
    right_on="District_Name",
    how="inner"
)

col1, col2, col3 = st.columns(3)
col1.metric("Districts", len(map_df))
col2.metric("Average Yield (t/ha)", round(map_df["Yield"].mean(), 2) if len(map_df) > 0 else 0)
col3.metric("Max Yield (t/ha)", round(map_df["Yield"].max(), 2) if len(map_df) > 0 else 0)

if map_df.empty:
    st.warning("No data available for selected filters")
    st.stop()

# -------------------------------------------------
# Percentile-based color scale (handles outliers)
# -------------------------------------------------
p0  = np.percentile(map_df["Yield"], 0)
p25 = np.percentile(map_df["Yield"], 25)
p50 = np.percentile(map_df["Yield"], 50)
p75 = np.percentile(map_df["Yield"], 75)
p95 = np.percentile(map_df["Yield"], 95)

colors = ["#ffffe5", "#d9f0a3", "#78c679", "#238443", "#005a32"]

colormap = cm.StepColormap(
    colors=colors,
    index=[p0, p25, p50, p75, p95],
    vmin=p0,
    vmax=p95
)

def get_color(yield_val):
    if yield_val is None:
        return "#d3d3d3"
    return colormap(min(yield_val, p95))

m = folium.Map(
    location=[22.5, 80],
    zoom_start=5,
    tiles=map_tiles[map_style],
    attr="Map Data",
    control_scale=True
)

folium.GeoJson(
    map_df,
    style_function=lambda feature: {
        "fillColor": get_color(feature["properties"]["Yield"]),
        "color": "white",
        "weight": 0.3,
        "fillOpacity": 0.8,
    },
    highlight_function=lambda x: {
        "fillColor": "#000000",
        "fillOpacity": 0.1,
        "color": "black",
        "weight": 1
    },
    tooltip=folium.GeoJsonTooltip(
        fields=["DISTRICT", "Yield", "Seasonal_Rainfall", "Seasonal_Temp"],
        aliases=["District:", "Yield (t/ha):", "Rainfall (mm):", "Temperature (°C):"],
        sticky=True
    )
).add_to(m)

# -------------------------------------------------
# Custom Legend with tonnes/hectare units
# -------------------------------------------------
legend_html = f"""
<div style="
    position: fixed;
    bottom: 90px;
    left: 10px;
    z-index: 9999;
    background-color: white;
    padding: 12px 16px;
    border-radius: 8px;
    box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
    font-family: Arial, sans-serif;
    font-size: 13px;
    min-width: 210px;
    color: black;
">
    <b style="font-size:14px; color:black;">Crop Yield</b>
    <span style="font-size:11px; color:#555; margin-left:4px;">(tonnes/hectare)</span><br>
    <span style="font-size:10px; color:#888;">(percentile scale)</span><br>
    <div style="margin-top:8px;">
        <div style="display:flex; align-items:center; margin-bottom:5px;">
            <div style="width:20px;height:14px;background:#ffffe5;border:1px solid #ccc;margin-right:8px;flex-shrink:0;"></div>
            <span style="color:black;">0–25th pct &nbsp;(&lt; {round(p25, 2)} t/ha)</span>
        </div>
        <div style="display:flex; align-items:center; margin-bottom:5px;">
            <div style="width:20px;height:14px;background:#d9f0a3;border:1px solid #ccc;margin-right:8px;flex-shrink:0;"></div>
            <span style="color:black;">25–50th pct &nbsp;({round(p25, 2)} – {round(p50, 2)} t/ha)</span>
        </div>
        <div style="display:flex; align-items:center; margin-bottom:5px;">
            <div style="width:20px;height:14px;background:#78c679;border:1px solid #ccc;margin-right:8px;flex-shrink:0;"></div>
            <span style="color:black;">50–75th pct &nbsp;({round(p50, 2)} – {round(p75, 2)} t/ha)</span>
        </div>
        <div style="display:flex; align-items:center; margin-bottom:5px;">
            <div style="width:20px;height:14px;background:#238443;border:1px solid #ccc;margin-right:8px;flex-shrink:0;"></div>
            <span style="color:black;">75–95th pct &nbsp;({round(p75, 2)} – {round(p95, 2)} t/ha)</span>
        </div>
        <div style="display:flex; align-items:center;">
            <div style="width:20px;height:14px;background:#005a32;border:1px solid #ccc;margin-right:8px;flex-shrink:0;"></div>
            <span style="color:black;">&gt; 95th pct &nbsp;({round(p95, 2)}+ t/ha)</span>
        </div>
    </div>
    <div style="margin-top:8px; font-size:10px; color:#888;">
        Outliers capped at 95th percentile
    </div>
</div>
"""

m.get_root().html.add_child(folium.Element(legend_html))

st_folium(m, width=1400, height=700)
