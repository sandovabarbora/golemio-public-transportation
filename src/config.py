# src/config_local.py
import os
from dotenv import load_dotenv

load_dotenv()

AZURE_TENANT_ID = os.getenv("parquetAzureTenantID")
AZURE_APP_ID = os.getenv("parquetAzureAppID")
AZURE_CLIENT_SECRET = os.getenv("parquetAzureClientSecret")
AZURE_STORAGE_NAME = os.getenv("parquetStorageName")
GOLEMIO_TOKEN = os.getenv("X-Access-Token-Golemio")

