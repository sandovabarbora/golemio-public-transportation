# User Guide
## Public Transport Analysis Dashboard

## Getting Started

### Installation Options

#### Local Installation
1. Clone the repository
2. Create virtual environment
3. Install dependencies
4. Set up environment variables
5. Run with `streamlit run app.py`

#### Docker Installation
1. Build Docker image
2. Set environment variables
3. Run container
4. Access via localhost:8501

### Dashboard Layout
- **Top**: Main title and navigation
- **Left**: Sidebar with filters and controls
- **Center**: Main visualization area
- **Bottom**: Additional information and updates

## Using the Dashboard

### Resource-Aware Usage

#### Optimal Performance
1. Use date filters to limit data load
2. Process data in smaller chunks
3. Clear cache when switching views

#### Memory Management
- Close unused tabs
- Regular cache clearing
- Limit concurrent operations

### Delay Statistics Tab

#### Map View
1. Choose your map type in the sidebar:
   - **Markers**: Individual stops with delay information
   - **Heatmap**: Heat visualization of delay patterns

2. Understanding the colors:
   - **Green**: Minimal delays (0-60 seconds)
   - **Yellow**: Moderate delays (60-120 seconds)
   - **Orange**: Significant delays (120-180 seconds)
   - **Red**: Severe delays (180+ seconds)

#### Time Filters
1. Use the sidebar to set:
   - Date range
   - Hour range
   - Specific days of week

#### Viewing Statistics
- Hover over markers for details
- Use charts for trends
- Check summary statistics

### Event Analysis Tab

#### Analyzing Event Impact
1. Select event date
2. View comparisons
3. Check impact zones

#### Understanding Reports
- **Impact Summary**: Overview
- **Time Analysis**: Delay periods
- **Recommendations**: Actions

#### Comparative Analysis
1. Use comparison option
2. Select baseline date
3. View statistics

### Delay Predictions Tab

#### Getting Predictions
1. Select stop
2. Choose direction
3. View predictions

#### Reading Predictions
- **Bold line**: Prediction
- **Shaded area**: Confidence
- **Score**: Reliability

## Data Management

### Efficient Data Loading
1. Use incremental loading
2. Apply necessary filters
3. Clear unused data

### Data Updates
1. Schedule during off-peak
2. Monitor memory usage
3. Verify successful update

## Performance Tips

### Optimization
- Filter data appropriately
- Clear cache regularly
- Monitor resource usage

### Common Tasks

#### Efficient Stop Search
1. Use search function
2. Apply relevant filters
3. Access stop details

#### Time Analysis
1. Set focused ranges
2. Compare specific periods
3. Identify patterns

#### Data Export
1. Export in chunks
2. Choose efficient format
3. Manage file sizes

## Best Practices

### For Analysis
- Use focused time ranges
- Process data incrementally
- Compare similar periods

### For Performance
- Monitor resource usage
- Clear cache regularly
- Use efficient filters

## Troubleshooting

### Common Issues

#### Memory Issues
- Reduce data range
- Clear application cache
- Restart application

#### Performance Issues
- Check resource usage
- Optimize query range
- Monitor system resources

#### Data Loading Issues
- Verify connection
- Check credentials
- Monitor logs

### Getting Help
- Check error logs
- Review documentation
- Contact support

## Technical Reference

### System Requirements
- Minimum 8GB RAM
- Modern web browser
- Network connection

### Performance Monitoring
- Resource usage
- Memory consumption
- Processing time

## Security

### Data Protection
- Encrypted storage
- Access logging
- Privacy controls

### Access Management
- Authentication
- Authorization
- Session control