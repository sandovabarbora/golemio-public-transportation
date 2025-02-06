"""
Module: segment_processor.py
Description: Processes stop times data to create segments, process trip data, and summarize segments.
             Uses DuckDB for optimized in‐memory SQL processing.
"""

import duckdb
import pandas as pd


def create_segments_df(stop_times_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create segments (edges) based on stop times data using DuckDB window functions.

    The input DataFrame must include at least:
      - rt_trip_id
      - gtfs_stop_id
      - gtfs_stop_sequence

    Returns a DataFrame with columns:
      - rt_trip_id
      - previous_stop_id
      - current_stop_id
      - segment_id_full (concatenation of previous and current stop IDs)
      - segment_id_short (concatenation of the parts of the stop IDs before the first 'Z')
    """
    # Create an in-memory DuckDB connection and register the DataFrame
    conn = duckdb.connect(database=":memory:")
    conn.register("stop_times", stop_times_df)

    query = """
    WITH segments AS (
        SELECT 
            rt_trip_id,
            gtfs_stop_id,
            gtfs_stop_sequence,
            LAG(gtfs_stop_id) OVER (PARTITION BY rt_trip_id ORDER BY gtfs_stop_sequence) AS previous_stop_id
        FROM stop_times
    )
    SELECT 
        rt_trip_id,
        previous_stop_id,
        gtfs_stop_id AS current_stop_id,
        previous_stop_id || '_' || gtfs_stop_id AS segment_id_full,
        split_part(previous_stop_id, 'Z', 1) || '_' || split_part(gtfs_stop_id, 'Z', 1) AS segment_id_short
    FROM segments
    WHERE previous_stop_id IS NOT NULL
    ORDER BY rt_trip_id, gtfs_stop_sequence;
    """

    segments_df = conn.execute(query).fetchdf()
    conn.unregister("stop_times")
    conn.close()
    return segments_df


def process_trip_data_duckdb(stop_times_df: pd.DataFrame) -> pd.DataFrame:
    """
    Process trip data using DuckDB SQL window functions to calculate additional fields such as
    real departure, real arrival, travel times, and segment information.

    The input DataFrame should include the following columns:
      - rt_trip_id
      - gtfs_stop_id
      - gtfs_stop_sequence
      - stop_name
      - current_stop_departure (as datetime)
      - current_stop_dep_delay (in seconds, integer or float)
      - current_stop_arrival (as datetime)
      - current_stop_arr_delay (in seconds, integer or float; may be null)

    Returns a processed DataFrame containing additional calculated columns:
      - real_departure
      - real_arrival
      - real_travel_time_seconds
      - planned_travel_time_seconds
      - section_id (concatenation of previous and current stop IDs)
    """
    conn = duckdb.connect(database=":memory:")
    conn.register("stop_times", stop_times_df)

    # Use a two-step CTE: first compute the base real_departure and real_arrival,
    # then compute lag values.
    query = """
    WITH base AS (
        SELECT 
            *,
            current_stop_departure + INTERVAL '1 second' * CAST(current_stop_dep_delay AS BIGINT) AS real_departure,
            CASE 
              WHEN current_stop_arr_delay IS NOT NULL
                THEN current_stop_arrival + INTERVAL '1 second' * CAST(current_stop_arr_delay AS BIGINT)
              ELSE current_stop_departure + INTERVAL '1 second' * CAST(current_stop_dep_delay AS BIGINT)
            END AS real_arrival
        FROM stop_times
    ),
    calculated AS (
        SELECT 
            *,
            LAG(current_stop_departure) OVER (PARTITION BY rt_trip_id ORDER BY gtfs_stop_sequence) AS previous_stop_departure,
            LAG(current_stop_arrival) OVER (PARTITION BY rt_trip_id ORDER BY gtfs_stop_sequence) AS previous_stop_arrival,
            LAG(gtfs_stop_id) OVER (PARTITION BY rt_trip_id ORDER BY gtfs_stop_sequence) AS previous_stop_id,
            LAG(real_departure) OVER (PARTITION BY rt_trip_id ORDER BY gtfs_stop_sequence) AS real_previous_stop_departure
        FROM base
    )
    SELECT 
        *,
        EXTRACT(EPOCH FROM (real_arrival - real_previous_stop_departure)) AS real_travel_time_seconds,
        EXTRACT(EPOCH FROM (current_stop_arrival - previous_stop_departure)) AS planned_travel_time_seconds,
        previous_stop_id || '_' || gtfs_stop_id AS section_id
    FROM calculated
    ORDER BY rt_trip_id, gtfs_stop_sequence;
    """
    processed_df = conn.execute(query).fetchdf()
    conn.unregister("stop_times")
    conn.close()
    return processed_df


def summarize_segments(processed_trip_df: pd.DataFrame, trip_id: str) -> pd.DataFrame:
    """
    Summarize segments for a given trip based on the processed trip data.

    The function groups the data by segment (using section_id) and computes:
      - planned start and end times
      - actual (real) start and end times
      - travel times (planned and actual) in seconds
      - delay (difference between real and planned departure)

    Parameters:
        processed_trip_df (pd.DataFrame): DataFrame returned from process_trip_data_duckdb.
        trip_id (str): The trip identifier (rt_trip_id) to summarize.

    Returns:
        pd.DataFrame: A summary DataFrame with one row per segment.
    """
    trip_df = processed_trip_df[processed_trip_df['rt_trip_id'] == trip_id].copy()
    if trip_df.empty:
        print(f"No data found for trip: {trip_id}")
        return pd.DataFrame()

    # Group by the section_id to summarize each segment's start and end times
    summary = trip_df.groupby("section_id").agg(
        planned_start_time=("current_stop_departure", "first"),
        planned_end_time=("current_stop_arrival", "last"),
        actual_start_time=("real_departure", "first"),
        actual_end_time=("real_arrival", "last")
    ).reset_index()

    # Calculate travel times and delay in seconds
    summary["planned_travel_time_seconds"] = (
        summary["planned_end_time"] - summary["planned_start_time"]
    ).dt.total_seconds()
    summary["actual_travel_time_seconds"] = (
        summary["actual_end_time"] - summary["actual_start_time"]
    ).dt.total_seconds()
    summary["delay_seconds"] = (
        summary["actual_start_time"] - summary["planned_start_time"]
    ).dt.total_seconds()

    return summary


# For testing purposes, you can run this module directly.
if __name__ == "__main__":
    # Example: read sample stop times from a CSV file (adjust the path as needed)
    sample_data = pd.read_csv('data/latest_stop_times.csv', parse_dates=[
        'current_stop_departure', 'current_stop_arrival'
    ])
    
    # Create segments
    segments_df = create_segments_df(sample_data)
    print("=== Segments ===")
    print(segments_df.head())

    # Process trip data
    processed_trip = process_trip_data_duckdb(sample_data)
    print("\n=== Processed Trip Data ===")
    print(processed_trip.head())

    # Summarize segments for a specific trip (adjust the trip ID as needed)
    summary_df = summarize_segments(processed_trip, "trip1")
    print("\n=== Summary for trip1 ===")
    print(summary_df)
