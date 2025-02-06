"""
Module: azure_duckdb_connector.py
Description: Provides the AzureDuckDBConnector class which connects DuckDB to Azure Blob Storage
             using the Azure extension. The connector automatically sets up Azure and supports
             context management. It also provides methods to persist and incrementally update data.
"""

import os
import duckdb
import logging
import pandas as pd
from src.config import AZURE_TENANT_ID, AZURE_APP_ID, AZURE_CLIENT_SECRET, AZURE_STORAGE_NAME


class AzureDuckDBConnector:
    """
    Connects DuckDB to Azure Blob Storage using the Azure extension.
    Automatically sets up the Azure connection on initialization.
    """

    def __init__(self, db_path: str = "azure_data.duckdb") -> None:
        """
        Initialize the connector and set up the Azure integration.
        
        Parameters:
            db_path (str): Path to the DuckDB database. Defaults to "azure_data.duckdb".
                           For a persistent database, if the file does not exist or if the
                           required Azure secret is missing, the Azure setup is run and saved.
        """
        self.db_path = db_path
        persistent = (db_path != ":memory:")
        file_exists = persistent and os.path.exists(db_path)

        # Connect to DuckDB.
        self.conn = duckdb.connect(database=db_path, read_only=False)
        logging.info(f"DuckDB connected with db_path: {db_path}")

        if not persistent:
            logging.info("Using in-memory DB; running Azure setup...")
            self.setup_azure()
        else:
            if not file_exists:
                logging.info("Persistent DB file not found; initializing schema and Azure setup...")
                self.setup_azure()
                self.conn.commit()  # commit changes to disk.
            else:
                try:
                    # Try to verify if the required secret exists.
                    secrets_df = self.conn.sql("SHOW SECRETS;").df()
                    if "azure_spn" not in secrets_df.values:
                        logging.info("Azure secret not found in persistent DB; running Azure setup...")
                        self.setup_azure()
                        self.conn.commit()
                    else:
                        logging.info("Persistent DB file exists and Azure secret found; skipping Azure setup.")
                except Exception as e:
                    logging.warning("Could not verify secrets; running Azure setup. Error: " + str(e))
                    self.setup_azure()
                    self.conn.commit()

    def setup_azure(self) -> None:
        """
        Setup Azure Blob Storage integration in DuckDB by installing and loading
        the Azure extension, and creating a secret with the necessary credentials.
        """
        logging.info("Setting up Azure via DuckDB...")

        # Install and load the Azure extension.
        self.conn.sql("INSTALL azure;")
        self.conn.sql("LOAD azure;")

        # Create the Azure secret.
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
        try:
            self.conn.sql(secret_sql)
            logging.info("Azure secret created successfully.")
        except duckdb.duckdb.Error as e:
            if "already exists" in str(e):
                logging.info("Azure secret already exists; skipping creation.")
            else:
                raise

    def load_data(self, stop_ids: str, start_date: str = None) -> pd.DataFrame:
        """
        Load stop times data from Azure Blob Storage using DuckDB’s Azure extension.
        If a start_date is provided, perform incremental loading.
        
        Parameters:
            stop_ids (str): A comma-separated string of stop IDs, e.g., "'ID1','ID2','ID3'".
            start_date (str, optional): Timestamp in the format 'YYYY-MM-DD HH:MM:SS'.
        
        Returns:
            pd.DataFrame: DataFrame with the loaded data.
        """
        base_query = """
            SELECT *
            FROM 'azure://golem-data-lake-pid/vehiclepositions_stop_times_history/*/*/*/*.parquet'
            WHERE YEAR in (2024, 2025)
              AND gtfs_stop_id IN ({stop_ids})
        """
        if start_date:
            query = base_query + " AND current_stop_departure > TIMESTAMP '{start_date}'"
            query = query.format(stop_ids=stop_ids, start_date=start_date)
            logging.info(f"Querying incremental data (after {start_date}) for stop IDs: {stop_ids}")
        else:
            query = base_query.format(stop_ids=stop_ids)
            logging.info(f"Querying full data for stop IDs: {stop_ids}")

        logging.debug(f"Executing query: {query}")
        df = self.conn.sql(query).df()
        logging.info(f"Retrieved {len(df)} stop times records from Azure")
        return df

    def persist_data(self, stop_ids: str, start_date: str = None, table_name: str ="stop_times") -> None:
        """
        Loads data from Azure using the provided stop IDs (and optionally a start_date)
        and persists (inserts/appends) that data into a local table in the persistent DuckDB database.
        If the table does not exist, it is created; if it exists, new data is appended.
        
        Parameters:
            stop_ids (str): A comma-separated string of stop IDs.
            start_date (str, optional): Timestamp in the format 'YYYY-MM-DD HH:MM:SS'.
            table_name (str): Name of the local table where data will be persisted.
        """
        logging.info("Loading new data from Azure to persist locally...")
        new_data = self.load_data(stop_ids, start_date=start_date)

        # Check if the local persistent table exists by listing all tables.
        tables_df = self.conn.sql("SHOW TABLES;").df()
        table_list = tables_df.iloc[:, 0].tolist()  # Assuming the first column holds table names.
        if table_name not in table_list:
            logging.info(f"Table {table_name} does not exist. Creating table with new data.")
            self.conn.register("new_data", new_data)
            self.conn.sql(f"CREATE TABLE {table_name} AS SELECT * FROM new_data;")
            self.conn.unregister("new_data")
        else:
            logging.info(f"Table {table_name} exists. Appending new data.")
            self.conn.register("new_data", new_data)
            self.conn.sql(f"INSERT INTO {table_name} SELECT * FROM new_data;")
            self.conn.unregister("new_data")
        self.conn.commit()
        logging.info(f"Data persisted to table {table_name} successfully.")

    def update_incremental_data(self, stop_ids: str, table_name: str = "stop_times") -> None:
        """
        Checks the maximum current_stop_departure in the persistent table and loads new data from Azure
        starting from one second after that maximum value until today.
        If the table does not exist or is empty, all data is loaded.
        
        Parameters:
            stop_ids (str): A comma-separated string of stop IDs.
            table_name (str): The local table where data is persisted.
        """
        logging.info("Updating persistent data incrementally...")
        # Check if the table exists by listing tables.
        tables_df = self.conn.sql("SHOW TABLES;").df()
        table_list = tables_df.iloc[:, 0].tolist()  # assuming table names are in the first column
        if table_name not in table_list:
            logging.info(f"Table {table_name} does not exist. Loading all data from Azure.")
            self.persist_data(stop_ids, start_date=None, table_name=table_name)
        else:
            # Get the maximum current_stop_departure in the persistent table.
            max_date = self.conn.sql(f"SELECT MAX(current_stop_departure) FROM {table_name};").fetchone()[0]
            logging.info(f"Max current_stop_departure in {table_name}: {max_date}")
            if max_date is None:
                logging.info(f"Table {table_name} is empty. Loading all data from Azure.")
                self.persist_data(stop_ids, start_date=None, table_name=table_name)
            else:
                # Add one second to avoid duplicate records.
                new_start = pd.to_datetime(max_date) + pd.Timedelta(seconds=1)
                new_start_str = new_start.strftime("%Y-%m-%d %H:%M:%S")
                logging.info(f"Loading new data from Azure starting from {new_start_str}")
                self.persist_data(stop_ids, start_date=new_start_str, table_name=table_name)
        self.conn.commit()

    def save_stop_times_to_csv(self, stop_ids: str, output_file: str, start_date: str = None) -> None:
        """
        Retrieve stop times data and save them as a CSV file.
        
        Parameters:
            stop_ids (str): A comma-separated string of stop IDs.
            output_file (str): Path for the output CSV.
            start_date (str, optional): If provided, only load data after this timestamp.
        """
        logging.info(f"Saving stop times for stop IDs: {stop_ids} to CSV file: {output_file}")
        df = self.load_data(stop_ids, start_date=start_date)
        df.to_csv(output_file, index=False)
        logging.info(f"Stop times saved to {output_file}")

    def close(self) -> None:
        """Close the DuckDB connection."""
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
