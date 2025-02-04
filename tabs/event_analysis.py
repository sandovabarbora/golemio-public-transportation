# tabs/event_analysis.py
import streamlit as st
import pandas as pd
from src.views.event_analysis import display_event_analysis

def render_event_analysis(data: pd.DataFrame, events_df: pd.DataFrame) -> None:
    """Wrapper for rendering event analysis."""
    display_event_analysis(data, events_df)
