import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster, HeatMap
from src.event_analysis import load_event_data, display_event_analysis
from src.predictions import display_travel_advice_wrapper, display_detailed_predictions
import numpy as np
import altair as alt

import warnings
warnings.filterwarnings("ignore")


# Load the data
@st.cache_data
def load_data():
    stop_times = pd.read_csv("stop_times.csv")
    stop_times = stop_times.assign(
        current_stop_departure=pd.to_datetime(stop_times['current_stop_departure'], utc=True),
        current_stop_arrival=pd.to_datetime(stop_times['current_stop_arrival'], utc=True),
        created_at=pd.to_datetime(stop_times['created_at'], utc=True),
        updated_at=pd.to_datetime(stop_times['updated_at'], utc=True),
        base_stop_id=stop_times['gtfs_stop_id'].str.extract(r'^(.*?)(?=[SZ])')[0],
        date=lambda df: df['current_stop_departure'].dt.date
    )

    stops_letna = pd.read_csv("letna_stops.csv")
    return stop_times.merge(stops_letna, on='base_stop_id', how='inner')


# Filter data for map display
def filter_data(data, hour_range, selected_date):
    return data[
        (data['date'] == selected_date) &
        (data['current_stop_departure'].dt.hour >= hour_range[0]) &
        (data['current_stop_departure'].dt.hour <= hour_range[1])
    ].fillna(0)


# Get color based on delay thresholds
def get_color(delay_seconds):
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


def analyze_event_impact(data, events):
    # Add event flag to transport data
    data['date'] = data['current_stop_departure'].dt.date
    data['is_event'] = data['date'].isin(events['Event Date'].dt.date)

    # Event day statistics
    event_stats = data.groupby('is_event').agg(
        avg_delay=('current_stop_dep_delay', 'mean'),
        max_delay=('current_stop_dep_delay', 'max'),
        total_records=('current_stop_dep_delay', 'count')
    ).reset_index()

    # Return filtered data for visualization and statistics
    event_day_data = data[data['is_event'] == True]
    return event_stats, event_day_data

def get_hourly_trends(data, selected_date, compare_date=None):
    # Get hourly trend for selected date
    day1_data = data[data['date'] == selected_date]
    hourly_trend_day1 = day1_data.groupby(day1_data['current_stop_departure'].dt.hour).agg(
        avg_delay=('current_stop_dep_delay', 'mean')
    ).reset_index()
    hourly_trend_day1['Date'] = str(selected_date)
    hourly_trend_day1.rename(columns={'current_stop_departure': 'Hour'}, inplace=True)
    
    hourly_trends = [hourly_trend_day1]
    
    # Add comparison date if provided
    if compare_date:
        day2_data = data[data['date'] == compare_date]
        if not day2_data.empty:
            hourly_trend_day2 = day2_data.groupby(day2_data['current_stop_departure'].dt.hour).agg(
                avg_delay=('current_stop_dep_delay', 'mean')
            ).reset_index()
            hourly_trend_day2['Date'] = str(compare_date)
            hourly_trend_day2.rename(columns={'current_stop_departure': 'Hour'}, inplace=True)
            hourly_trends.append(hourly_trend_day2)
    
    return pd.concat(hourly_trends)

# Create the map
def create_map(data, map_type):
    stops = pd.read_csv("letna_stops.csv")
    unique_stops = data.groupby('base_stop_id').agg(
        avg_latitude=('avg_latitude', 'mean'),
        avg_longitude=('avg_longitude', 'mean'),
        stop_name=('stop_name', 'first'),
        avg_delay=('current_stop_dep_delay', 'mean')
    ).reset_index()

    m = folium.Map(location=[stops['avg_latitude'].mean(), stops['avg_longitude'].mean()],
                   zoom_start=14,
                   tiles="CartoDB Positron")
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
                    popup=(
                        f"<b>Stop Name:</b> {stop['stop_name']}<br>"
                        f"<b>Average Delay:</b> {avg_delay_min:.2f} mins<br>"
                        f"<b>ROPID Status:</b> {color.capitalize()}"
                    )
                ).add_to(marker_cluster)

    if map_type == "Heatmap":
    # Prepare heatmap data
        heat_data = [
            [row['avg_latitude'], row['avg_longitude'], row['avg_delay'] / 60]  # Delay in minutes
            for _, row in unique_stops.iterrows()
            if pd.notnull(row['avg_latitude']) and pd.notnull(row['avg_longitude'])
        ]

        # Add heatmap layer
        HeatMap(heat_data, radius=15, max_zoom=12).add_to(m)

        # Add transparent markers with tooltips
        for _, stop in unique_stops.iterrows():
            if pd.notnull(stop["avg_latitude"]) and pd.notnull(stop["avg_longitude"]):
                avg_delay_min = stop["avg_delay"] / 60  # Convert delay to minutes

                folium.CircleMarker(
                    location=[stop["avg_latitude"], stop["avg_longitude"]],
                    radius=0,  # Transparent marker
                    tooltip=f"{stop['stop_name']} - Avg Delay: {stop['avg_delay']:.0f} secs ({avg_delay_min:.2f} mins)",
                ).add_to(m)

    return m


