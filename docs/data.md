# Data Sources and Processing Documentation

## Data Sources

### 1. Transport Data (from sample data)
The raw transport data includes fields e.g.:
```
- rt_trip_id: e.g., "2024-05-31T23:30:00+02:00_94_1867_240428_8278"
- gtfs_stop_id: e.g., "U100Z4P"
- current_stop_departure: Timestamp
- current_stop_dep_delay: Delay in seconds
- gtfs_route_short_name: e.g., "94", "911"
- gtfs_direction_id: 0 or 1
- vehicle_registration_number: e.g., "8278.0"
- gtfs_stop_sequence: Sequence number for stops
```

### 2. Stop Information (letna_stops.csv)
A CSV file containing rows with:
- stop_name
- avg_longitude
- avg_latitude
- base_stop_id
- all_stop_ids

### 3. Event Data (sparta_matches.csv)
Contains rows of match data with:
- Home Team
- Away Team
- Opponent
- is_home
- Competition
- Date and Time information

## Data Processing Pipeline

### 1. Basic Data Processing
From processing.py, the core data preparation includes:

```python
required_columns = [
    'rt_trip_id',
    'gtfs_stop_id',
    'current_stop_departure',
    'current_stop_dep_delay',
    'gtfs_stop_sequence',
    'gtfs_route_short_name',
    'gtfs_direction_id'
]
```

Key transformations:
1. Select only required columns
2. Convert departure times to datetime
3. Extract base_stop_id from gtfs_stop_id
4. Add date and hour columns

### 2. Stops Data Collection
The StopsFetcher class specifically focuses on 10 stops:
```python
self.stop_names = [
    "Hradčanská",
    "Sparta",
    "Korunovační",
    "Letenské náměstí",
    "Kamenická",
    "Strossmayerovo náměstí",
    "Nábřeží Kapitána Jaroše",
    "Vltavská",
    "Výstaviště",
    "Veletržní palác"
]
```

### 3. Data Storage

The system uses two DuckDB connectors:

#### Azure DuckDB Connector
- Connects to Azure Blob Storage
- Queries parquet files
- Filters for years 2024, 2025
- Supports incremental updates

#### Optimized DuckDB Connector
Creates optimized tables:
```sql
CREATE TABLE stops (
    base_stop_id VARCHAR PRIMARY KEY,
    stop_name VARCHAR NOT NULL,
    avg_latitude DOUBLE,
    avg_longitude DOUBLE,
    all_stop_ids VARCHAR
);

CREATE TABLE stop_times (
    rt_trip_id VARCHAR,
    gtfs_stop_id VARCHAR,
    current_stop_departure TIMESTAMP,
    current_stop_dep_delay INTEGER,
    gtfs_stop_sequence INTEGER,
    gtfs_route_short_name VARCHAR,
    gtfs_direction_id INTEGER,
    base_stop_id VARCHAR,
    date DATE,
    hour INTEGER
);
```

### 4. Event Data Collection
The scraper module:
- Scrapes Sparta Praha match schedule from Eurofotbal
- Processes match information
- Determines home/away status
- Saves to sparta_matches.csv

## Sample Data Analysis

From the provided transport data sample:
- Time range: Around midnight (23:30-00:41)
- Routes: 94, 97, 911, 93, 91, 907, 905
- Delays range from -22 to 216 seconds
- Mix of bus and tram services (gtfs_route_type)

## Actual Processing Flow

1. Data is either:
   - Retrieved from Azure storage (parquet files)
   - Or loaded from local CSV files

2. Stop data is processed to extract base IDs:
   - Uses regex pattern `^(.*?)(?=[SZ])`
   - Example: "U100Z4P" → "U100" as base_stop_id

3. Data is stored in DuckDB with:
   - Indexes on date and hour
   - Hourly statistics view
   - Batch processing (100,000 rows per batch)

4. Event data is either:
   - Scraped from website
   - Or loaded from existing sparta_matches.csv

## Performance Considerations

The actual implementation includes:
- Batch processing for large datasets
- Caching of stop information (LRU cache with max size 100)
- Indexes on frequently queried columns
- Materialized view for hourly statistics