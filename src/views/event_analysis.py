# src/views/event_analysis.py
import pandas as pd
import altair as alt
import streamlit as st
from datetime import timedelta
from src.models.event_analysis import get_comparison_data, analyze_event_impact

def display_overall_impact(data: pd.DataFrame, events_df: pd.DataFrame):
    """
    Render overall impact analysis of events on delays.
    Displays aggregate metrics, key findings, and an hourly delay chart.
    """
    event_stats, hourly_stats = analyze_event_impact(data, events_df)
    try:
        match_avg_delay = event_stats.loc[event_stats["is_event"] == True, "avg_delay"].iloc[0]
        normal_avg_delay = event_stats.loc[event_stats["is_event"] == False, "avg_delay"].iloc[0]
        delay_increase = ((match_avg_delay / normal_avg_delay) - 1) * 100
    except Exception as ex:
        st.error("Error calculating overall metrics: " + str(ex))
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Average Impact on Delays",
            f"{delay_increase:.1f}%",
            delta=f"{match_avg_delay - normal_avg_delay:.0f} sec longer",
            delta_color="inverse"
        )
    with col2:
        st.metric(
            "Matches Analyzed",
            f"{len(events_df)} games",
            f"{len(events_df[events_df['is_home']])} home matches"
        )
    with col3:
        worst_hour_stats = hourly_stats[hourly_stats["day_type"] == "Match Days"]
        worst_hour = worst_hour_stats.loc[worst_hour_stats["mean_delay"].idxmax()]
        st.metric(
            "Most Affected Time",
            f"{int(worst_hour['hour']):02d}:00",
            f"{worst_hour['mean_delay']:.0f} sec average delay",
            delta_color="inverse"
        )
    
    st.subheader("Key Findings")
    col1, col2 = st.columns(2)
    with col1:
        st.write("##### 🚌 Transport Impact")
        # (Additional detailed text/metrics can be rendered here.)
        st.write(f"Average delays increase by {delay_increase:.1f}% on match days.")
    with col2:
        st.write("##### 💡 Recommendations")
        recommendations = [
            "• Adjust traffic light timing during peak match hours",
            "• Consider dedicated lanes for public transport",
            "• Deploy traffic officers at key intersections"
        ]
        for rec in recommendations:
            st.write(rec)
    
    st.subheader("Hourly Delay Statistics")
    chart = alt.Chart(hourly_stats).mark_line(point=True).encode(
        x=alt.X("hour:Q", title="Hour of Day", scale=alt.Scale(domain=[0, 23])),
        y=alt.Y("mean_delay:Q", title="Average Delay (seconds)"),
        color=alt.Color("day_type:N", title="Day Type",
                        scale=alt.Scale(domain=["Match Days", "Regular Days"], range=["#ff6b6b", "#4c6ef5"])),
        tooltip=["hour:Q", "mean_delay:Q", "day_type:N"]
    ).properties(width=700, height=400, title="Average Transport Delays")
    rush_hours = pd.DataFrame([
        {"start": 7, "end": 9},
        {"start": 16, "end": 19}
    ])
    rush_hour_bands = alt.Chart(rush_hours).mark_rect(opacity=0.2, color="gray").encode(
        x="start:Q",
        x2="end:Q",
        y=alt.value(0),
        y2=alt.value(300)
    )
    st.altair_chart(rush_hour_bands + chart)
    st.caption("Gray bands indicate typical rush hour periods")


