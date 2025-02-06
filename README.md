# Public Transport Analysis Dashboard 🚌

A Streamlit-based dashboard for analyzing public transport delays and their relationship with sporting events. The application provides real-time insights, visualizations, and predictions for transport planners and analysts.

## Features 🌟

- **Real-time Delay Analysis**: Track and visualize current transport delays
- **Event Impact Assessment**: Analyze how sports events affect transport patterns
- **Interactive Maps**: View delay patterns through markers or heatmaps
- **Predictive Analytics**: Get short-term delay predictions with reliability scores

## Quick Start 🚀

### Prerequisites

- Python 3.9 or higher
- Azure account with blob storage access
- Golemio API access token

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/public-transport-analysis.git
cd public-transport-analysis
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your credentials:
```env
parquetAzureTenantID=your_tenant_id
parquetAzureAppID=your_app_id
parquetAzureClientSecret=your_client_secret
parquetStorageName=your_storage_name
X-Access-Token-Golemio=your_golemio_token
```

5. Run the application:
```bash
streamlit run app.py
```

## Dashboard Overview 📊

### 1. Delay Statistics
- Current delay patterns
- Historical trends
- Interactive map visualization
- Time-based filtering

### 2. Event Analysis
- Sports event impact assessment
- Before/after event comparisons
- Pattern identification
- Impact zone mapping

### 3. Delay Predictions
- Short-term delay forecasts
- Reliability scoring
- Pattern-based predictions
- Interactive trend visualization

## Data Sources 📂

The dashboard integrates data from multiple sources:
- Transport data from Azure Data Lake - stop times parquet files filtered to Prague 7, provided by Golemio
- Sports event schedules - scraping Sparta Prague matches from Eurofotbal.cz
- Stop information and geography data - Golemio API

## Documentation 📚

For detailed information, check out the docs folder:
- [Technical Documentation](docs/technical.md)
- [User Guide](docs/user_guide.md)
- [Deployment Guide](docs/deployment.md)
- [Prediction Methodlogy](docs/prediction.md)

## Project Structure 📁

```
public-transport-dashboard/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── data/                 # Data files
│   ├── letna_stops.csv
│   └── sparta_matches.csv
├── src/                  # Source code
│   ├── connectors/      # Data connectors
│   ├── models/          # Analysis models
│   ├── utils/           # Utility functions
│   └── views/           # Dashboard views
└── docs/                # Documentation
```

## Performance Tips 💡

- Use the date filters to limit data loading
- Enable caching for faster reloads
- Optimize map view based on your needs
- Update data during off-peak hours

## Troubleshooting 🔧

Common issues and solutions:
1. **Data loading fails**: Check Azure credentials and connection
2. **Maps not displaying**: Verify internet connection and Folium installation
3. **Prediction errors**: Ensure sufficient historical data is available

---
Made with ❤️ by Barbora and Vojtěch
