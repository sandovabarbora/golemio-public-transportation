"""
Module: optimized_duckdb_connector.py
Description: Provides the OptimizedDuckDBConnector class which sets up an optimized DuckDB
             environment with precomputed columns, indexes, materialized views, and caching.
"""

import duckdb
import logging
import pandas as pd
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Dict, Optional, List


class OptimizedDuckDBConnector:
    """
    Optimized DuckDB connector with materialized views and caching support.
    """

    def __init__(self, db_path: str = "transport_data.duckdb") -> None:
        """
        Initialize the connector and create the database schema if necessary.

        Parameters:
            db_path (str): Path to the DuckDB database.
        """
        self.db_path = db_path
        self.conn = duckdb.connect(database=db_path, read_only=False)
        self._setup_logging()
        self._initialize_schema()

    def _setup_logging(self) -> None:
        """
        Setup logging for the connector.
        """
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger(__name__)

    def _initialize_schema(self) -> None:
        """
        Create the necessary database schema including tables, indexes, and views.
        """
        try:
            # Create stops table.
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS stops (
                    base_stop_id VARCHAR PRIMARY KEY,
                    stop_name VARCHAR NOT NULL,
                    avg_latitude DOUBLE,
                    avg_longitude DOUBLE,
                    all_stop_ids VARCHAR
                );
            """)
            # Create stop_times table with precomputed date and hour columns.
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS stop_times (
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
            """)
            # Create indexes for performance.
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_stop_times_date ON stop_times(date);")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_stop_times_hour ON stop_times(hour);")
            # Create a view for hourly statistics.
            self.conn.execute("""
                CREATE OR REPLACE VIEW hourly_stats AS
                SELECT 
                    date,
                    hour,
                    gtfs_stop_id,
                    AVG(current_stop_dep_delay) AS avg_delay,
                    COUNT(*) AS count,
                    STDDEV(current_stop_dep_delay) AS std_delay
                FROM stop_times
                GROUP BY date, hour, gtfs_stop_id;
            """)
            self.logger.info("Schema initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing schema: {e}")
            raise

    def load_stops_data(self, stops_df: pd.DataFrame) -> None:
        """
        Load stops data into the 'stops' table.

        Parameters:
            stops_df (pd.DataFrame): DataFrame containing stops data.
        """
        try:
            self.conn.register('stops_temp', stops_df)
            self.conn.execute("""
                INSERT INTO stops 
                SELECT * FROM stops_temp 
                ON CONFLICT (base_stop_id) DO UPDATE 
                SET 
                    stop_name = EXCLUDED.stop_name,
                    avg_latitude = EXCLUDED.avg_latitude,
                    avg_longitude = EXCLUDED.avg_longitude,
                    all_stop_ids = EXCLUDED.all_stop_ids
            """)
            self.logger.info(f"Loaded {len(stops_df)} stops")
        except Exception as e:
            self.logger.error(f"Error loading stops data: {e}")
            raise

    def load_stop_times(self, stop_times_df: pd.DataFrame, batch_size: int = 100000) -> None:
        """
        Load stop times data into the 'stop_times' table in batches.

        Parameters:
            stop_times_df (pd.DataFrame): DataFrame containing stop times data.
            batch_size (int): Number of rows per batch.
        """
        try:
            # Import the data preparation function from the data processing module.
            from src.data.processing import prepare_stop_times_data
            prepared_df = prepare_stop_times_data(stop_times_df, include_base_stop_id=True)
            total_rows = len(prepared_df)
            for i in range(0, total_rows, batch_size):
                batch = prepared_df.iloc[i:i + batch_size]
                self.conn.register('stop_times_temp', batch)
                self.conn.execute("""
                    INSERT INTO stop_times 
                    SELECT * FROM stop_times_temp
                """)
                self.conn.unregister('stop_times_temp')
                self.logger.info(f"Loaded batch {i // batch_size + 1}/{(total_rows + batch_size - 1) // batch_size}")
        except Exception as e:
            self.logger.error(f"Error loading stop times: {e}")
            raise

    @lru_cache(maxsize=100)
    def get_stop_info(self, stop_id: str) -> Dict:
        """
        Retrieve cached stop information for a given base_stop_id.

        Parameters:
            stop_id (str): Base stop ID.
        
        Returns:
            Dict: Dictionary with stop information.
        """
        result = self.conn.execute("""
            SELECT * FROM stops WHERE base_stop_id = ?
        """, [stop_id]).fetchone()
        if result is None:
            return {}
        return dict(zip(
            ['base_stop_id', 'stop_name', 'avg_latitude', 'avg_longitude', 'all_stop_ids'], result
        ))

    def get_filtered_data(
        self, date: datetime.date, hour_range: tuple, stop_ids: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Retrieve filtered stop times data for a given date, hour range, and optionally, stop IDs.

        Parameters:
            date (datetime.date): The date for filtering.
            hour_range (tuple): A tuple (start_hour, end_hour) defining the hour range.
            stop_ids (List[str], optional): List of stop IDs to filter.
        
        Returns:
            pd.DataFrame: DataFrame with the filtered data.
        """
        try:
            query = """
                SELECT 
                    st.*,
                    s.stop_name,
                    s.avg_latitude,
                    s.avg_longitude
                FROM stop_times st
                JOIN stops s ON st.base_stop_id = s.base_stop_id
                WHERE st.date = ?
                  AND st.hour BETWEEN ? AND ?
            """
            params = [date, hour_range[0], hour_range[1]]
            if stop_ids:
                query += " AND st.gtfs_stop_id = ANY(?)"
                params.append(stop_ids)
            return self.conn.execute(query, params).df()
        except Exception as e:
            self.logger.error(f"Error getting filtered data: {e}")
            raise

    def get_delay_statistics(self, date: datetime.date) -> Dict:
        """
        Retrieve delay statistics for a given date.

        Parameters:
            date (datetime.date): Date for which to compute statistics.
        
        Returns:
            Dict: Dictionary containing average delay, standard deviation, total records, and unique stops.
        """
        try:
            stats = self.conn.execute("""
                SELECT 
                    AVG(current_stop_dep_delay) as avg_delay,
                    STDDEV(current_stop_dep_delay) as std_delay,
                    COUNT(*) as total_records,
                    COUNT(DISTINCT gtfs_stop_id) as unique_stops
                FROM stop_times
                WHERE date = ?
            """, [date]).fetchone()
            return {
                'avg_delay': stats[0],
                'std_delay': stats[1],
                'total_records': stats[2],
                'unique_stops': stats[3]
            }
        except Exception as e:
            self.logger.error(f"Error getting delay statistics: {e}")
            raise

    def close(self) -> None:
        """
        Close the DuckDB connection.
        """
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
