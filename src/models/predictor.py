"""
Module: predictor.py
Description: Contains classes for predicting transport delays based on historical data.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy import stats
from typing import Optional, Dict, List


class DelayPredictor:
    """
    Predict delays using historical public transport data with error correction.
    """

    def __init__(self) -> None:
        self.data: Optional[pd.DataFrame] = None
        self.events_df: Optional[pd.DataFrame] = None
        self.peak_hours = set(range(7, 10)) | set(range(16, 19))
        self.confidence_level = 0.95
        self.recent_window_minutes = 60

    def load_data(self, data: pd.DataFrame, events_df: Optional[pd.DataFrame] = None) -> None:
        """
        Load and preprocess historical stop times and optionally event data.

        Parameters:
            data (pd.DataFrame): Historical stop times data.
            events_df (pd.DataFrame, optional): Event data (e.g., match schedules).
        """
        self.data = data.copy()
        # Ensure the datetime column is correctly parsed.
        if not pd.api.types.is_datetime64_any_dtype(self.data["current_stop_departure"]):
            self.data["current_stop_departure"] = pd.to_datetime(self.data["current_stop_departure"], errors="coerce")
        self.data.dropna(subset=["current_stop_departure"], inplace=True)
        self.data["hour"] = self.data["current_stop_departure"].dt.hour
        self.data["weekday"] = self.data["current_stop_departure"].dt.dayofweek
        self.data["is_weekend"] = self.data["weekday"].isin([5, 6])
        self.data.sort_values(["rt_trip_id", "gtfs_stop_sequence"], inplace=True)
        self.data["next_stop"] = self.data.groupby("rt_trip_id")["gtfs_stop_id"].shift(-1)

        if events_df is not None:
            self.events_df = events_df.copy()
            if not pd.api.types.is_datetime64_any_dtype(self.events_df["datetime"]):
                self.events_df["datetime"] = pd.to_datetime(self.events_df["datetime"], errors="coerce")
            self.events_df.dropna(subset=["datetime"], inplace=True)

    def compute_prediction(
        self, target_datetime: datetime, stop_id: Optional[str] = None, direction: Optional[int] = None
    ) -> Optional[Dict]:
        """
        Compute a delay prediction for a given datetime (and optional stop/direction).

        Parameters:
            target_datetime (datetime): The time for which to predict the delay.
            stop_id (str, optional): Base stop ID filter.
            direction (int, optional): Transport direction filter.

        Returns:
            Dict: A dictionary containing prediction details, or None if insufficient data.
        """
        target_dt = pd.Timestamp(target_datetime)
        if target_dt.tzinfo is None:
            target_dt = target_dt.tz_localize("UTC")
        target_hour = target_dt.hour
        target_weekday = target_dt.weekday()

        # Determine if the target day is a match/event day.
        is_match_day = False
        if self.events_df is not None:
            event_dates = set(self.events_df["datetime"].dt.date)
            is_match_day = target_dt.date() in event_dates

        # Filter the data for similar conditions.
        similar = self.data[(self.data["hour"] == target_hour) & (self.data["weekday"] == target_weekday)].copy()
        if direction is not None:
            similar = similar[similar["gtfs_direction_id"] == direction]
        if stop_id:
            similar = similar[similar["base_stop_id"] == stop_id]

        if len(similar) < 5:
            return None

        delays = similar["current_stop_dep_delay"]
        base_mean = delays.mean()
        std_delay = delays.std()
        sample_size = len(delays)
        t_val = stats.t.ppf((1 + self.confidence_level) / 2, sample_size - 1)
        margin = t_val * (std_delay / (sample_size ** 0.5))

        # Adjust prediction using recent data.
        recent_start = target_dt - timedelta(minutes=self.recent_window_minutes)
        recent = self.data[self.data["current_stop_departure"] >= recent_start]
        if stop_id:
            recent = recent[recent["base_stop_id"] == stop_id]
        if direction is not None:
            recent = recent[recent["gtfs_direction_id"] == direction]
        if len(recent) >= 3:
            recent_mean = recent["current_stop_dep_delay"].mean()
            error_corr = recent_mean - base_mean
        else:
            error_corr = 0

        adjusted_mean = base_mean + error_corr
        is_peak = target_hour in self.peak_hours

        reliability = self.calculate_reliability(adjusted_mean, margin, sample_size, is_peak, is_match_day)

        return {
            "datetime": target_dt,
            "mean_delay": adjusted_mean,
            "base_mean_delay": base_mean,
            "error_correction": error_corr,
            "median_delay": delays.median(),
            "std_delay": std_delay,
            "confidence_lower": adjusted_mean - margin,
            "confidence_upper": adjusted_mean + margin,
            "margin_error": margin,
            "sample_size": sample_size,
            "reliability": reliability,
            "is_match_day": is_match_day,
            "is_weekend": target_weekday in [5, 6],
            "is_peak_hour": is_peak,
        }

    def calculate_reliability(
        self, mean_delay: float, margin_error: float, sample_size: int, is_peak_hour: bool, is_match_day: bool
    ) -> float:
        """
        Calculate a reliability score (0-100%) for a prediction.

        Parameters:
            mean_delay (float): Adjusted mean delay.
            margin_error (float): Margin of error from the confidence interval.
            sample_size (int): Number of samples used.
            is_peak_hour (bool): Whether the target is during peak hour.
            is_match_day (bool): Whether the target day is an event/match day.

        Returns:
            float: Reliability score as a percentage.
        """
        sample_score = min(1.0, sample_size / 30)
        rel_ci = (2 * margin_error) / (abs(mean_delay) + 1)
        ci_score = 1 - min(1.0, rel_ci)
        cond_score = 1.0
        if is_peak_hour:
            cond_score *= 0.8
        if is_match_day:
            cond_score *= 0.9
        weights = {"sample_size": 0.4, "ci_width": 0.4, "conditions": 0.2}
        reliability = (weights["sample_size"] * sample_score +
                       weights["ci_width"] * ci_score +
                       weights["conditions"] * cond_score) * 100
        return round(reliability, 1)

    def generate_weekly_predictions(
        self, start_datetime: Optional[datetime] = None, stop_id: Optional[str] = None,
        direction: Optional[int] = None, interval_minutes: int = 15, min_reliability: float = 0.0
    ) -> List[Dict]:
        """
        Generate predictions over one week at specified intervals.

        Parameters:
            start_datetime (datetime, optional): Start time for predictions (defaults to now).
            stop_id (str, optional): Filter by stop ID.
            direction (int, optional): Filter by direction.
            interval_minutes (int): Time interval between predictions.
            min_reliability (float): Minimum reliability threshold.

        Returns:
            List[Dict]: List of prediction dictionaries.
        """
        if start_datetime is None:
            start_datetime = datetime.now()
        preds = []
        curr_dt = start_datetime.replace(minute=0, second=0, microsecond=0)
        end_dt = start_datetime + timedelta(days=7)
        while curr_dt < end_dt:
            pred = self.compute_prediction(curr_dt, stop_id, direction)
            if pred and pred["reliability"] >= min_reliability:
                pred["day_name"] = curr_dt.strftime("%A")
                if 7 <= curr_dt.hour <= 9:
                    pred["time_period"] = "Morning Peak"
                elif 16 <= curr_dt.hour <= 18:
                    pred["time_period"] = "Evening Peak"
                else:
                    pred["time_period"] = "Off-Peak"
                preds.append(pred)
            curr_dt += timedelta(minutes=interval_minutes)
        return preds

    def generate_short_term_predictions(
        self, start_datetime: Optional[datetime] = None, stop_id: Optional[str] = None,
        direction: Optional[int] = None, interval_minutes: int = 15, duration_hours: int = 3
    ) -> List[Dict]:
        """
        Generate short-term predictions for the next few hours.

        Parameters:
            start_datetime (datetime, optional): Start time for predictions.
            stop_id (str, optional): Filter by stop ID.
            direction (int, optional): Filter by direction.
            interval_minutes (int): Interval between predictions.
            duration_hours (int): Duration in hours to generate predictions.

        Returns:
            List[Dict]: List of prediction dictionaries including confidence intervals.
        """
        if start_datetime is None:
            start_datetime = datetime.now()
        preds = []
        curr_dt = start_datetime
        end_dt = start_datetime + timedelta(hours=duration_hours)
        while curr_dt < end_dt:
            pred = self.compute_prediction(curr_dt, stop_id, direction)
            if pred:
                preds.append({
                    "datetime": curr_dt,
                    "mean_delay": pred["mean_delay"],
                    "confidence_lower": pred["confidence_lower"],
                    "confidence_upper": pred["confidence_upper"]
                })
            curr_dt += timedelta(minutes=interval_minutes)
        return preds

    def get_next_stop(self, base_stop_id: str, direction: int) -> Optional[str]:
        """
        Retrieve the next stop name for a given base_stop_id and direction.

        Parameters:
            base_stop_id (str): The base stop ID.
            direction (int): The direction id.

        Returns:
            Optional[str]: The next stop name if available; otherwise, None.
        """
        df = self.data[
            (self.data["base_stop_id"] == base_stop_id) &
            (self.data["gtfs_direction_id"] == direction)
        ]
        next_stops = df["next_stop"].dropna()
        if not next_stops.empty:
            next_stop_id = next_stops.mode().iloc[0]
            # Extract the base stop ID from the next stop ID (everything before S or Z)
            next_base_id = next_stop_id.split('Z')[0].split('S')[0]
            # Get the corresponding stop name
            next_stop_df = self.data[self.data["base_stop_id"] == next_base_id]
            if not next_stop_df.empty:
                return next_stop_df["stop_name"].iloc[0]
        return None
    


class PredictionsDisplay:
    """
    Utility class to display predictions in a Streamlit interface.
    """

    @staticmethod
    def display_predictions(predictor: DelayPredictor) -> None:
        import streamlit as st
        import altair as alt

        stops = sorted(predictor.data["stop_name"].unique())
        selected_stop = st.selectbox("Select Transit Stop", options=stops)
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

        stop_id = predictor.data[predictor.data["stop_name"] == selected_stop]["base_stop_id"].iloc[0]
        next_stop = predictor.get_next_stop(stop_id, selected_direction)
        if next_stop:
            st.info(f"Next Stop in this direction: **{next_stop}**")
        else:
            st.info("Next Stop not found for this direction.")

        current_pred = predictor.compute_prediction(pred_datetime, stop_id, selected_direction)
        if current_pred is None:
            st.warning("Insufficient historical data for a current prediction.")
            return

        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "Predicted Delay",
                f"{current_pred['mean_delay']:.0f} sec",
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

        # Historical data chart.
        current_ts = pred_datetime
        last_week_start = current_ts - pd.Timedelta(days=7)
        historical_data = predictor.data[
            (predictor.data["base_stop_id"] == stop_id) &
            (predictor.data["gtfs_direction_id"] == selected_direction) &
            (predictor.data["current_stop_departure"] >= last_week_start) &
            (predictor.data["current_stop_departure"] < current_ts)
        ]
        if not historical_data.empty:
            hist_chart = alt.Chart(historical_data).mark_line(point=True).encode(
                x=alt.X("current_stop_departure:T", title="Time"),
                y=alt.Y("current_stop_dep_delay:Q", title="Delay (seconds)"),
                tooltip=[
                    alt.Tooltip("current_stop_departure:T", title="Time"),
                    alt.Tooltip("current_stop_dep_delay:Q", title="Delay (sec)", format=".1f")
                ]
            ).properties(width=700, height=400, title="Historical Delays (Last Week)")
            st.altair_chart(hist_chart)
        else:
            st.warning("No historical data available for last week.")

        # Short-term prediction chart.
        future_preds = predictor.generate_short_term_predictions(
            start_datetime=pred_datetime,
            stop_id=stop_id,
            direction=selected_direction,
            interval_minutes=15,
            duration_hours=3,
        )
        if future_preds:
            future_df = pd.DataFrame(future_preds)
            ci_band = alt.Chart(future_df).mark_area(opacity=0.3, color="lightblue").encode(
                x=alt.X("datetime:T", title="Time"),
                y=alt.Y("confidence_lower:Q", title="Predicted Delay (seconds)"),
                y2=alt.Y2("confidence_upper:Q")
            )
            line_chart = alt.Chart(future_df).mark_line(point=True, color="blue").encode(
                x=alt.X("datetime:T", title="Time"),
                y=alt.Y("mean_delay:Q", title="Predicted Delay (seconds)"),
                tooltip=[
                    alt.Tooltip("datetime:T", title="Time"),
                    alt.Tooltip("mean_delay:Q", title="Delay (sec)", format=".1f")
                ]
            )
            future_chart = ci_band + line_chart
            future_chart = future_chart.properties(width=700, height=400, title="Predicted Delays (Next 3 Hours)")
            st.altair_chart(future_chart)
        else:
            st.warning("Insufficient data for short-term predictions.")


def display_predictions_wrapper(predictor: DelayPredictor) -> None:
    """
    Module-level wrapper to display predictions via PredictionsDisplay.
    """
    PredictionsDisplay.display_predictions(predictor)
