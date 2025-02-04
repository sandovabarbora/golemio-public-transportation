"""
Module: delay_predictions.py
Description: Renders the Delay Predictions view using the DelayPredictor model.
"""

import streamlit as st
import pandas as pd
from src.models.predictor import DelayPredictor, PredictionsDisplay

def render_delay_predictions(data: pd.DataFrame, events_df: pd.DataFrame = None) -> None:
    """
    Render the Delay Predictions view.

    Parameters:
        data (pd.DataFrame): Historical stop times data.
        events_df (pd.DataFrame, optional): Event data (e.g., match schedules).
    """
    st.header("Delay Predictions")
    
    # Initialize and load the predictor model with data.
    predictor = DelayPredictor()
    predictor.load_data(data, events_df)
    
    # Use the model's built-in display functionality to render predictions.
    PredictionsDisplay.display_predictions(predictor)
