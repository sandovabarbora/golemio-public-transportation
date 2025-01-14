import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster, HeatMap


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


# Streamlit layout
st.title("Public Transport Delay Map")
st.markdown("Interactive map showing public transport delays based on user-defined filters.")

data = load_data()
hour_range = st.sidebar.slider("Select Hour Range", min_value=0, max_value=24, value=(8, 10), step=1)
selected_date = st.sidebar.date_input("Select Date", value=data['date'].min())
map_type = st.sidebar.radio("Select Map Type", options=["Markers", "Heatmap"])
show_statistics = st.sidebar.checkbox("Show Summary Statistics", value=True)
if show_statistics:
    compare_date = st.sidebar.date_input("Select Second Date (Optional)")
    if st.sidebar.button("Reset Compare Date"):
        compare_date = None  # Clear the second date


st.sidebar.subheader("Cultural References")
upload_events = st.sidebar.file_uploader("Upload Event CSV (Optional)", type=["csv"])

# Read event data if provided
if upload_events:
    event_data = pd.read_csv(upload_events)
    event_data['Event Date'] = pd.to_datetime(event_data['Event Date'])
    st.write("Uploaded Event Data:", event_data)
else:
    st.write("No event data uploaded yet. Feel free to upload a CSV file.")

# Filter data
filtered_data = filter_data(data, hour_range, selected_date)

# Display map
st.subheader(f"Delays for {selected_date}, Hours: {hour_range[0]}:00 to {hour_range[1]}:00")
delay_map = create_map(filtered_data, map_type)
st_data = st_folium(delay_map, width=700, height=500)

# Display statistics
if show_statistics:
    # Reset button to clear compare_date
    st.subheader("Statistics for Selected Date")
    day_data = data[data['date'] == selected_date]
    total_stops = filtered_data['base_stop_id'].nunique()
    average_delay = filtered_data['current_stop_dep_delay'].mean() 
    maximum_delay = filtered_data['current_stop_dep_delay'].max()
    ok_stops = len(filtered_data[filtered_data['current_stop_dep_delay'] <= 60])
    percent_ok = (ok_stops / len(filtered_data)) * 100 if len(filtered_data) > 0 else 0

    delay_bins = {
        "0-60s": ok_stops,
        "60-120s": len(filtered_data[(filtered_data['current_stop_dep_delay'] > 60) & (filtered_data['current_stop_dep_delay'] <= 120)]),
        "120-180s": len(filtered_data[(filtered_data['current_stop_dep_delay'] > 120) & (filtered_data['current_stop_dep_delay'] <= 180)]),
        "180-300s": len(filtered_data[(filtered_data['current_stop_dep_delay'] > 180) & (filtered_data['current_stop_dep_delay'] <= 300)]),
        ">300s": len(filtered_data[(filtered_data['current_stop_dep_delay'] > 300)])
    }

    delay_bins_df = pd.DataFrame({
        "Bin": ["0-60s", "60-120s", "120-180s", "180-300s", ">300s"],
        "Number of Stops": [delay_bins["0-60s"], delay_bins["60-120s"], delay_bins["120-180s"], delay_bins["180-300s"], delay_bins[">300s"]]
    })

    delay_bins_df["Bin"] = pd.Categorical(delay_bins_df["Bin"], categories=["0-60s", "60-120s", "120-180s", "180-300s", ">300s"], ordered=True)
    delay_bins_df = delay_bins_df.sort_values("Bin")  # Sort by categorical order

    # Hourly trend for the selected date
    day1_data = data[data['date'] == selected_date]
    hourly_trend_day1 = day1_data.groupby(day1_data['current_stop_departure'].dt.hour).agg(
        avg_delay=('current_stop_dep_delay', 'mean')
    ).reset_index()
    hourly_trend_day1['Date'] = str(selected_date)
    hourly_trend_day1.rename(columns={'current_stop_departure': 'Hour'}, inplace=True)

    st.write(f"**Total Stops:** {total_stops}")
    st.write(f"**Average Delay:** {average_delay:.2f} secs ({average_delay / 60:.2f} mins)")
    st.write(f"**Maximum Delay:** {maximum_delay:.2f} secs ({maximum_delay / 60:.2f} mins)")
    st.write(f"**Percentage of OK Stops:** {percent_ok:.2f}%")
    st.write("**Delay Distribution:**")
    st.bar_chart(delay_bins_df.set_index("Bin")["Number of Stops"])
    
    st.subheader("Hourly Trends")
    # Check for second date
    hourly_trends = [hourly_trend_day1]
    if compare_date:
        day2_data = data[data['date'] == compare_date] if compare_date else None
        if not day2_data.empty:
            hourly_trend_day2 = day2_data.groupby(day2_data['current_stop_departure'].dt.hour).agg(
                avg_delay=('current_stop_dep_delay', 'mean')
            ).reset_index()
            hourly_trend_day2['Date'] = str(compare_date)
            hourly_trend_day2.rename(columns={'current_stop_departure': 'Hour'}, inplace=True)
            hourly_trends.append(hourly_trend_day2)

    # Combine hourly trends for comparison
    combined_hourly_trends = pd.concat(hourly_trends)
    combined_hourly_trends['avg_delay'] = combined_hourly_trends['avg_delay'] / 60  # Convert to minutes

    # Plot the hourly trends
    st.subheader(f"Hourly Delay Trend for {selected_date} vs {compare_date if compare_date else 'N/A'}")
    import altair as alt
    trend_chart = alt.Chart(combined_hourly_trends).mark_line().encode(
        x=alt.X('Hour:O', title='Hour of Day'),
        y=alt.Y('avg_delay:Q', title='Average Delay (mins)'),
        color=alt.Color('Date:N', legend=alt.Legend(title="Date")),
        tooltip=['Date', 'Hour', 'avg_delay']
    ).properties(
        width=700,
        height=400
    )
    st.altair_chart(trend_chart)


