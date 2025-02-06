# segment_predictor.py

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy import stats
from typing import Optional, Dict, List


class SegmentPredictor:
    def __init__(self) -> None:
        self.data: Optional[pd.DataFrame] = None
        self.events_df: Optional[pd.DataFrame] = None
        self.peak_hours = set(range(7, 10)) | set(range(16, 19))
        self.confidence_level = 0.95
        self.recent_window_minutes = 60

    def load_data(self, data: pd.DataFrame, events_df: Optional[pd.DataFrame] = None) -> None:
        self.data = data.copy()
        self.data = self._process_segments(self.data)
        self.events_df = events_df

    def _process_segments(self, data: pd.DataFrame) -> pd.DataFrame:
        from src.models.segment_processor import create_segments_df, process_trip_data_duckdb
        
        segments_df = create_segments_df(data)
        processed_data = process_trip_data_duckdb(data)
        
        merged_data = processed_data.merge(
            segments_df[['rt_trip_id', 'segment_id_full', 'segment_id_short']],
            on='rt_trip_id',
            how='inner'
        )
        
        return merged_data

    def compute_segment_prediction(
        self, target_datetime: datetime, segment_id: str, direction: Optional[int] = None
    ) -> Optional[Dict]:
        target_dt = pd.Timestamp(target_datetime)
        if target_dt.tzinfo is None:
            target_dt = target_dt.tz_localize("UTC")
        target_hour = target_dt.hour
        target_weekday = target_dt.weekday()

        similar = self.data[
            (self.data['segment_id_short'] == segment_id) &
            (self.data['current_stop_departure'].dt.hour == target_hour) &
            (self.data['current_stop_departure'].dt.weekday == target_weekday)
        ]
        
        if direction is not None:
            similar = similar[similar['gtfs_direction_id'] == direction]

        if len(similar) < 5:
            return None

        travel_times = similar['real_travel_time_seconds']
        base_mean = travel_times.mean()
        std_time = travel_times.std()
        sample_size = len(travel_times)
        
        t_val = stats.t.ppf((1 + self.confidence_level) / 2, sample_size - 1)
        margin = t_val * (std_time / (sample_size ** 0.5))

        recent_start = target_dt - timedelta(minutes=self.recent_window_minutes)
        recent = self.data[
            (self.data['segment_id_short'] == segment_id) &
            (self.data['current_stop_departure'] >= recent_start)
        ]
        if direction is not None:
            recent = recent[recent['gtfs_direction_id'] == direction]

        if len(recent) >= 3:
            recent_mean = recent['real_travel_time_seconds'].mean()
            error_corr = recent_mean - base_mean
        else:
            error_corr = 0

        adjusted_mean = base_mean + error_corr
        is_peak = target_hour in self.peak_hours
        is_match_day = False
        
        if self.events_df is not None:
            event_dates = set(self.events_df['datetime'].dt.date)
            is_match_day = target_dt.date() in event_dates

        reliability = self._calculate_reliability(
            adjusted_mean, margin, sample_size, is_peak, is_match_day
        )

        return {
            'datetime': target_dt,
            'mean_travel_time': adjusted_mean,
            'base_mean_travel_time': base_mean,
            'error_correction': error_corr,
            'median_travel_time': travel_times.median(),
            'std_travel_time': std_time,
            'confidence_lower': adjusted_mean - margin,
            'confidence_upper': adjusted_mean + margin,
            'margin_error': margin,
            'sample_size': sample_size,
            'reliability': reliability,
            'is_match_day': is_match_day,
            'is_weekend': target_weekday in [5, 6],
            'is_peak_hour': is_peak,
        }

    def _calculate_reliability(
        self, mean_time: float, margin_error: float, sample_size: int,
        is_peak_hour: bool, is_match_day: bool
    ) -> float:
        sample_score = min(1.0, sample_size / 30)
        rel_ci = (2 * margin_error) / (abs(mean_time) + 1)
        ci_score = 1 - min(1.0, rel_ci)
        
        cond_score = 1.0
        if is_peak_hour:
            cond_score *= 0.8
        if is_match_day:
            cond_score *= 0.9
            
        weights = {'sample_size': 0.4, 'ci_width': 0.4, 'conditions': 0.2}
        reliability = (
            weights['sample_size'] * sample_score +
            weights['ci_width'] * ci_score +
            weights['conditions'] * cond_score
        ) * 100
        
        return round(reliability, 1)

    def generate_short_term_predictions(
        self, start_datetime: Optional[datetime] = None,
        segment_id: Optional[str] = None,
        direction: Optional[int] = None,
        interval_minutes: int = 15,
        duration_hours: int = 3
    ) -> List[Dict]:
        if start_datetime is None:
            start_datetime = datetime.now()
            
        preds = []
        curr_dt = start_datetime
        end_dt = start_datetime + timedelta(hours=duration_hours)
        
        while curr_dt < end_dt:
            pred = self.compute_segment_prediction(curr_dt, segment_id, direction)
            if pred:
                preds.append({
                    'datetime': curr_dt,
                    'mean_travel_time': pred['mean_travel_time'],
                    'confidence_lower': pred['confidence_lower'],
                    'confidence_upper': pred['confidence_upper']
                })
            curr_dt += timedelta(minutes=interval_minutes)
            
        return preds