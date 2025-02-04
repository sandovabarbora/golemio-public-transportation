# main.py
import os
import warnings
import streamlit as st
import pandas as pd

from src.utils.data_loader import load_stop_data
from src.utils.sidebar import render_sidebar

# Import the tab wrappers
from tabs.delay_statistics import render_delay_statistics
from tabs.event_analysis import render_event_analysis
from tabs.delay_predictions import render_delay_predictions

warnings.filterwarnings("ignore")


def load_events() -> pd.DataFrame:
    """
    Load events data from one of several sources:
      1. Session state (if already loaded)
      2. Uploaded file (via the sidebar)
      3. Local CSV file ("sparta_matches.csv")
    Returns:
      pd.DataFrame or None: The events DataFrame or None if not available.
    """
    # Check session state first
    if "events_df" in st.session_state:
        return st.session_state["events_df"]

    # Check if a file was uploaded via the sidebar
    event_file = st.session_state.get("event_file", None)
    if event_file is not None:
        from src.views.event_analysis import load_event_data
        events_df = load_event_data(event_file)
        st.session_state["events_df"] = events_df
        return events_df

    # Fallback: check if the local file exists
    if os.path.exists("data/sparta_matches.csv"):
        events_df = pd.read_csv("data/sparta_matches.csv")
        events_df["Date"] = pd.to_datetime(events_df["Date"], format='%d.%m.%Y', errors='coerce')
        events_df["Time"] = pd.to_datetime(events_df["Time"], format='%H:%M', errors='coerce').dt.time
        events_df["datetime"] = events_df.apply(
            lambda x: pd.Timestamp.combine(x["Date"].date(), x["Time"])
            if pd.notnull(x["Date"]) and pd.notnull(x["Time"]) else pd.NaT,
            axis=1
        )
        st.session_state["events_df"] = events_df
        return events_df

    return None


def main():
    st.title("Public Transport Analysis Dashboard")
    event_file = render_sidebar()
    if event_file:
        st.session_state["event_file"] = event_file

    data = load_stop_data()

    # Load event data from one of the available sources.
    events_df = load_events()
    tabs = st.tabs(["Delay Statistics", "Event Analysis", "Delay Predictions"])
    
    with tabs[0]:
        render_delay_statistics(data)
    with tabs[1]:
        if events_df is not None:
            render_event_analysis(data, events_df)
        else:
            st.info("Please upload or scrape Sparta Praha match schedule CSV to see event analysis.")
    with tabs[2]:
        render_delay_predictions(data, events_df)

    st.markdown("---")
    st.caption(f"Last updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    try:
        last_updated = pd.to_datetime(data['updated_at']).max().strftime('%Y-%m-%d %H:%M:%S')
        st.caption(f"Latest data from public transport: {last_updated}")
    except Exception:
        st.caption("Latest data timestamp unavailable.")


if __name__ == '__main__':
    main()
