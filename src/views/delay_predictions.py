"""
Module: delay_predictions.py
Description: Renders the Delay Predictions view using the DelayPredictor model.
"""

import streamlit as st
import pandas as pd
from src.models.predictor import DelayPredictor, PredictionsDisplay
from src.models.segment_predictor import SegmentPredictor
from src.views.segment_display import SegmentPredictionsDisplay

def render_delay_predictions(data: pd.DataFrame, events_df: pd.DataFrame = None) -> None:
    st.header("Delay & Travel Time Predictions")
    
    prediction_type = st.radio(
        "Select Prediction Type",
        ["Stop Delays", "Segment Travel Times"],
        horizontal=True
    )
    
    if prediction_type == "Stop Delays":
        stop_predictor = DelayPredictor()
        stop_predictor.load_data(data, events_df)
        PredictionsDisplay.display_predictions(stop_predictor)
        
    else:  # Segment Travel Times
        segment_predictor = SegmentPredictor()
        segment_predictor.load_data(data, events_df)
        SegmentPredictionsDisplay.display_predictions(segment_predictor)