# Streamlit app
st.title("Public Transport Analysis Dashboard")

# Create tabs
tab1, tab2, tab3 = st.tabs(["Delay Statistics", "Event Analysis", "Predictions"])

# Load main data
data = load_data()

# Sidebar for event file upload (shared between tabs)
with st.sidebar:
    st.header("Event Data")
    event_file = st.file_uploader("Upload Sparta Praha Match Schedule", type=['csv'])

with tab1:
    st.header("Current Delay Statistics")
    
    # Sidebar filters for statistics tab
    with st.sidebar:
        st.header("Map Filters")
        hour_range = st.slider("Select Hour Range", min_value=0, max_value=24, value=(8, 10), step=1)
        selected_date = st.date_input("Select Date", value=data['date'].max())
        map_type = st.radio("Select Map Type", options=["Markers", "Heatmap"])
        
        # Add comparison date selection
        st.header("Comparison")
        show_comparison = st.checkbox("Compare with another date", value=False)
        compare_date = None
        if show_comparison:
            compare_date = st.date_input("Select Comparison Date", 
                                       value=data['date'].min(),
                                       key="compare_date")
    
    # Display map and basic statistics
    filtered_data = filter_data(data, hour_range, selected_date)
    
    st.subheader(f"Delays for {selected_date}, Hours: {hour_range[0]}:00 to {hour_range[1]}:00")
    delay_map = create_map(filtered_data, map_type)
    st_folium(delay_map, width=700, height=500)
    
    # Basic statistics section
    st.subheader("Basic Statistics")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Average Delay", f"{filtered_data['current_stop_dep_delay'].mean():.2f} sec")
    with col2:
        st.metric("Maximum Delay", f"{filtered_data['current_stop_dep_delay'].max():.2f} sec")
    with col3:
        st.metric("Total Stops", filtered_data['base_stop_id'].nunique())
    
    # Add delay distribution
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
    
    st.bar_chart(delay_dist_df.set_index("Delay Range"))
    
    # Add hourly trends
    st.subheader("Hourly Delay Trends")
    hourly_data = get_hourly_trends(data, selected_date, compare_date)
    
    # Create the trend chart
    trend_chart = alt.Chart(hourly_data).mark_line(point=True).encode(
        x=alt.X('Hour:Q', title='Hour of Day', scale=alt.Scale(domain=[0, 23])),
        y=alt.Y('avg_delay:Q', title='Average Delay (seconds)'),
        color=alt.Color('Date:N', title='Date'),
        tooltip=['Hour:Q', 'avg_delay:Q', 'Date:N']
    ).properties(
        width=700,
        height=400,
        title='Average Delays Throughout the Day'
    )
    
    st.altair_chart(trend_chart)
    
    # Add comparison metrics if comparison date is selected
    if show_comparison and compare_date:
        st.subheader("Date Comparison")
        compare_data = filter_data(data, hour_range, compare_date)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            diff_avg = filtered_data['current_stop_dep_delay'].mean() - compare_data['current_stop_dep_delay'].mean()
            st.metric("Average Delay Difference", 
                     f"{abs(diff_avg):.2f} sec",
                     delta=f"{'Higher' if diff_avg > 0 else 'Lower'} than comparison date")
        with col2:
            diff_max = filtered_data['current_stop_dep_delay'].max() - compare_data['current_stop_dep_delay'].max()
            st.metric("Maximum Delay Difference",
                     f"{abs(diff_max):.2f} sec",
                     delta=f"{'Higher' if diff_max > 0 else 'Lower'} than comparison date")
        with col3:
            diff_stops = filtered_data['base_stop_id'].nunique() - compare_data['base_stop_id'].nunique()
            st.metric("Stop Count Difference",
                     abs(diff_stops),
                     delta=f"{'More' if diff_stops > 0 else 'Fewer'} than comparison date")

with tab2:
    st.header("Event Impact Analysis")
    if event_file is not None:
        try:
            events_df = load_event_data(event_file)
            display_event_analysis(data, events_df)
        except Exception as e:
            st.error(f"Error processing event data: {str(e)}")
    else:
        st.info("Please upload the Sparta Praha match schedule CSV file to see event analysis.")

# Update the main tab code
with tab3:
    st.header("Delay Predictions")
    if event_file is not None:
        try:
            if 'events_df' not in locals():
                events_df = load_event_data(event_file)
            
            # Create tabs for different prediction views
            pred_tab1, pred_tab2 = st.tabs(["Travel Advisor", "Detailed Predictions"])
            
            with pred_tab1:
                display_travel_advice_wrapper(data, events_df)
            
            with pred_tab2:
                display_detailed_predictions(data, events_df)
                
        except Exception as e:
            st.error(f"Error in predictions: {str(e)}")
            st.exception(e)
    else:
        st.info("Please upload the Sparta Praha match schedule CSV file to see delay predictions.")

# Add a footer with last update information
st.markdown("---")
st.caption(f"Last updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")