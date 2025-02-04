# src/data/event_data.py
import pandas as pd

def load_event_data(file_content) -> pd.DataFrame:
    """
    Load and process Sparta Praha match schedule from a semicolon-delimited CSV.
    
    Expected CSV columns (after header): Skip, Location, Date, Time, Opponent.
    
    Returns a DataFrame with:
      - 'Date' as datetime
      - 'Time' as a time object
      - 'datetime' as a combined datetime column
      - 'is_home' as a boolean (True if Location indicates home)
      - 'Opponent' with missing values filled as 'TBD'
    """
    df = pd.read_csv(
        file_content,
        sep=';',
        encoding='utf-8',
        names=['Skip', 'Location', 'Date', 'Time', 'Opponent'],
        skiprows=1
    )
    df.drop('Skip', axis=1, inplace=True)
    df['Date'] = pd.to_datetime(df['Date'], format='%d.%m.%Y', errors='coerce')
    df['Time'] = pd.to_datetime(df['Time'], format='%H:%M', errors='coerce').dt.time
    df['datetime'] = df.apply(
        lambda x: pd.Timestamp.combine(x['Date'], x['Time'])
        if pd.notnull(x['Date']) and pd.notnull(x['Time']) else pd.NaT,
        axis=1
    )
    # Ensure the datetime column is proper
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    df['is_home'] = df['Location'].str.strip().str.lower() == 'd'
    df['Opponent'] = df['Opponent'].fillna('TBD')
    return df
