"""
Module: azure_duckdb_connector.py
Description: Provides the AzureDuckDBConnector class which connects DuckDB to Azure Blob Storage
             using the Azure extension.
"""

import duckdb
import logging
import pandas as pd
from src.config import AZURE_TENANT_ID, AZURE_APP_ID, AZURE_CLIENT_SECRET, AZURE_STORAGE_NAME


class AzureDuckDBConnector:
    """
    Connects DuckDB to Azure Blob Storage using the Azure extension.
    """

    def __init__(self, db_path: str = ":memory:") -> None:
        """
        Initialize the connector.

        Parameters:
            db_path (str): Path to the DuckDB database. Defaults to in-memory.
        """
        self.conn = duckdb.connect(database=db_path, read_only=False)
        logging.info(f"DuckDB connected with db_path: {db_path}")

    def setup_azure(self) -> None:
        """
        Setup Azure Blob Storage integration in DuckDB by installing and loading
        the Azure extension, and creating a secret with the necessary credentials.
        """
        logging.info("Setting up Azure via DuckDB...")
        self.conn.sql("ATTACH 'public-transport.db';")
        self.conn.sql("INSTALL azure;")
        self.conn.sql("LOAD azure;")
        secret_sql = f"""
            CREATE SECRET azure_spn (
                TYPE AZURE,
                PROVIDER SERVICE_PRINCIPAL,
                TENANT_ID '{AZURE_TENANT_ID}',
                CLIENT_ID '{AZURE_APP_ID}',
                CLIENT_SECRET '{AZURE_CLIENT_SECRET}',
                ACCOUNT_NAME '{AZURE_STORAGE_NAME}'
            );
        """
        self.conn.sql(secret_sql)
        logging.info("Azure and DuckDB setup complete.")

    def get_stop_times(self, stop_ids: str) -> pd.DataFrame:
        """
        Retrieve stop times for the provided stop IDs.

        Parameters:
            stop_ids (str): A comma-separated string of stop IDs, e.g., "'ID1','ID2','ID3'".
        
        Returns:
            pd.DataFrame: DataFrame containing stop times data.
        """
        query = f"""
        SELECT *
        FROM 'azure://golem-data-lake-pid/vehiclepositions_stop_times_history/*/*/*/*.parquet'
        WHERE YEAR in (2024, 2025)
          AND gtfs_stop_id IN ({stop_ids})
        """
        logging.info(f"Querying stop times for stop IDs: {stop_ids}")
        logging.debug(f"Executing query: {query}")
        df = self.conn.sql(query).df()
        logging.info(f"Retrieved {len(df)} stop times records")
        return df

    def get_stop_times_incremental(self, stop_ids: str, start_date: str) -> pd.DataFrame:
        """
        Retrieve incremental stop times for the provided stop IDs starting after the given start_date.

        Parameters:
            stop_ids (str): A comma-separated string of stop IDs.
            start_date (str): Timestamp in the format 'YYYY-MM-DD HH:MM:SS'.
        
        Returns:
            pd.DataFrame: DataFrame containing new stop times data.
        """
        query = f"""
        SELECT *
        FROM 'azure://golem-data-lake-pid/vehiclepositions_stop_times_history/*/*/*/*.parquet'
        WHERE YEAR in (2024, 2025)
          AND gtfs_stop_id IN ({stop_ids})
          AND current_stop_departure > TIMESTAMP '{start_date}'
        """
        logging.info(f"Querying incremental stop times (after {start_date}) for stop IDs: {stop_ids}")
        df = self.conn.sql(query).df()
        logging.info(f"Retrieved {len(df)} new stop times records")
        return df

    def save_stop_times_to_csv(self, stop_ids: str, output_file: str) -> None:
        """
        Retrieve stop times for the given stop IDs and save them to a CSV file.

        Parameters:
            stop_ids (str): A comma-separated string of stop IDs.
            output_file (str): File path for the output CSV.
        """
        logging.info(f"Saving stop times for stop IDs: {stop_ids} to CSV file: {output_file}")
        df = self.get_stop_times(stop_ids)
        df.to_csv(output_file, index=False)
        logging.info(f"Stop times saved to {output_file}")
