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
    Render detailed analysis for an individual match.
    Allows selection of a match date and displays metrics and charts around that match.
    """
    historical_matches = events_df[events_df["datetime"].dt.date <= pd.Timestamp.now().date()].sort_values("datetime")
    if historical_matches.empty:
        st.info("No historical match data available for analysis")
        return
    
    selected_date = st.selectbox(
        "Select Match Date",
        options=historical_matches["datetime"].dt.date,
        format_func=lambda x: (
            f"{x.strftime('%d.%m.%Y')} - {historical_matches[historical_matches['datetime'].dt.date == x]['Opponent'].iloc[0]} "
            f"({'Home' if historical_matches[historical_matches['datetime'].dt.date == x]['is_home'].iloc[0] else 'Away'})"
        )
    )
    if selected_date:
        match_data = historical_matches[historical_matches["datetime"].dt.date == selected_date].iloc[0]
        comparison_data = get_comparison_data(data, selected_date)
        st.write("### Match Information")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"🏟️ **Location:** {'Home match at Letná' if match_data['is_home'] else 'Away match'}")
            st.write(f"👥 **Opponent:** {match_data['Opponent']}")
        with col2:
            st.write(f"📅 **Date:** {match_data['datetime'].strftime('%d.%m.%Y')}")
            st.write(f"⏰ **Kickoff:** {match_data['datetime'].strftime('%H:%M')}")
        # Further detailed charts and metrics for the individual match can be added here.
        

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
