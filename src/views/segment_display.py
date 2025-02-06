# segment_display.py

import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime

class SegmentPredictionsDisplay:
    @staticmethod
    def display_predictions(predictor) -> None:
        stops = sorted(predictor.data["stop_name"].unique())
        segments = sorted(predictor.data["segment_id_short"].unique())
        
        selected_segment = st.selectbox("Select Transit Segment", options=segments)
        directions = sorted(predictor.data["gtfs_direction_id"].unique())
        selected_direction = st.selectbox("Select Direction", options=directions)

        col_date, col_time = st.columns(2)
        with col_date:
            pred_date = st.date_input("Select Prediction Date", value=datetime.now().date())
        with col_time:
            pred_time = st.time_input("Select Prediction Time", value=datetime.now().time())
        pred_datetime = pd.Timestamp(datetime.combine(pred_date, pred_time))
        if pred_datetime.tzinfo is None:
            pred_datetime = pred_datetime.tz_localize("UTC")

        current_pred = predictor.compute_segment_prediction(pred_datetime, selected_segment, selected_direction)
        if current_pred is None:
            st.warning("Insufficient historical data for a current prediction.")
            return

        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "Predicted Travel Time",
                f"{current_pred['mean_travel_time']:.0f} sec",
                help=f"Confidence Interval: [{current_pred['confidence_lower']:.0f}, {current_pred['confidence_upper']:.0f}] sec"
            )
        with col2:
            st.metric(
                "Prediction Reliability",
                f"{current_pred['reliability']:.1f}%",
                help=(
                    f"Sample size: {current_pred['sample_size']} observations\n"
                    f"CI width: ±{current_pred['margin_error']:.1f} sec\n"
                    f"{'Peak Hour' if current_pred['is_peak_hour'] else 'Non-peak Hour'}, "
                    f"{'Match Day' if current_pred['is_match_day'] else 'Regular Day'}"
                )
            )

        # Historical data chart
        current_ts = pred_datetime
        last_week_start = current_ts - pd.Timedelta(days=7)
        historical_data = predictor.data[
            (predictor.data["segment_id_short"] == selected_segment) &
            (predictor.data["gtfs_direction_id"] == selected_direction) &
            (predictor.data["current_stop_departure"] >= last_week_start) &
            (predictor.data["current_stop_departure"] < current_ts)
        ]
        
        if not historical_data.empty:
            hist_chart = alt.Chart(historical_data).mark_line(point=True).encode(
                x=alt.X("current_stop_departure:T", title="Time"),
                y=alt.Y("real_travel_time_seconds:Q", title="Travel Time (seconds)"),
                tooltip=[
                    alt.Tooltip("current_stop_departure:T", title="Time"),
                    alt.Tooltip("real_travel_time_seconds:Q", title="Travel Time (sec)", format=".1f")
                ]
            ).properties(width=700, height=400, title="Historical Travel Times (Last Week)")
            st.altair_chart(hist_chart)
        else:
            st.warning("No historical data available for last week.")

        # Short-term prediction chart
        future_preds = predictor.generate_short_term_predictions(
            start_datetime=pred_datetime,
            segment_id=selected_segment,
            direction=selected_direction,
            interval_minutes=15,
            duration_hours=3,
        )
        
        if future_preds:
            future_df = pd.DataFrame(future_preds)
            ci_band = alt.Chart(future_df).mark_area(opacity=0.3, color="lightblue").encode(
                x=alt.X("datetime:T", title="Time"),
                y=alt.Y("confidence_lower:Q", title="Predicted Travel Time (seconds)"),
                y2=alt.Y2("confidence_upper:Q")
            )
            line_chart = alt.Chart(future_df).mark_line(point=True, color="blue").encode(
                x=alt.X("datetime:T", title="Time"),
                y=alt.Y("mean_travel_time:Q", title="Predicted Travel Time (seconds)"),
                tooltip=[
                    alt.Tooltip("datetime:T", title="Time"),
                    alt.Tooltip("mean_travel_time:Q", title="Travel Time (sec)", format=".1f")
                ]
            )
            future_chart = ci_band + line_chart
            future_chart = future_chart.properties(width=700, height=400, title="Predicted Travel Times (Next 3 Hours)")
            st.altair_chart(future_chart)
        else:
            st.warning("Insufficient data for short-term predictions.")