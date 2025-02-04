"""
Module: delay_statistics.py
Description: Renders the Delay Statistics view, now broken into modular components.
"""

import streamlit as st
import pandas as pd
import altair as alt
from datetime import timedelta
from streamlit_folium import st_folium
from src.utils.visualization import create_map, get_hourly_trends


def render_map_section(filtered_data: pd.DataFrame, map_type: str) -> None:
    """Render the map section using Folium."""
    st.subheader("Map View")
    delay_map = create_map(filtered_data, map_type)
    st_folium(delay_map, width=700, height=500)


def render_basic_statistics(filtered_data: pd.DataFrame) -> None:
    """Display basic delay statistics as metrics."""
    st.subheader("Basic Statistics")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Average Delay", f"{filtered_data['current_stop_dep_delay'].mean():.2f} sec")
    with col2:
        st.metric("Maximum Delay", f"{filtered_data['current_stop_dep_delay'].max():.2f} sec")
    with col3:
        st.metric("Total Stops", filtered_data['base_stop_id'].nunique())


def render_delay_distribution(filtered_data: pd.DataFrame) -> None:
    """Render a bar chart showing the distribution of delays."""
    st.subheader("Delay Distribution")
    delay_bins = {
        "0-60s": len(filtered_data[filtered_data['current_stop_dep_delay'] <= 60]),
        "60-120s": len(filtered_data[(filtered_data['current_stop_dep_delay'] > 60) &
                                     (filtered_data['current_stop_dep_delay'] <= 120)]),
        "120-180s": len(filtered_data[(filtered_data['current_stop_dep_delay'] > 120) &
                                      (filtered_data['current_stop_dep_delay'] <= 180)]),
        "180-300s": len(filtered_data[(filtered_data['current_stop_dep_delay'] > 180) &
                                      (filtered_data['current_stop_dep_delay'] <= 300)]),
        ">300s": len(filtered_data[filtered_data['current_stop_dep_delay'] > 300])
    }
    delay_dist_df = pd.DataFrame({
        "Delay Range": list(delay_bins.keys()),
        "Count": list(delay_bins.values())
    })

    bin_order = ["0-60s", "60-120s", "120-180s", "180-300s", ">300s"]
    delay_dist_df["Delay Range"] = pd.Categorical(delay_dist_df["Delay Range"], categories=bin_order, ordered=True)
    delay_dist_df = delay_dist_df.sort_values("Delay Range")
    st.bar_chart(delay_dist_df.set_index("Delay Range"))


def render_hourly_trends_section(data: pd.DataFrame, selected_date, compare_date=None) -> None:
    """Render hourly delay trends using Altair with rush hour overlays."""
    st.subheader("Hourly Delay Trends")
    rush_hours = pd.DataFrame([
        {"start": 7, "end": 9},
        {"start": 16, "end": 19}
    ])
    rush_hour_bands = alt.Chart(rush_hours).mark_rect(
        opacity=0.2,
        color="gray"
    ).encode(
        x=alt.X("start:Q", title="Hour of Day", scale=alt.Scale(domain=[0, 23])),
        x2="end:Q",
        y=alt.value(0),
        y2=alt.value(300)
    )
    hourly_data = get_hourly_trends(data, selected_date, compare_date)
    trend_chart = alt.Chart(hourly_data).mark_line(point=True).encode(
        x=alt.X('Hour:Q', title='Hour of Day', scale=alt.Scale(domain=[0, 23])),
        y=alt.Y('avg_delay:Q', title='Average Delay (seconds)'),
        color=alt.Color('Date:N', title='Date'),
        tooltip=['Hour:Q', 'avg_delay:Q', 'Date:N']
    ).properties(width=700, height=400, title='Average Delays Throughout the Day')
    
    st.altair_chart(trend_chart + rush_hour_bands)


def render_delay_statistics(data: pd.DataFrame) -> None:
    """
    Render the Delay Statistics view with modular sub-components.

    Parameters:
        data (pd.DataFrame): Merged stop times and stops data.
    """
    st.header("Current Delay Statistics")
    
    # Sidebar filters: these can be modularized further if needed.
    with st.sidebar:
        st.header("Map Filters")
        hour_range = st.slider("Select Hour Range", min_value=0, max_value=24, value=(0, 24), step=1)
        selected_date = st.date_input("Select Date", value=data['date'].max() - timedelta(days=1))
        map_type = st.radio("Select Map Type", options=["Markers", "Heatmap"])
        st.header("Comparison")
        show_comparison = st.checkbox("Compare with another date", value=False)
        compare_date = None
        if show_comparison:
            compare_date = st.date_input("Select Comparison Date", value=data['date'].min(), key="compare_date")
    
    # Filter data based on user input.
    filtered_data = data[
        (data['date'] == selected_date) &
        (data['current_stop_departure'].dt.hour >= hour_range[0]) &
        (data['current_stop_departure'].dt.hour <= hour_range[1])
    ].fillna(0)
    
    st.subheader(f"Delays for {selected_date}, Hours: {hour_range[0]}:00 to {hour_range[1]}:00")
    
    # Render each modular section.
    render_map_section(filtered_data, map_type)
    render_basic_statistics(filtered_data)
    render_delay_distribution(filtered_data)
    render_hourly_trends_section(data, selected_date, compare_date)
