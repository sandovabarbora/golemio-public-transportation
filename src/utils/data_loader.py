"""
Module: data_loader.py
Description: Provides functions for loading and merging stop times data and stops data.
"""

import os
import pandas as pd


def load_stop_data() -> pd.DataFrame:
    """
    Load stop times data. If 'latest_stop_times.csv' exists, load it; otherwise, load 'stop_times.csv'.
    Then merge with stops data from 'letna_stops.csv'.

    Returns:
        pd.DataFrame: Merged DataFrame containing stop times and stops information.
    """
    filename = "./data/latest_stop_times.csv" if os.path.exists("./data/latest_stop_times.csv") else "./data/stop_times.csv"
    stop_times = pd.read_csv(filename)

    # Convert columns to datetime, extract base_stop_id, and compute the date.
    stop_times = stop_times.assign(
        current_stop_departure=pd.to_datetime(
            stop_times['current_stop_departure'], utc=True, errors='coerce', infer_datetime_format=True
        ),
        current_stop_arrival=pd.to_datetime(
            stop_times['current_stop_arrival'], utc=True, errors='coerce', infer_datetime_format=True
        ),
        created_at=pd.to_datetime(
            stop_times['created_at'], utc=True, errors='coerce', infer_datetime_format=True
        ),
        updated_at=pd.to_datetime(
            stop_times['updated_at'], utc=True, errors='coerce', infer_datetime_format=True
        ),
        base_stop_id=stop_times['gtfs_stop_id'].str.extract(r'^(.*?)(?=[SZ])')[0],
        date=lambda df: df['current_stop_departure'].dt.date
    )

    stops_letna = pd.read_csv("./data/letna_stops.csv")
    merged_data = stop_times.merge(stops_letna, on='base_stop_id', how='inner')
    return merged_data
