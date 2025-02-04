# tabs/delay_predictions.py
import streamlit as st
import pandas as pd
from src.views.delay_predictions import render_delay_predictions as view_render_delay_predictions

def render_delay_predictions(data: pd.DataFrame, events_df: pd.DataFrame = None) -> None:
    """Wrapper for the Delay Predictions view."""
    view_render_delay_predictions(data, events_df)
