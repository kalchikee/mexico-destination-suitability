"""
Mexico Vacation Destination Suitability Analysis
Interactive Streamlit Dashboard
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import folium
from streamlit_folium import st_folium

from mcda import (
    load_data, compute_suitability, CRITERIA,
    DEFAULT_WEIGHTS, TRAVELER_PROFILES
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Mexico Destination Suitability",
    page_icon="🌮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    .main-title {font-size:2.2rem; font-weight:700; color:#1a1a2e;}
    .sub-title  {font-size:1rem;  color:#555; margin-top:-10px;}
    .metric-card {
        background:#f7f7f7; border-radius:10px; padding:14px 18px;
        border-left:4px solid #e63946;
    }
    [data-testid="stMetricValue"] {font-size:1.6rem !important;}
</style>
""", unsafe_allow_html=True)

DEST_COLORS = {
    "Cancún":           "#e63946",
    "Playa del Carmen": "#457b9d",
    "Tulum":            "#2a9d8f",
    "Puerto Vallarta":  "#e9c46a",
    "Los Cabos":        "#f4a261",
    "Mexico City":      "#264653",
    "Oaxaca":           "#8338ec",
}

CRITERION_LABELS = {k: v["label"] for k, v in CRITERIA.items()}

# ---------------------------------------------------------------------------
# Data load (cached)
# ---------------------------------------------------------------------------
@st.cache_data
def get_data():
    return load_data("data/destinations.csv")

df_raw = get_data()

# ---------------------------------------------------------------------------
# Sidebar — weight controls
# ---------------------------------------------------------------------------
st.sidebar.header("⚙️ Scenario Settings")

profile_choice = st.sidebar.selectbox(
    "Traveler Profile",
    ["Custom"] + list(TRAVELER_PROFILES.keys()),
    index=1,
)

if profile_choice != "Custom":
    preset = TRAVELER_PROFILES[profile_choice]
else:
    preset = DEFAULT_WEIGHTS

st.sidebar.markdown("**Criterion Weights** (must sum to 1.0)")

weight_inputs = {}
for key, label in CRITERION_LABELS.items():
    weight_inputs[key] = st.sidebar.slider(
        label, 0.0, 1.0, float(preset[key]), 0.05, key=f"w_{key}"
    )

total_w = sum(weight_inputs.values())
if abs(total_w - 1.0) > 0.01:
    st.sidebar.warning(f"Weights sum to {total_w:.2f} — will be auto-normalized.")
    norm_weights = {k: v / total_w for k, v in weight_inputs.items()}
else:
    norm_weights = weight_inputs

st.sidebar.markdown(f"**Sum: {total_w:.2f}**")

# ---------------------------------------------------------------------------
# Run MCDA
# ---------------------------------------------------------------------------
df_result = compute_suitability(df_raw, norm_weights)
score_cols = [f"score_{k}" for k in CRITERIA]

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown('<p class="main-title">Mexico Vacation Destination Suitability</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-title">GIS-based Multi-Criteria Decision Analysis · '
    'Seven major tourism centers evaluated across six spatial criteria</p>',
    unsafe_allow_html=True,
)
st.divider()

# ============================================================
# TAB LAYOUT
# ============================================================
tab_map, tab_rank, tab_radar, tab_scenarios, tab_data = st.tabs([
    "🗺️ Suitability Map",
    "🏆 Rankings",
    "📊 Criterion Profiles",
    "🔀 Scenario Comparison",
    "📋 Raw Data & Sources",
])

