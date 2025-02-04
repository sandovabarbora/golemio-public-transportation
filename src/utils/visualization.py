"""
Module: visualization.py
Description: Contains utility functions for visualizing public transport data using Folium and Altair.
"""

import folium
from folium.plugins import MarkerCluster, HeatMap
import pandas as pd


def get_color(delay_seconds: float) -> str:
    """
    Determine marker color based on delay duration.

    Parameters:
        delay_seconds (float): Delay in seconds.

    Returns:
        str: Color name.
    """
    if delay_seconds <= 60:
        return "green"
    elif delay_seconds <= 120:
        return "yellow"
    elif delay_seconds <= 180:
        return "orange"
    elif delay_seconds <= 300:
        return "red"
    else:
        return "darkred"


def create_map(data: pd.DataFrame, map_type: str) -> folium.Map:
    """
    Create a Folium map visualization of stops.

    Parameters:
        data (pd.DataFrame): DataFrame with stop times and stops details.
        map_type (str): "Markers" for clustered markers or "Heatmap" for a heatmap view.

    Returns:
        folium.Map: A Folium map object.
    """
    stops = pd.read_csv("./data/letna_stops.csv")
    unique_stops = data.groupby('base_stop_id').agg(
        avg_latitude=('avg_latitude', 'mean'),
        avg_longitude=('avg_longitude', 'mean'),
        stop_name=('stop_name', 'first'),
        avg_delay=('current_stop_dep_delay', 'mean')
    ).reset_index()

    m = folium.Map(
        location=[stops['avg_latitude'].mean(), stops['avg_longitude'].mean()],
        zoom_start=14,
        tiles="CartoDB Positron"
    )
    if map_type == "Markers":
        marker_cluster = MarkerCluster().add_to(m)
        for _, stop in unique_stops.iterrows():
            if pd.notnull(stop["avg_latitude"]) and pd.notnull(stop["avg_longitude"]):
                avg_delay_min = stop["avg_delay"] / 60
                color = get_color(stop["avg_delay"])
                folium.CircleMarker(
                    location=[stop["avg_latitude"], stop["avg_longitude"]],
                    radius=8,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.7,
                    tooltip=f"{stop['stop_name']} - Avg Delay: {stop['avg_delay']:.0f} secs ({avg_delay_min:.2f} mins)",
                    popup=(f"<b>Stop Name:</b> {stop['stop_name']}<br>"
                           f"<b>Average Delay:</b> {avg_delay_min:.2f} mins<br>"
                           f"<b>ROPID Status:</b> {color.capitalize()}")
                ).add_to(marker_cluster)
    elif map_type == "Heatmap":
        heat_data = [
            [row['avg_latitude'], row['avg_longitude'], row['avg_delay'] / 60]
            for _, row in unique_stops.iterrows()
            if pd.notnull(row['avg_latitude']) and pd.notnull(row['avg_longitude'])
        ]
        HeatMap(heat_data, radius=15, max_zoom=12).add_to(m)
    return m


def get_hourly_trends(data: pd.DataFrame, selected_date, compare_date=None) -> pd.DataFrame:
    """
    Compute hourly average delay trends for a selected date and an optional comparison date.

    Parameters:
        data (pd.DataFrame): Stop times data.
        selected_date: Primary date for analysis.
        compare_date (optional): Secondary date for comparison.

    Returns:
        pd.DataFrame: DataFrame containing hourly trends with date labels.
    """
    day1_data = data[data['date'] == selected_date]
    hourly_trend_day1 = day1_data.groupby(day1_data['current_stop_departure'].dt.hour).agg(
        avg_delay=('current_stop_dep_delay', 'mean')
    ).reset_index()
    hourly_trend_day1['Date'] = str(selected_date)
    hourly_trend_day1.rename(columns={'current_stop_departure': 'Hour'}, inplace=True)

    hourly_trends = [hourly_trend_day1]

    if compare_date:
        day2_data = data[data['date'] == compare_date]
        if not day2_data.empty:
            hourly_trend_day2 = day2_data.groupby(day2_data['current_stop_departure'].dt.hour).agg(
                avg_delay=('current_stop_dep_delay', 'mean')
            ).reset_index()
            hourly_trend_day2['Date'] = str(compare_date)
            hourly_trend_day2.rename(columns={'current_stop_departure': 'Hour'}, inplace=True)
            hourly_trends.append(hourly_trend_day2)

    return pd.concat(hourly_trends, ignore_index=True)
