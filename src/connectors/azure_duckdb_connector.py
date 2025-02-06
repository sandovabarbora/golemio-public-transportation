"""
Module: azure_duckdb_connector.py
Description: Provides the AzureDuckDBConnector class which connects DuckDB to Azure Blob Storage
             using the Azure extension. The connector automatically sets up Azure and supports
             context management.
"""

import duckdb
import logging
import pandas as pd
import urllib3
import os
import certifi

# Disable urllib3 warnings (for self-signed or other non-standard cert issues)
urllib3.disable_warnings()

# Ensure SSL_CERT_FILE is set before any network connections are made.
os.environ['SSL_CERT_FILE'] = certifi.where()

# Import Azure credentials and other configuration values from your config module.
from src.config import AZURE_TENANT_ID, AZURE_APP_ID, AZURE_CLIENT_SECRET, AZURE_STORAGE_NAME

# Optionally, if you want to use ClientSecretCredential for testing/debugging:
from azure.identity import ClientSecretCredential


class AzureDuckDBConnector:
    """
    Connects DuckDB to Azure Blob Storage using the Azure extension.
    Automatically sets up the Azure connection on initialization.
    """

    def __init__(self, db_path: str = ":memory:") -> None:
        """
        Initialize the connector and set up the Azure integration.

        Parameters:
            db_path (str): Path to the DuckDB database. Defaults to in-memory.
        """
        self.conn = duckdb.connect(database=db_path, read_only=False)
        logging.info(f"DuckDB connected with db_path: {db_path}")
        self.setup_azure()

    def setup_azure(self) -> None:
        """
        Setup Azure Blob Storage integration in DuckDB by installing and loading
        the Azure extension, and creating a secret with the necessary credentials.
        Handles the case where the external database is already attached and prevents secret re-creation.
        """
        logging.info("Setting up Azure via DuckDB...")

        # Attach an external database if necessary.
        try:
            self.conn.sql("ATTACH 'public-transport.db';")
        except Exception as e:
            if "Unique file handle conflict" in str(e):
                logging.info("Database 'public-transport.db' is already attached; skipping attach.")
            else:
                raise

        # Install and load the Azure extension.
        self.conn.sql("INSTALL azure;")
        self.conn.sql("LOAD azure;")

        # Optional: Acquire a token using ClientSecretCredential to verify connectivity.
        # This step is not required for DuckDB's integration but can help you debug SSL or credential issues.
        try:
            with ClientSecretCredential(
                tenant_id=AZURE_TENANT_ID,
                client_id=AZURE_APP_ID,
                client_secret=AZURE_CLIENT_SECRET
            ) as credential:
                # Acquire a token for Azure Storage (the default scope is "https://storage.azure.com/.default")
                token = credential.get_token("https://storage.azure.com/.default")
                logging.info("Successfully acquired token via ClientSecretCredential.")
                # You could log part of the token or its expiry if needed:
                logging.debug(f"Token expires at: {token.expires_on}")
        except Exception as ex:
            logging.error("Error acquiring token using ClientSecretCredential: %s", ex)
            # Depending on your use case, you might want to raise or handle the error here.
            raise

        # Create the Azure secret for DuckDB. DuckDB will use this secret for authentication.
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
                raise  # Reraise the exception if it's a different error.

    def load_data(self, stop_ids: str, start_date: str = None) -> pd.DataFrame:
        """
        Load stop times data from Azure Blob Storage using DuckDB’s Azure extension.
        If a start_date is provided, perform incremental loading (only records after the start_date).
        Otherwise, load the full dataset.

        Parameters:
            stop_ids (str): A comma-separated string of stop IDs, e.g., "'ID1','ID2','ID3'".
            start_date (str, optional): Timestamp in the format 'YYYY-MM-DD HH:MM:SS'. If provided,
                                        only records with current_stop_departure greater than start_date are loaded.

        Returns:
            pd.DataFrame: DataFrame containing the loaded stop times data.
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

    def save_stop_times_to_csv(self, stop_ids: str, output_file: str, start_date: str = None) -> None:
        """
        Retrieve stop times data for the given stop IDs and save them to a CSV file.

        Parameters:
            stop_ids (str): A comma-separated string of stop IDs.
            output_file (str): File path for the output CSV.
            start_date (str, optional): If provided, incremental loading is used.
        """
        logging.info(f"Saving stop times for stop IDs: {stop_ids} to CSV file: {output_file}")
        df = self.load_data(stop_ids, start_date=start_date)
        df.to_csv(output_file, index=False)
        logging.info(f"Stop times saved to {output_file}")

    def close(self) -> None:
        """
        Close the DuckDB connection.
        """
        self.conn.close()

    # Implement context manager support.
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
