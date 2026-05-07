import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import branca.colormap as cm
import numpy as np
from folium.plugins import Fullscreen
import base64
import os
import plotly.express as px

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(layout="wide", page_title="Crop Yield Dashboard")

# -------------------------------------------------
# FORCE DARK THEME
# -------------------------------------------------
st.markdown("""
<style>

/* Main app */
.stApp {
    background-color: #0e1117;
    color: white;
}

/* Main page */
[data-testid="stAppViewContainer"] {
    background-color: #0e1117;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #111827 !important;
}

/* Sidebar labels/text */
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] div {
    color: #f9fafb !important;
}

/* Sidebar title */
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: white !important;
}

/* Selectbox */
.stSelectbox div[data-baseweb="select"] {
    background-color: #1f2937 !important;
    color: white !important;
    border-radius: 8px;
}

/* Selected dropdown text */
.stSelectbox div[data-baseweb="select"] span {
    color: white !important;
}

/* Dropdown menu */
div[role="listbox"] {
    background-color: #1f2937 !important;
}

/* Dropdown option text */
div[role="option"] {
    color: white !important;
}

/* Checkbox */
.stCheckbox label {
    color: white !important;
}

/* Metric cards */
.metric-card,
.trend-wrapper,
.trend-metric-card {
    background-color: #1f2937 !important;
    border: 1px solid #374151 !important;
}

/* Metric labels */
.metric-label,
.trend-metric-label,
.trend-subtitle {
    color: #d1d5db !important;
}

/* Metric values */
.metric-value,
.trend-metric-value,
.trend-title {
    color: white !important;
}

/* Alerts */
[data-testid="stAlert"] {
    background-color: #1f2937 !important;
    color: white !important;
}

/* Toolbar */
header {
    background-color: #0e1117 !important;
}

[data-testid="stToolbar"] {
    background-color: #0e1117 !important;
}

/* Padding */
.block-container {
    padding-top: 0.35rem;
}

</style>
""", unsafe_allow_html=True)

# Reduce the default top padding of Streamlit to make the banner sit better
st.markdown("""
    <style>
    .block-container {
        padding-top: 0.35rem;
    }
    </style>
    """, unsafe_allow_html=True)

