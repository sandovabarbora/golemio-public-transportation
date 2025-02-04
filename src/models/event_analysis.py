# src/models/event_analysis.py
import pandas as pd
from datetime import timedelta
import numpy as np
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

def get_comparison_data(data: pd.DataFrame, match_date) -> dict:
    """
    Given historical data and a match_date, return subsets of data for:
      - "Match Day"
      - "Day Before"
      - "Day After"
      - "Week Before"
      - "Week After"
    """
    return {
        "Match Day": data[data["date"] == match_date],
        "Day Before": data[data["date"] == match_date - timedelta(days=1)],
        "Day After": data[data["date"] == match_date + timedelta(days=1)],
        "Week Before": data[data["date"] == match_date - timedelta(days=7)],
        "Week After": data[data["date"] == match_date + timedelta(days=7)]
    }

def analyze_event_impact(data: pd.DataFrame, events_df: pd.DataFrame):
    """
    Analyze the impact of events on transport delays.
    
    Assumes:
      - data["current_stop_departure"] is datetime.
      - events_df["datetime"] is a proper datetime column.
      
    Returns a tuple (event_stats, hourly_stats):
      - event_stats: aggregate metrics comparing event vs. non-event days.
      - hourly_stats: hourly delay statistics segmented by event occurrence.
    """
    data["date"] = data["current_stop_departure"].dt.date
    events_df["datetime"] = pd.to_datetime(events_df["datetime"], errors="coerce")
    events_df = events_df.dropna(subset=["datetime"])
    events_df["date"] = events_df["datetime"].dt.date
    data["is_event"] = data["date"].isin(events_df["date"])
    
    event_stats = data.groupby("is_event").agg({
        "current_stop_dep_delay": [
            ("avg_delay", "mean"),
            ("median_delay", "median"),
            ("max_delay", "max"),
            ("min_delay", "min"),
            ("std_delay", "std"),
            ("total_records", "count")
        ]
    }).reset_index()
    event_stats.columns = ["is_event", "avg_delay", "median_delay", "max_delay", "min_delay", "std_delay", "total_records"]
    
    event_delays = data[data["is_event"]]["current_stop_dep_delay"]
    non_event_delays = data[~data["is_event"]]["current_stop_dep_delay"]
    if len(event_delays) > 1 and len(non_event_delays) > 1:
        t_stat, p_value = stats.ttest_ind(event_delays, non_event_delays, equal_var=False)
    else:
        t_stat, p_value = None, None
    event_stats["t_statistic"] = t_stat
    event_stats["p_value"] = p_value
    if len(event_delays) > 0 and len(non_event_delays) > 0:
        pooled_std = np.sqrt((event_delays.std() ** 2 + non_event_delays.std() ** 2) / 2)
        cohen_d = (event_delays.mean() - non_event_delays.mean()) / pooled_std
    else:
        cohen_d = None
    event_stats["effect_size"] = cohen_d
    
    hourly_stats = data.groupby(["is_event", data["current_stop_departure"].dt.hour]).agg({
        "current_stop_dep_delay": ["mean", "median", "std", "count"]
    }).reset_index()
    hourly_stats.columns = ["is_event", "hour", "mean_delay", "median_delay", "std_delay", "count"]
    hourly_stats["day_type"] = hourly_stats["is_event"].map({True: "Match Days", False: "Regular Days"})
    
    return event_stats, hourly_stats

def identify_delay_patterns(data: pd.DataFrame):
    """
    Identify delay patterns using clustering (KMeans).
    
    Returns:
      tuple: (cluster_stats, features)
    """
    features = pd.DataFrame({
        "hour": data["current_stop_departure"].dt.hour,
        "delay": data["current_stop_dep_delay"],
        "weekday": data["current_stop_departure"].dt.weekday,
    }).dropna()
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)
    n_clusters = 3
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    clusters = kmeans.fit_predict(features_scaled)
    features["cluster"] = clusters
    cluster_stats = features.groupby("cluster").agg({
        "delay": ["mean", "std", "count"],
        "hour": ["mean", "std"],
        "weekday": "mean",
    }).round(2)
    return cluster_stats, features
