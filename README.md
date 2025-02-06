# Public Transport Analysis Dashboard 🚌

A Streamlit-based dashboard for analyzing public transport delays and their relationship with sporting events. The application provides real-time insights, visualizations, and predictions for transport planners and analysts.

## Real-World Impact 🎯

> It's a Friday afternoon in December, and Aleš is finishing up his work at the office. As a data analyst in Prague and an avid fan of Sparta, he faces a common dilemma: how to maximize his work time without risking a late arrival at the stadium. With tonight's match approaching, he knows that public transportation delays can be unpredictable—especially with potential extra delays caused by increased traffic around Letná during event times and weather conditions. Therefore, Aleš pulls out the transit analysis dashboard, that he has been using for the entire season, and plans his journey thanks to its extraordinary predictive capabilities.


## Features 🌟
- **Real-time Delay Analysis**: Track and visualize current transport delays
- **Event Impact Assessment**: Analyze how sports events affect transport patterns
- **Interactive Maps**: View delay patterns through markers or heatmaps
- **Predictive Analytics**: Get short-term delay predictions with reliability scores

## System Requirements ⚙️
- Python 3.9 or higher
- Minimum 8GB RAM
- Docker (optional, for containerized deployment)
- Sufficient storage for data processing (minimum 10GB recommended)

## Quick Start 🚀

### Prerequisites
- Python 3.9 or higher
- Azure account with blob storage access
- Golemio API access token

### Installation Options

#### Local Setup
1. Clone the repository:
```bash
git clone https://github.com/yourusername/public-transport-analysis.git
cd public-transport-analysis
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
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

#### Docker Setup
1. Build the Docker image:
```bash
docker build -t transport-analysis .
```

2. Run the container:
```bash
docker run -p 8501:8501 --env-file .env transport-analysis
```

## Important Notes ⚠️

### Resource Requirements
- Memory usage can peak at 2-3GB during data processing
- Significant CPU usage for real-time calculations
- Regular cache clearing recommended for optimal performance

### Known Limitations
- Currently not deployable to cloud platforms (Heroku, Streamlit Cloud) due to memory requirements
- Large datasets require incremental processing
- Real-time updates may be affected by API rate limits

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
- [Prediction Methodology](docs/prediction.md)
- [Limitations and Future Work](docs/limitations.md)

## Project Structure 📁
```
public-transport-dashboard/
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose setup
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
├── data/                   # Data files
│   ├── letna_stops.csv
│   └── sparta_matches.csv
├── src/                    # Source code
│   ├── connectors/        # Data connectors
│   ├── models/           # Analysis models
│   ├── utils/            # Utility functions
│   └── views/            # Dashboard views
└── docs/                  # Documentation
```

## Performance Tips 💡
- Use date filters to limit data loading
- Enable caching for faster reloads
- Clear cache regularly for optimal performance
- Process data in smaller chunks
- Update data during off-peak hours

## Troubleshooting 🔧
Common issues and solutions:
1. **Memory Issues**: Reduce date range, clear cache, or restart application
2. **Data loading fails**: Check Azure credentials and connection
3. **Maps not displaying**: Verify internet connection and Folium installation
4. **Prediction errors**: Ensure sufficient historical data is available
5. **Performance issues**: Monitor resource usage, optimize query range

## Future Plans 🔮
- Integration with additional data sources (Waze, FCD, NDIC)
- Enhanced memory optimization
- Cloud deployment solutions
- Advanced analytics features

## Acknowledgments 🙏
We gratefully acknowledge the support of various AI tools that assisted with code optimization, as well as our data providers who made this project possible. However, the code base and the main idea still lies in our heads, and our heads only. Despite current technical and resource limitations, our work demonstrates the potential for comprehensive public transport analysis. We remain committed to continuous improvement through resource optimization, feature enhancement, and performance refinement as we work toward a more scalable solution. Moreover, let us thank Golemio Prague Data Platform for providing the data.
---
Made with ❤️ by Barbora and Vojtěch