# ============================================================
# TAB 1 — MAP
# ============================================================
with tab_map:
    st.subheader("Spatial Suitability Index")
    st.caption(
        "Bubble size and color intensity represent composite suitability score. "
        "Click a marker for destination details."
    )

    m = folium.Map(
        location=[21.0, -97.5],
        zoom_start=6,
        tiles="CartoDB positron",
    )

    # Color scale: low=red, high=green
    def suit_color(score):
        r = int(230 * (1 - score))
        g = int(180 * score)
        b = 60
        return f"#{r:02x}{g:02x}{b:02x}"

    for dest, row in df_result.iterrows():
        score = row["suitability_index"]
        radius = 18 + score * 30

        popup_html = f"""
        <div style='font-family:sans-serif; min-width:200px'>
            <b style='font-size:1.1em'>{dest}</b><br>
            <hr style='margin:4px 0'>
            <b>Rank:</b> #{row['rank']}<br>
            <b>Suitability Index:</b> {score:.3f}<br>
            <hr style='margin:4px 0'>
            {''.join(
                f"<b>{CRITERION_LABELS[k]}:</b> {row[f'score_{k}']:.2f}<br>"
                for k in CRITERIA
            )}
        </div>
        """

        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=radius,
            color=suit_color(score),
            fill=True,
            fill_color=suit_color(score),
            fill_opacity=0.75,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{dest}  |  Score: {score:.3f}  |  Rank #{row['rank']}",
        ).add_to(m)

        folium.Marker(
            location=[row["lat"] + 0.35, row["lon"]],
            icon=folium.DivIcon(
                html=f'<div style="font-size:11px;font-weight:bold;color:#222;'
                     f'text-shadow:1px 1px 2px white">{dest}</div>',
                icon_size=(160, 20),
                icon_anchor=(0, 0),
            ),
        ).add_to(m)

    st_folium(m, width=None, height=520, returned_objects=[])

    # Legend
    cols = st.columns(len(df_result))
    for i, (dest, row) in enumerate(df_result.iterrows()):
        with cols[i]:
            st.metric(
                label=f"#{row['rank']} {dest}",
                value=f"{row['suitability_index']:.3f}",
            )

# ============================================================
# TAB 2 — RANKINGS BAR CHART
# ============================================================
with tab_rank:
    st.subheader("Composite Suitability Rankings")

    fig_bar = go.Figure()

    for k in CRITERIA:
        fig_bar.add_trace(go.Bar(
            name=CRITERION_LABELS[k],
            x=df_result.index.tolist(),
            y=(df_result[f"score_{k}"] * norm_weights[k]).round(4),
            hovertemplate="%{x}<br>" + CRITERION_LABELS[k] + ": %{y:.3f}<extra></extra>",
        ))

    fig_bar.update_layout(
        barmode="stack",
        title=f"Weighted Criterion Contributions — {profile_choice} Profile",
        xaxis_title="Destination",
        yaxis_title="Suitability Index (0–1)",
        legend_title="Criterion",
        height=480,
        template="plotly_white",
        yaxis_range=[0, 1],
    )

    st.plotly_chart(fig_bar, use_container_width=True)

    # Table
    tbl = df_result[["rank", "suitability_index"] + score_cols].copy()
    tbl.columns = ["Rank", "Composite Score"] + list(CRITERION_LABELS.values())
    tbl = tbl.round(3)
    tbl["Composite Score"] = tbl["Composite Score"].apply(lambda x: f"{x:.3f}")
    st.dataframe(
        tbl.style.background_gradient(
            subset=["Composite Score"], cmap="RdYlGn", vmin=0, vmax=1
        ),
        use_container_width=True,
    )

# ============================================================
# TAB 3 — RADAR CHARTS
# ============================================================
with tab_radar:
    st.subheader("Destination Criterion Profiles")
    st.caption("Radar charts show normalized 0–1 scores per criterion (before weighting).")

    selected_dests = st.multiselect(
        "Select destinations to compare",
        options=df_result.index.tolist(),
        default=df_result.index.tolist()[:4],
    )

    if selected_dests:
        categories = list(CRITERION_LABELS.values())
        fig_radar = go.Figure()

        for dest in selected_dests:
            row = df_result.loc[dest]
            values = [row[f"score_{k}"] for k in CRITERIA]
            values_closed = values + [values[0]]
            cats_closed = categories + [categories[0]]

            fig_radar.add_trace(go.Scatterpolar(
                r=values_closed,
                theta=cats_closed,
                fill="toself",
                name=dest,
                line_color=DEST_COLORS.get(dest, "#333"),
                opacity=0.7,
            ))

        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 1], tickfont_size=10)
            ),
            showlegend=True,
            height=520,
            template="plotly_white",
            title="Normalized Criterion Scores by Destination",
        )
        st.plotly_chart(fig_radar, use_container_width=True)
    else:
        st.info("Select at least one destination above.")

