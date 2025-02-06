# Streamlit Cloud Deployment Guide
## Public Transport Analysis Dashboard

### 1. Repository Setup
We deployed our application using GitHub and Streamlit Cloud. Here's how:

1. Created a GitHub repository with the following structure:
```
public-transport-analysis/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Dependencies
├── data/                 # Data files
│   ├── letna_stops.csv
│   └── sparta_matches.csv
└── src/                  # Source code
    ├── connectors/
    ├── models/
    ├── utils/
    └── views/
```

2. Ensured requirements.txt contains all necessary dependencies:
```text
streamlit==1.31.1
pandas==2.2.0
numpy==1.26.3
duckdb==0.9.2
requests==2.31.0
beautifulsoup4==4.12.3
folium==0.15.1
streamlit-folium==0.17.4
python-dotenv==1.0.1
scipy==1.12.0
scikit-learn==1.4.0
altair==5.2.0
```

### 2. Streamlit Cloud Deployment

1. Visited [share.streamlit.io](https://share.streamlit.io)
2. Logged in with GitHub account
3. Selected our repository from the list
4. Added environment variables in the Streamlit Cloud dashboard:
   - parquetAzureTenantID
   - parquetAzureAppID
   - parquetAzureClientSecret
   - parquetStorageName
   - X-Access-Token-Golemio

### 3. Application Access

After deployment:
1. Streamlit Cloud provided a public URL for the application
2. The dashboard is now accessible through this URL
3. Updates to the GitHub repository automatically trigger redeployment

### 4. Maintenance

To update the application:
1. Push changes to the GitHub repository
2. Streamlit Cloud automatically detects changes
3. Application redeploys with updates

### 5. Resources

- Application URL: https://golemio-public-transport.streamlit.app/
- GitHub Repository: https://github.com/sandovabarbora/golemio-public-transportation
- Documentation: See /docs folder in repository