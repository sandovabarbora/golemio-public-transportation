import os
import ast
import pandas as pd
import logging
import streamlit as st
from src.connectors.azure_duckdb_connector import AzureDuckDBConnector
import duckdb

# Configure logging: logs are written both to the console and to a file.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('data_loader.log')
    ]
)

@st.cache_resource(show_spinner=False)
def get_duckdb_connection(db_path: str = "azure_data.duckdb"):
    return duckdb.connect(database=db_path, read_only=False)

@st.cache_data(ttl=3600)
def load_stop_data(sample: bool = False) -> pd.DataFrame:
    """
    Loads and processes stops data from a CSV file and then merges the persisted
    DuckDB data with the stops data.
    
    Parameters:
        sample (bool): If True, only a subset of the data is loaded (e.g., LIMIT 10000 rows).
                       If False (default), all persisted data is loaded.
    
    Returns:
        pd.DataFrame: The merged dataset.
    """
    logging.info("Starting data loading process")
    try:
        # Define the path to your stops CSV file.
        stops_letna_path = "./data/letna_stops.csv"
        if not os.path.exists(stops_letna_path):
            logging.error(f"Stops file not found: {stops_letna_path}")
            raise FileNotFoundError(f"Stops file not found: {stops_letna_path}")
        logging.info("Loading stops data from CSV")
        stops_letna = pd.read_csv(stops_letna_path)

        # Process the stop IDs from the 'all_stop_ids' column.
        stop_ids_list = []
        logging.info("Processing stop IDs")
        for ids_str in stops_letna.get("all_stop_ids", []):
            try:
                ids = ast.literal_eval(ids_str)
                stop_ids_list.extend(ids)
            except Exception as e:
                logging.warning(f"Failed to parse stop ID: {ids_str}. Error: {str(e)}")
                stop_ids_list.append(ids_str)
        unique_stop_ids = sorted(set(stop_ids_list))
        stop_ids = ",".join([f"'{sid}'" for sid in unique_stop_ids])
        logging.info(f"Found {len(unique_stop_ids)} unique stop IDs")

        # Use the shared connection via st.cache_resource.
        conn = get_duckdb_connection("azure_data.duckdb")
        
        # Here we simply load the data from the persisted table.
        query = "SELECT * FROM stop_times order by current_stop_departure DESC"
        if sample:
            query += " LIMIT 300000"
            logging.info("Loading a sample of data (LIMIT 300000 rows)")
        else:
            logging.info("Loading all persisted data from the local table")
        local_data = conn.sql(query).df()
        logging.info(f"Loaded {len(local_data)} persisted records from local DuckDB table")

        logging.info("Processing retrieved data")
        processed_data = local_data.assign(
            current_stop_departure=pd.to_datetime(
                local_data['current_stop_departure'], utc=True, errors='coerce', infer_datetime_format=True
            ),
            current_stop_arrival=pd.to_datetime(
                local_data['current_stop_arrival'], utc=True, errors='coerce', infer_datetime_format=True
            ),
            created_at=pd.to_datetime(
                local_data['created_at'], utc=True, errors='coerce', infer_datetime_format=True
            ),
            updated_at=pd.to_datetime(
                local_data['updated_at'], utc=True, errors='coerce', infer_datetime_format=True
            ),
            base_stop_id=local_data['gtfs_stop_id'].str.extract(r'^(.*?)(?=[SZ])')[0],
            date=lambda df: df['current_stop_departure'].dt.date
        )

        logging.info("Merging with stops data")
        merged_data = processed_data.merge(stops_letna, on='base_stop_id', how='inner')
        logging.info(f"Final merged dataset has {len(merged_data)} records")
        return merged_data

    except Exception as e:
        logging.error(f"Error in load_stop_data: {str(e)}", exc_info=True)
        raise

if __name__ == '__main__':
    # For testing, you can call with sample=True to load only a subset.
    load_stop_data(sample=True)
