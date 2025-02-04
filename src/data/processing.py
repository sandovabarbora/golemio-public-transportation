"""
Module: processing.py
Description: Contains functions for processing public transport stop times data.
"""

import pandas as pd


def prepare_stop_times_data(df: pd.DataFrame, include_base_stop_id: bool = True) -> pd.DataFrame:
    """
    Prepare stop times data by selecting required columns, converting datetime fields,
    and computing additional columns for date and hour.

    Parameters:
        df (pd.DataFrame): Raw stop times data.
        include_base_stop_id (bool): If True, extracts a base stop id from gtfs_stop_id. Default is True.

    Returns:
        pd.DataFrame: Processed DataFrame with selected columns, plus 'date' and 'hour' columns.
    """
    required_columns = [
        'rt_trip_id',
        'gtfs_stop_id',
        'current_stop_departure',
        'current_stop_dep_delay',
        'gtfs_stop_sequence',
        'gtfs_route_short_name',
        'gtfs_direction_id'
    ]
    
    df_filtered = df[required_columns].copy()
    
    # Convert the 'current_stop_departure' column to datetime.
    df_filtered['current_stop_departure'] = pd.to_datetime(
        df_filtered['current_stop_departure'], 
        errors='coerce',
        infer_datetime_format=True
    )
    
    # Optionally extract a base stop id from the gtfs_stop_id (everything before an "S" or "Z")
    if include_base_stop_id:
        df_filtered['base_stop_id'] = df_filtered['gtfs_stop_id'].str.extract(r'^(.*?)(?=[SZ])')
    
    # Precompute additional columns for date and hour.
    df_filtered['date'] = df_filtered['current_stop_departure'].dt.date
    df_filtered['hour'] = df_filtered['current_stop_departure'].dt.hour

    return df_filtered
