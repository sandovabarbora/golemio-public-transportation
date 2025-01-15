# Prague 7 Transit Analysis Dashboard

## Overview
A comprehensive transit analysis tool for Prague 7, focusing on public transportation delays, event impacts, and predictive analytics. This application helps monitor and analyze transportation patterns around key areas like Letná, providing valuable insights for transit management and urban planning.

## Features

### 1. Delay Statistics
- Real-time delay monitoring
- Interactive map visualization (Markers & Heatmap)
- Hourly trend analysis
- Date comparison tools
- Basic transit statistics

### 2. Event Impact Analysis
- Sparta Praha match impact tracking
- Cross-event analysis
- Weather impact integration
- Tourism pattern analysis
- Construction zone impact assessment

### 3. Predictive Analytics
- Machine learning-based delay predictions
- Travel advisory system
- Multi-factor impact analysis
- Confidence interval calculations
- Real-time recommendations

## Prerequisites
- Python 3.8+
- pip (Python package installer)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/prague7-transit-analysis.git
cd prague7-transit-analysis
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

## Required Files
Place these files in your project root directory:
- `stop_times.csv` - Transit stop timing data
- `letna_stops.csv` - Letná area stop information
- Match schedule CSV file (to be uploaded through the UI)

## Running the Application

1. Start the Streamlit server:
```bash
streamlit run app.py
```

2. Open your web browser and navigate to:
```
http://localhost:8501
```

## Project Structure

```
prague7-transit-analysis/
├── app.py                 # Main Streamlit application
├── src/
│   ├── event_analysis.py  # Event impact analysis
│   ├── predictions.py     # ML predictions
│   ├── data_processing.py # Data processing utilities
│   └── imports.py         # API imports and utilities
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Key Components

### Data Processing (`data_processing.py`)
- Stop information extraction
- Data normalization
- Coordinate processing

### Event Analysis (`event_analysis.py`)
- Match schedule processing
- Impact calculations
- Visualization tools
- Statistical analysis

### Predictions (`predictions.py`)
- ML model implementation
- Weather integration
- Construction impact analysis
- Tourism pattern processing

### Main Application (`app.py`)
- Streamlit UI implementation
- Interactive visualizations
- Real-time data processing
- Map generation

## Data Requirements

### Stop Times CSV Format
```csv
current_stop_departure,current_stop_arrival,created_at,updated_at,gtfs_stop_id,current_stop_dep_delay
2024-01-15 08:00:00,2024-01-15 07:59:00,2024-01-15 07:58:00,2024-01-15 07:58:00,12345S,60
```

### Letná Stops CSV Format
```csv
base_stop_id,stop_name,avg_latitude,avg_longitude
12345,Letná,50.1234,14.4321
```

## Usage Tips

1. **Data Upload**:
   - Use the sidebar to upload event schedule files
   - Ensure CSV files are in the correct format

2. **Map Navigation**:
   - Use the map type selector for different visualizations
   - Click markers for detailed stop information
   - Adjust time ranges using the slider

3. **Event Analysis**:
   - Upload match schedules for event impact analysis
   - Compare different dates for pattern analysis
   - Review recommendations based on predictions

4. **Predictions**:
   - Check the travel advisor for immediate guidance
   - Review detailed predictions for longer-term planning
   - Consider all impact factors in the analysis

## Contributing
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments
- Prague Public Transit Authority for data support
- Sparta Praha for match schedule information
- Prague 7 Municipal Office for project support

## Contact
For questions and support, please contact [your contact information]