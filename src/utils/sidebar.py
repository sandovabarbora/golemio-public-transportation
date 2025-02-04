# src/utils/sidebar.py
import os
import ast
import streamlit as st
import pandas as pd
from datetime import timedelta
from typing import Optional

from src.connectors.azure_duckdb_connector import AzureDuckDBConnector
from src.data.scraper import scrape_sparta_matches


def download_azure_data() -> None:
    """
    Download new stop times data from Azure and update the local CSV.
    """
    try:
        stops_df = pd.read_csv("./data/letna_stops.csv")
        stop_ids_list = []
        for ids_str in stops_df["all_stop_ids"]:
            try:
                # Convert string representation of a list into an actual list
                ids = ast.literal_eval(ids_str)
                stop_ids_list.extend(ids)
            except Exception:
                stop_ids_list.append(ids_str)
        unique_stop_ids = sorted(set(stop_ids_list))
        # Build comma-separated list with quotes: "'ID1','ID2',..."
        stop_ids = ",".join([f"'{sid}'" for sid in unique_stop_ids])
        
        azure_connector = AzureDuckDBConnector(db_path="azure_data.duckdb")
        azure_connector.setup_azure()

        if os.path.exists("./data/latest_stop_times.csv"):
            existing_df = pd.read_csv("./data/latest_stop_times.csv")
            existing_df["current_stop_departure"] = pd.to_datetime(
                existing_df["current_stop_departure"], utc=True,
                errors='coerce', infer_datetime_format=True
            )
            max_date = existing_df["current_stop_departure"].max()
            max_date_str = (max_date.strftime("%Y-%m-%d %H:%M:%S")
                            if pd.notnull(max_date) else "1900-01-01 00:00:00")
            new_df = azure_connector.get_stop_times_incremental(stop_ids, max_date_str)
            if new_df.empty:
                st.info("No new records found from Azure.")
            else:
                merged_df = pd.concat([existing_df, new_df]).drop_duplicates()
                merged_df.to_csv("./data/latest_stop_times.csv", index=False)
                st.success(f"Downloaded and merged {len(new_df)} new records from Azure.")
        else:
            azure_connector.save_stop_times_to_csv(stop_ids, "latest_stop_times.csv")
            st.success("Downloaded full data from Azure to latest_stop_times.csv")
    except Exception as e:
        st.error(f"Error during Azure data download: {e}")


def scrape_event_data() -> None:
    """
    Scrape the latest Sparta match schedule and update the events data.
    """
    matches_df = scrape_sparta_matches()
    if not matches_df.empty:
        matches_df.to_csv("data/sparta_matches.csv", index=False)
        st.session_state["events_df"] = matches_df
        st.success("Scraped latest Sparta matches and updated events data.")
    else:
        st.error("Failed to scrape Sparta matches.")


def render_sidebar() -> Optional[pd.DataFrame]:
    """
    Render the sidebar for updating data and scraping event data.
    
    Returns:
        Optional[pd.DataFrame]: The uploaded event file, if provided.
    """
    with st.sidebar:
        st.header("Data Update")
        if st.button("Download New Data from Azure"):
            download_azure_data()

        st.header("Event Data")
        if st.button("Scrape Latest Sparta Matches"):
            scrape_event_data()
            
        event_file = st.file_uploader("Upload Sparta Praha Match Schedule", type=['csv'])
        return event_file
