import requests
import logging
import duckdb
import os


def get_stops(base_url, token, stop_names):
    params = {
        'names[]': stop_names,
        'offset': 0
    }
    headers = {
        'accept': 'application/json',
        'X-Access-Token': token
    }
    response = requests.get(base_url, params=params, headers=headers)
    if response.status_code != 200:
        logging.error(f'Error: {response.status_code}')
        return

    return response.json()

def setup_azure_duckdb(duckdb_conn: duckdb.DuckDBPyConnection) -> None:
    duckdb_conn.sql(f"ATTACH 'public-transport.db';")
    duckdb_conn.sql('INSTALL azure; LOAD azure;')
    duckdb_conn.sql(f'''
        CREATE SECRET azure_spn (
            TYPE AZURE,
            PROVIDER SERVICE_PRINCIPAL,
            TENANT_ID '{os.getenv("parquetAzureTenantID")}',
            CLIENT_ID '{os.getenv("parquetAzureAppID")}',
            CLIENT_SECRET '{os.getenv("parquetAzureClientSecret")}',
            ACCOUNT_NAME '{os.getenv("parquetStorageName")}');
            ''')
    logging.info("Azure and DuckDB setup complete")
    
def get_stop_times_from_azure(duckdb_conn, stop_ids) -> pd.DataFrame:
    stop_times_sql_string = f'''
    SELECT * 
        FROM 'azure://golem-data-lake-pid/vehiclepositions_stop_times_history/*/*/*/*.parquet'
        WHERE YEAR = 2024 AND gtfs_stop_id IN ({stop_ids})
    '''
    logging.info("Getting stop times from Azure")
    return duckdb_conn.sql(stop_times_sql_string).df()