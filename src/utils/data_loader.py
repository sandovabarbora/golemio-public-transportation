import os
import ast
import pandas as pd
import logging
import sys
import os
from src.connectors.azure_duckdb_connector import AzureDuckDBConnector
import streamlit as st

# Configure logging
logging.basicConfig(
   level=logging.INFO,
   format='%(asctime)s - %(levelname)s - %(message)s',
   handlers=[
       logging.StreamHandler(),
       logging.FileHandler('data_loader.log')
   ]
)

@st.cache_data(ttl=3600)
def load_stop_data() -> pd.DataFrame:
   logging.info("Starting data loading process")
   
   try:
       stops_letna_path = "./data/letna_stops.csv"
       if not os.path.exists(stops_letna_path):
           logging.error(f"Stops file not found: {stops_letna_path}")
           raise FileNotFoundError(f"Stops file not found: {stops_letna_path}")
           
       logging.info("Loading stops data from CSV")
       stops_letna = pd.read_csv(stops_letna_path)
       
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

       logging.info("Loading data from Azure via DuckDB")
       with AzureDuckDBConnector(db_path="azure_data.duckdb") as azure_connector:
           azure_data = azure_connector.load_data(stop_ids)
       logging.info(f"Loaded {len(azure_data)} records from Azure")

       logging.info("Processing retrieved data")
       processed_data = azure_data.assign(
           current_stop_departure=pd.to_datetime(
               azure_data['current_stop_departure'], utc=True, errors='coerce', infer_datetime_format=True
           ),
           current_stop_arrival=pd.to_datetime(
               azure_data['current_stop_arrival'], utc=True, errors='coerce', infer_datetime_format=True
           ),
           created_at=pd.to_datetime(
               azure_data['created_at'], utc=True, errors='coerce', infer_datetime_format=True
           ),
           updated_at=pd.to_datetime(
               azure_data['updated_at'], utc=True, errors='coerce', infer_datetime_format=True
           ),
           base_stop_id=azure_data['gtfs_stop_id'].str.extract(r'^(.*?)(?=[SZ])')[0],
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
   load_stop_data()