# ============================================================
# TAB 4 — SCENARIO COMPARISON
# ============================================================
with tab_scenarios:
    st.subheader("Ranking Sensitivity Across Traveler Profiles")
    st.caption(
        "How destination rankings shift under different traveler priority weightings."
    )

    profile_results = {
        name: compute_suitability(df_raw, weights)
        for name, weights in TRAVELER_PROFILES.items()
    }

    # Rank heatmap
    rank_matrix = pd.DataFrame({
        name: res["rank"]
        for name, res in profile_results.items()
    })

    fig_heat = px.imshow(
        rank_matrix.values,
        x=rank_matrix.columns.tolist(),
        y=rank_matrix.index.tolist(),
        color_continuous_scale="RdYlGn_r",
        text_auto=True,
        aspect="auto",
        labels=dict(color="Rank"),
        title="Destination Rank by Traveler Profile (1 = Best)",
        zmin=1, zmax=7,
    )
    fig_heat.update_layout(height=400, template="plotly_white")
    st.plotly_chart(fig_heat, use_container_width=True)

    # Score comparison line chart
    score_matrix = pd.DataFrame({
        name: res["suitability_index"].round(3)
        for name, res in profile_results.items()
    })

    fig_line = go.Figure()
    for dest in score_matrix.index:
        fig_line.add_trace(go.Scatter(
            x=score_matrix.columns,
            y=score_matrix.loc[dest],
            mode="lines+markers",
            name=dest,
            line=dict(color=DEST_COLORS.get(dest, "#333"), width=2),
            marker=dict(size=8),
        ))

    fig_line.update_layout(
        title="Suitability Index Across Traveler Profiles",
        xaxis_title="Profile",
        yaxis_title="Suitability Index",
        yaxis_range=[0, 1],
        height=420,
        template="plotly_white",
        legend_title="Destination",
    )
    st.plotly_chart(fig_line, use_container_width=True)

    # Summary table
    st.markdown("**Profile Weight Summary**")
    weight_tbl = pd.DataFrame(TRAVELER_PROFILES).T
    weight_tbl.columns = list(CRITERION_LABELS.values())
    st.dataframe(weight_tbl.style.format("{:.0%}").background_gradient(
        cmap="Blues", axis=1
    ), use_container_width=True)

# ============================================================
# TAB 5 — RAW DATA & SOURCES
# ============================================================
with tab_data:
    st.subheader("Raw Destination Data")

    display_cols = {
        "region": "Region",
        "airport_code": "Airport",
        "airport_dist_km": "Airport Dist (km)",
        "intl_flight_routes": "Int'l Routes",
        "avg_temp_c": "Avg Temp (°C)",
        "annual_precip_mm": "Precip (mm)",
        "homicide_rate_per100k": "Homicide /100k",
        "travel_advisory_level": "US Advisory",
        "avg_hotel_rate_usd": "Hotel Rate (USD)",
        "avg_daily_tourist_spend_usd": "Daily Spend (USD)",
        "attraction_score": "Attractions",
        "beach_quality": "Beach Quality",
        "cultural_score": "Culture",
        "nature_score": "Nature",
        "hurricane_risk": "Hurricane Risk",
        "seismic_risk": "Seismic Risk",
        "flood_risk": "Flood Risk",
    }

    raw_display = df_raw[list(display_cols.keys())].rename(columns=display_cols)
    st.dataframe(raw_display, use_container_width=True)

    st.subheader("Data Sources")
    try:
        sources_df = pd.read_csv("data/data_sources.csv")
        st.dataframe(sources_df, use_container_width=True)
    except FileNotFoundError:
        st.info("data/data_sources.csv not found.")

    st.subheader("Methodology Notes")
    st.markdown("""
    **Normalization:** All raw variables are min-max normalized to a 0–1 scale.
    Cost and hazard variables are inverted so that higher scores always indicate
    better suitability.

    **Temperature Comfort:** Rather than a linear scale, temperature comfort is
    modeled with a Gaussian bell curve centered at 24 °C (σ = 6), reflecting
    the non-linear human perception of thermal comfort.

    **Weighted Overlay:** The composite suitability index is the dot product of
    criterion scores and user-specified weights. Weights are auto-normalized
    to sum to 1.0 before calculation.

    **Traveler Profiles:** Six pre-defined profiles shift criterion weights to
    simulate different traveler priorities. A custom profile can be defined
    using the sidebar sliders.

    **Limitations:** Data are compiled at the state or municipal level and
    represent annual averages. Seasonal variation, micro-level spatial
    heterogeneity, and rapidly changing conditions (e.g., travel advisories)
    are not captured.
    """)

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.divider()
st.caption(
    "Mexico Destination Suitability Analysis · "
    "Data: INEGI, CONAGUA, SECTUR, CENAPRED, US DOS, WorldClim v2.1, OAG Aviation · "
    "Analysis: MCDA Weighted Overlay"
)