# -------------------------------------------------
# HEADER (BANNER WITH BACKGROUND)
# -------------------------------------------------
def get_base64_img(file_path):
    if os.path.isfile(file_path):
        with open(file_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return ""

# Load assets for the banner
bg_b64 = get_base64_img("bg.png")
logo_b64 = get_base64_img("logo.png")

banner_html = f"""
<div style="
    position: relative; 
    background-image: linear-gradient(rgba(255,255,255,0.75), rgba(255,255,255,0.75)), url('data:image/png;base64,{bg_b64}'); 
    background-size: 110%; /* Fills the taller container */
    background-position: center top; 
    padding: 60px 40px; /* Greatly increased top/bottom padding for height */
    border-radius: 5px; 
    display: flex; 
    align-items: center; /* This centers everything vertically */
    justify-content: space-between; 
    border-bottom: 3px solid #3d85c6;
    margin-bottom: 8px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
    
    <img src="data:image/png;base64,{logo_b64}" style="width: 100px; height: auto;">
    
    <div style="text-align: center; flex-grow: 1;">
        <h1 style="
            margin: 0; 
            font-family: 'Rockwell', 'Courier Bold', serif; 
            font-size: 42px; 
            border-bottom: none; 
            line-height: 1.1;
            letter-spacing: 1px;">
            <span style="color: #3194eb; font-weight: 700;">Hydro</span><span style="color: #0b5394; font-weight: 400;">-</span><span style="color: #ff9900; font-weight: 700;">S</span><span style="color: #0b5394; font-weight: 400;">ocio-</span><span style="color: #6aa84f; font-weight: 700;">E</span><span style="color: #0b5394; font-weight: 400;">co </span><span style="color: #3d85c6; font-weight: 700;">L</span><span style="color: #0b5394; font-weight: 400;">ab</span>
        </h1>
        <h2 style="
            margin: 8px 0 0 0; /* Slight increase in space between titles */
            font-family: 'Rockwell', serif; 
            font-size: 34px; 
            font-weight: 400; 
            color: #0b5394;
            border-bottom: none;">
            (<span style="color: #3194eb;">H</span>ydro-<span style="color: #ff9900;">S</span><span style="color: #6aa84f;">E</span><span style="color: #3d85c6;">L</span>)
        </h2>
    </div>

    <img src="data:image/png;base64,{logo_b64}" style="width: 100px; height: auto;">
</div>
"""


# Render the banner using st.html (or st.markdown fallback)
try:
    st.html(banner_html)
except AttributeError:
    st.markdown(banner_html, unsafe_allow_html=True)

# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------
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

# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
st.sidebar.title("India Crop Yield Dashboard")

apply_filters = st.sidebar.checkbox("Apply Filters")

year = st.sidebar.selectbox("Year", sorted(df["Crop_Year"].unique()))
crop = st.sidebar.selectbox("Crop", sorted(df["Crop"].unique()))
season = st.sidebar.selectbox("Season", sorted(df["Season"].unique()))

st.sidebar.markdown("---")

map_style = st.sidebar.selectbox(
    "Map Style",
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

# -------------------------------------------------
# LOAD SHAPEFILE
# -------------------------------------------------
@st.cache_resource
def load_shapefile():
    gdf = gpd.read_file("DISTRICT_BOUNDARY_small.shp")
    gdf = gdf.to_crs(epsg=4326)
    gdf["DISTRICT"] = gdf["DISTRICT"].str.strip().str.upper()
    gdf["geometry"] = gdf["geometry"].simplify(0.02)
    return gdf

gdf = load_shapefile()

# -------------------------------------------------
# DEFAULT MAP
# -------------------------------------------------
m = folium.Map(
    location=[22.5, 80],
    zoom_start=5,
    tiles=map_tiles[map_style],
    attr="Map Data",
    control_scale=True
)

# -------------------------------------------------
# APPLY FILTERS
# -------------------------------------------------
if apply_filters:

    filtered = df[
        (df["Crop_Year"] == year) &
        (df["Crop"] == crop) &
        (df["Season"] == season)
    ]

    map_df = gdf.merge(
        filtered,
        left_on="DISTRICT",
        right_on="District_Name",
        how="inner"
    )

    districts_count = len(map_df)
    avg_yield = round(map_df["Yield"].mean(), 2) if len(map_df) > 0 else 0
    max_yield = round(map_df["Yield"].max(), 2) if len(map_df) > 0 else 0

    st.markdown("""
        <style>
        .metric-card {
            background-color: #fdfdfd; 
            border: 1px solid #eeeeee;
            padding: 8px 14px;
            border-radius: 10px;
            border-left: 6px solid #3194eb;
            text-align: left;
            margin-bottom: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }
        .metric-label {
            font-size: 13px;
            color: #555555;
            margin-bottom: 4px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .metric-value {
            font-size: 24px;
            font-weight: 700;
            color: #0b5394;
            font-family: 'Rockwell', 'Courier Bold', serif;
            line-height: 1.2;
        }
        </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">Districts</div>
            <div class="metric-value">{districts_count}</div>
        </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown(f"""<div class="metric-card" style="border-left-color: #6aa84f;">
            <div class="metric-label">Average Yield (t/ha)</div>
            <div class="metric-value">{avg_yield}</div>
        </div>""", unsafe_allow_html=True)

    with col3:
        st.markdown(f"""<div class="metric-card" style="border-left-color: #ff9900;">
            <div class="metric-label">Max Yield (t/ha)</div>
            <div class="metric-value">{max_yield}</div>
        </div>""", unsafe_allow_html=True)

    if map_df.empty:
        st.warning("No data available for selected filters")
    else:
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
                    <span style="color:black;">0–25th pct  (< {round(p25, 2)} t/ha)</span>
                </div>
                <div style="display:flex; align-items:center; margin-bottom:5px;">
                    <div style="width:20px;height:14px;background:#d9f0a3;border:1px solid #ccc;margin-right:8px;flex-shrink:0;"></div>
                    <span style="color:black;">25–50th pct  ({round(p25, 2)} – {round(p50, 2)} t/ha)</span>
                </div>
                <div style="display:flex; align-items:center; margin-bottom:5px;">
                    <div style="width:20px;height:14px;background:#78c679;border:1px solid #ccc;margin-right:8px;flex-shrink:0;"></div>
                    <span style="color:black;">50–75th pct  ({round(p50, 2)} – {round(p75, 2)} t/ha)</span>
                </div>
                <div style="display:flex; align-items:center; margin-bottom:5px;">
                    <div style="width:20px;height:14px;background:#238443;border:1px solid #ccc;margin-right:8px;flex-shrink:0;"></div>
                    <span style="color:black;">75–95th pct  ({round(p75, 2)} – {round(p95, 2)} t/ha)</span>
                </div>
                <div style="display:flex; align-items:center;">
                    <div style="width:20px;height:14px;background:#005a32;border:1px solid #ccc;margin-right:8px;flex-shrink:0;"></div>
                    <span style="color:black;">> 95th pct  ({round(p95, 2)}+ t/ha)</span>
                </div>
            </div>
            <div style="margin-top:8px; font-size:10px; color:#888;">
                Outliers capped at 95th percentile
            </div>
        </div>
        """
        m.get_root().html.add_child(folium.Element(legend_html))

# -------------------------------------------------
# MAP CONTROLS
# -------------------------------------------------
# DISPLAY MAP & HANDLE INTERACTIONS
# -------------------------------------------------
map_output = st_folium(
    m,
    width=None,
    height=430,
    key="india_map"
)

# TREND CHART SECTION (Triggers when a district is clicked)
if apply_filters and map_output and map_output.get("last_active_drawing"):

    clicked_district = map_output["last_active_drawing"]["properties"].get("DISTRICT")

    if clicked_district:

        st.markdown("""
        <style>

        .trend-wrapper {
            background: #ffffff;
            border-radius: 14px;
            padding: 12px;
            margin-top: 8px;
            margin-bottom: 8px;
            border: 1px solid #e8e8e8;
            box-shadow: 0 4px 14px rgba(0,0,0,0.06);
        }

        .trend-title {
            font-size: 20px;
            font-weight: 700;
            color: #0b5394;
            font-family: 'Rockwell', serif;
            margin-bottom: 4px;
        }

        .trend-subtitle {
            font-size: 14px;
            color: #666666;
            margin-bottom: 8px;
        }

        .trend-metric-card {
            background-color: #fdfdfd;
            border: 1px solid #eeeeee;
            padding: 8px 14px;
            border-radius: 10px;
            border-left: 6px solid #3194eb;
            text-align: left;
            margin-bottom: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }

        .trend-metric-label {
            font-size: 13px;
            color: #555555;
            margin-bottom: 4px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .trend-metric-value {
            font-size: 20px;
            font-weight: 700;
            color: #0b5394;
            font-family: 'Rockwell', serif;
            line-height: 1.2;
        }

        </style>
        """, unsafe_allow_html=True)

        trend_df = df[
            (df["District_Name"] == clicked_district) &
            (df["Crop"] == crop) &
            (df["Season"] == season)
        ].sort_values("Crop_Year")

        if not trend_df.empty:

            st.markdown('<div class="trend-wrapper">', unsafe_allow_html=True)

            st.markdown(
                f"""
                <div class="trend-subtitle">
                    Yield Trend
                </div>

                <div class="trend-subtitle">
                    {clicked_district.title()} • {crop} • {season}
                </div>
                """,
                unsafe_allow_html=True
            )

            fig = px.line(
                trend_df,
                x="Crop_Year",
                y="Yield",
                markers=True,
                labels={
                    "Crop_Year": "Year",
                    "Yield": "Yield (tonnes/ha)"
                },
                template="plotly_dark",
                color_discrete_sequence=["#4da3ff"]
            )

            fig.update_traces(
                line=dict(
                    width=2.8,
                    color="#4da3ff"
                ),
                marker=dict(
                    size=13,
                    color="#4da3ff",
                    line=dict(
                        width=2.5,
                        color="white"
                    )
                ),
                hovertemplate=
                "<b>Year:</b> %{x}<br>" +
                "<b>Yield:</b> %{y:.2f} t/ha<extra></extra>"
            )

            fig.update_layout(
                hovermode="x unified",
                height=290,
                paper_bgcolor="#111827",
                plot_bgcolor="#111827",
                margin=dict(
                    l=20,
                    r=20,
                    t=10,
                    b=20
                ),
                font=dict(
                    family="Arial",
                    size=14,
                    color="white"
                ),
                xaxis=dict(
                    tickmode='linear',
                    dtick=1,
                    showgrid=False,
                    title_font=dict(
                        size=16,
                        color="white"
                    ),
                    tickfont=dict(
                        size=13,
                        color="white"
                    ),
                    linecolor="white"
                ),
                yaxis=dict(
                    title="Yield (t/ha)",
                    showgrid=True,
                    gridcolor="rgba(255,255,255,0.10)",
                    zeroline=False,
                    title_font=dict(
                        size=16,
                        color="white"
                    ),
                    tickfont=dict(
                        size=13,
                        color="white"
                    ),
                    linecolor="white"
                ),
                hoverlabel=dict(
                    bgcolor="#1f2937",
                    font_size=11,
                    font_color="white"
                )
            )

            avg_val = round(trend_df["Yield"].mean(), 2)
            max_val = round(trend_df["Yield"].max(), 2)
            
            t_col1, t_col2, t_col3 = st.columns(3)

            with t_col1:
                st.markdown(f"""
                <div class="trend-metric-card">
                    <div class="trend-metric-label">District</div>
                    <div class="trend-metric-value" style="font-size:24px;">
                        {clicked_district.title()}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with t_col2:
                st.markdown(f"""
                <div class="trend-metric-card"
                     style="border-left-color:#6aa84f;">
                    <div class="trend-metric-label">
                        15-Year Avg Yield
                    </div>
                    <div class="trend-metric-value">
                        {avg_val}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with t_col3:
                st.markdown(f"""
                <div class="trend-metric-card"
                     style="border-left-color:#ff9900;">
                    <div class="trend-metric-label">
                        Peak Yield
                    </div>
                    <div class="trend-metric-value">
                        {max_val}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.plotly_chart(fig, use_container_width=True)
            st.markdown("""
<style>

/* Remove empty container generated after chart */
.element-container:has(.js-plotly-plot) + div:empty {
    display: none !important;
}

/* Remove blank vertical block */
div[data-testid="stVerticalBlock"] div:empty {
    display: none !important;
    margin: 0 !important;
    padding: 0 !important;
}

</style>
""", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        else:
            st.info(
                f"No historical trend data found for "
                f"**{clicked_district.title()}** with the selected Crop/Season."
            )

else:
    if apply_filters:
        st.markdown(
            "<p style='color:#9ca3af; text-align:center; margin-top:8px;'>"
            "👆 Click on a district on the map to view its 15-year yield trend."
            "</p>",
            unsafe_allow_html=True
        )