def display_individual_matches(data: pd.DataFrame, events_df: pd.DataFrame):
    """
    Render detailed analysis for an individual match with comprehensive visualizations.
    Shows match details, delay comparisons, and temporal patterns around match time.
    """
    st.subheader("Match Day Impact Analysis")
    historical_matches = events_df[events_df['datetime'].dt.date <= pd.Timestamp.now().date()]
    
    if not historical_matches.empty:
        historical_matches = historical_matches.sort_values('datetime')
        selected_date = st.selectbox(
            "Select Match Date",
            options=historical_matches['datetime'].dt.date,
            format_func=lambda x: (
                f"{x.strftime('%d.%m.%Y')} - {historical_matches[historical_matches['datetime'].dt.date == x]['Opponent'].iloc[0]} "
                f"({'Home' if historical_matches[historical_matches['datetime'].dt.date == x]['is_home'].iloc[0] else 'Away'})"
            )
        )
        
        if selected_date:
            match_data = historical_matches[historical_matches['datetime'].dt.date == selected_date].iloc[0]
            comparison_data = get_comparison_data(data, selected_date)
            
            # Match info and key metrics
            st.write("### Match Information")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"🏟️ **Location:** {'Home match at Letná' if match_data['is_home'] else 'Away match'}")
                st.write(f"👥 **Opponent:** {match_data['Opponent']}")
            with col2:
                st.write(f"📅 **Date:** {match_data['datetime'].strftime('%d.%m.%Y')}")
                st.write(f"⏰ **Kickoff:** {match_data['datetime'].strftime('%H:%M')}")
            
            # Time Window Analysis
            st.subheader("Delays Around Match Time")
            
            match_hour = match_data['datetime'].hour
            time_windows = {
                '3 hours before': (match_hour - 3, match_hour),
                '2 hours before': (match_hour - 2, match_hour),
                '1 hour before': (match_hour - 1, match_hour),
                '1 hour after': (match_hour, match_hour + 1),
                '2 hours after': (match_hour, match_hour + 2),
                '3 hours after': (match_hour, match_hour + 3)
            }
            
            window_stats = {}
            for window_name, (start_hour, end_hour) in time_windows.items():
                match_window = comparison_data['Match Day'][
                    (comparison_data['Match Day']['current_stop_departure'].dt.hour >= start_hour) &
                    (comparison_data['Match Day']['current_stop_departure'].dt.hour < end_hour)
                ]
                regular_window = comparison_data['Week Before'][
                    (comparison_data['Week Before']['current_stop_departure'].dt.hour >= start_hour) &
                    (comparison_data['Week Before']['current_stop_departure'].dt.hour < end_hour)
                ]
                
                match_avg = match_window['current_stop_dep_delay'].mean()
                regular_avg = regular_window['current_stop_dep_delay'].mean()
                increase = ((match_avg / regular_avg) - 1) * 100 if regular_avg > 0 else 0
                
                window_stats[window_name] = {
                    'match_avg': match_avg,
                    'regular_avg': regular_avg,
                    'increase': increase,
                    'sample_size': len(match_window)
                }
            
            # Display time window analysis
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("##### Before Match")
                for window in ['3 hours before', '2 hours before', '1 hour before']:
                    stats = window_stats[window]
                    st.metric(
                        window,
                        f"{stats['match_avg']:.0f} sec",
                        f"{stats['increase']:.1f}% vs normal",
                        help=f"Based on {stats['sample_size']} measurements",
                        delta_color="inverse"
                    )
            
            with col2:
                st.write("##### After Match")
                for window in ['1 hour after', '2 hours after', '3 hours after']:
                    stats = window_stats[window]
                    st.metric(
                        window,
                        f"{stats['match_avg']:.0f} sec",
                        f"{stats['increase']:.1f}% vs normal",
                        help=f"Based on {stats['sample_size']} measurements",
                        delta_color="inverse"
                    )
            
            # Add a visual summary of the time windows
            window_data = pd.DataFrame([
                {
                    'window': window,
                    'delay': stats['match_avg'],
                    'increase': stats['increase'],
                    'is_before': 'Before' if 'before' in window else 'After'
                }
                for window, stats in window_stats.items()
            ])
            
            window_chart = alt.Chart(window_data).mark_bar().encode(
                x=alt.X('window:N', 
                    sort=['3 hours before', '2 hours before', '1 hour before',
                            '1 hour after', '2 hours after', '3 hours after'],
                    title='Time Window'),
                y=alt.Y('delay:Q', title='Average Delay (seconds)'),
                color=alt.Color('is_before:N', 
                            scale=alt.Scale(domain=['Before', 'After'],
                                            range=['#5276A7', '#57A44C'])),
                tooltip=[
                    alt.Tooltip('window:N', title='Time Window'),
                    alt.Tooltip('delay:Q', title='Average Delay', format='.1f'),
                    alt.Tooltip('increase:Q', title='Increase vs Normal', format='.1f')
                ]
            ).properties(
                width=700,
                height=300,
                title='Average Delays in Different Time Windows'
            )
            
            st.altair_chart(window_chart)
            st.caption(f"Analysis of delays before and after {match_data['datetime'].strftime('%H:%M')} kickoff")
            
            # Traffic Impact Summary
            st.subheader("Overall Traffic Impact")
            
            # Calculate average delays
            match_avg = comparison_data['Match Day']['current_stop_dep_delay'].mean()
            regular_avg = comparison_data['Week Before']['current_stop_dep_delay'].mean()
            delay_increase = ((match_avg / regular_avg) - 1) * 100 if regular_avg > 0 else 0
            
            # Simple metrics that matter for city management
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "Overall Delay Impact",
                    f"{delay_increase:.1f}%",
                    delta=f"{match_avg - regular_avg:.0f} sec" if delay_increase > 0 else "Normal traffic",
                    delta_color="inverse"
                )
            
            with col2:
                # Calculate delays around match time (±2 hours)
                match_hour = match_data['datetime'].hour
                match_window = comparison_data['Match Day'][
                    (comparison_data['Match Day']['current_stop_departure'].dt.hour >= match_hour - 2) &
                    (comparison_data['Match Day']['current_stop_departure'].dt.hour <= match_hour + 2)
                ]
                match_time_avg = match_window['current_stop_dep_delay'].mean()
                
                st.metric(
                    "Match Time Delays",
                    f"{match_time_avg:.0f} sec",
                    help="Average delays during ±2 hours around match time",
                    delta_color="inverse"
                )
            
            with col3:
                # Most affected hour
                hourly_delays = comparison_data['Match Day'].groupby(
                    comparison_data['Match Day']['current_stop_departure'].dt.hour
                )['current_stop_dep_delay'].mean()
                worst_hour = hourly_delays.idxmax()
                worst_delay = hourly_delays.max()
                
                st.metric(
                    "Peak Impact Hour",
                    f"{worst_hour:02d}:00",
                    f"{worst_delay:.0f} sec average delay",
                    delta_color='inverse'
                )
            
            # Hourly delay visualization
            st.subheader("Hourly Delay Pattern")
            
            # Prepare hourly data
            hourly_data = []
            for day_type, day_data in {'Match Day': comparison_data['Match Day'], 
                                    'Regular Day': comparison_data['Week Before']}.items():
                if not day_data.empty:
                    hourly = day_data.groupby(
                        day_data['current_stop_departure'].dt.hour
                    )['current_stop_dep_delay'].mean().reset_index()
                    hourly['day_type'] = day_type
                    hourly_data.append(hourly)
            
            if hourly_data:
                hourly_df = pd.concat(hourly_data)
                
                chart = alt.Chart(hourly_df).mark_line(point=True).encode(
                    x=alt.X('current_stop_departure:Q', 
                        title='Hour of Day',
                        scale=alt.Scale(domain=[0, 23])),
                    y=alt.Y('current_stop_dep_delay:Q', 
                        title='Average Delay (seconds)'),
                    color=alt.Color('day_type:N', 
                                title='Day Type'),
                    tooltip=['current_stop_departure:Q', 
                            'current_stop_dep_delay:Q', 
                            'day_type:N']
                ).properties(
                    width=700,
                    height=400,
                    title='Hourly Delay Comparison'
                )
                
                # Add match time marker
                match_line = alt.Chart(pd.DataFrame({'x': [match_hour]})).mark_rule(
                    color='red',
                    strokeDash=[4, 4]
                ).encode(x='x:Q')
                
                st.altair_chart(chart + match_line)
                st.caption("Red dashed line shows match start time")
                
                # Recommendations
                st.subheader("Recommendations")
                if match_avg > regular_avg * 1.2:  # 20% or more increase
                    st.write("Based on the observed delays:")
                    recommendations = [
                        f"🚌 Consider additional public transport capacity {match_hour-1:02d}:00 - {match_hour+1:02d}:00",
                        "🚥 Review traffic light timing during peak impact hours",
                        "👮 Deploy additional traffic officers at key intersections"
                    ]
                    if match_data['is_home']:
                        recommendations.append("🅿️ Consider temporary parking restrictions in residential areas")
                    
                    for rec in recommendations:
                        st.write(rec)
                else:
                    st.write("✅ Current traffic management measures appear adequate for this type of match")
    else:
        st.info("No historical match data available for analysis")


def display_event_analysis(data: pd.DataFrame, events_df: pd.DataFrame):
    """
    Main view function to render event analysis.
    Provides two modes: Overall Impact and Individual Matches.
    """
    # Ensure datetime conversion
    if not pd.api.types.is_datetime64_any_dtype(events_df["datetime"]):
        events_df["datetime"] = pd.to_datetime(events_df["datetime"], errors="coerce")
    events_df = events_df.dropna(subset=["datetime"])
    if events_df.empty:
        st.error("No valid event dates found in the schedule.")
        return
    
    view = st.radio("Select Analysis View:", ["Overall Impact", "Individual Matches"], horizontal=True)
    
    if view == "Overall Impact":
        display_overall_impact(data, events_df)
    elif view == "Individual Matches":
        display_individual_matches(data, events_df)
