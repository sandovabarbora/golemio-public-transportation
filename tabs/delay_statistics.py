# tabs/delay_statistics.py
import streamlit as st
import pandas as pd
from src.views.delay_statistics import render_delay_statistics as view_render_delay_statistics

def render_delay_statistics(data: pd.DataFrame) -> None:
    """Wrapper for the Delay Statistics view."""
    view_render_delay_statistics(data)
