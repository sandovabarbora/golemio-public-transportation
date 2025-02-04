# Public Transport Analysis Dashboard

## Project Overview
This project provides a comprehensive analysis of public transport delays around the Letná area in Prague, with a specific focus on the impact of Sparta Praha football matches on public transportation. The dashboard offers real-time delay predictions, statistical analysis, and event impact assessment.

## Use Case: Match Day Planning
Imagine Aleš, a data analyst in Prague and an avid Sparta fan. It's a Friday afternoon in December, and he's trying to maximize his productive time at the office while ensuring he won't miss kickoff at the stadium. Like many fans, he faces a common dilemma:

- When should he leave the office to arrive on time?
- How will the usual Friday rush hour affect his journey?
- What additional delays might the match day traffic cause?

Using our transit analysis dashboard, which he's relied on throughout the season, Aleš can:
1. Check predicted delays specific to match days
2. Compare current conditions with historical patterns
3. Make an informed decision about his departure time

This real-world scenario exemplifies why we built this tool - to help people like Aleš make data-driven decisions about their journey to Letná stadium, taking into account all variables that might affect public transport reliability.

## Key Features
- Real-time delay predictions using historical data
- Interactive visualization of transport delays
- Event impact analysis for Sparta Praha matches
- Automated data updates from Azure Blob Storage
- Match schedule scraping from Eurofotbal.cz


## Technical Requirements

### Python Version
- Python 3.9+ (developed and tested with Python 3.9.7)

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

4. Set up environment variables in a `.env` file:
```env
parquetAzureTenantID=your_tenant_id
parquetAzureAppID=your_app_id
parquetAzureClientSecret=your_client_secret
parquetStorageName=your_storage_name
X-Access-Token-Golemio=your_golemio_token
```

### Project Structure
```
├── app.py                  # Main Streamlit application
├── data/                   # Data directory
│   ├── letna_stops.csv    # Static stops data
│   └── sparta_matches.csv # Scraped match schedules
├── src/
│   ├── config.py          # Configuration and environment variables
│   ├── connectors/        # Database connectors
│   ├── data/              # Data processing modules
│   ├── models/            # Analysis and prediction models
│   ├── utils/             # Utility functions
│   └── views/             # Dashboard view components
├── tabs/                   # Tab components
└── requirements.txt       # Project dependencies
```

## Code Design Principles

### Pythonic Code
- EAFP (Easier to Ask for Forgiveness than Permission) principle applied throughout:
    - Type hints and docstrings for better code readability
    - Modular design with clear separation of concerns
    - Consistent naming conventions following PEP 8


### Data Analysis Features
1. **Delay Statistics**
   - Basic statistics (average, maximum delays)
   - Delay distribution visualization
   - Hourly trends with rush hour overlays
   - Interactive map view with delay heatmaps

2. **Event Analysis**
   - Match day vs. regular day comparison
   - Individual match impact analysis
   - Key findings and recommendations

3. **Delay Predictions**
   - Machine learning-based delay predictions
   - Confidence intervals and reliability metrics
   - Short-term and weekly forecasts

## Running the Project
1. Start the Streamlit application:
```bash
streamlit run app.py
```

2. Access the dashboard at `http://localhost:8501`

3. Features available:
   - View current delay statistics
   - Analyze event impact
   - Generate delay predictions
   - Update data from Azure
   - Scrape new match schedules

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit changes with meaningful messages
4. Push to the branch
5. Create a Pull Request

## Authors
- Vojtěch Strachota
- Barbora Šandová

## Acknowledgments
- Data provided by Golemio, Prague Data Platform
- Match schedules from Eurofotbal.cz