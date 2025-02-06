# Transport Delay Prediction Methodology

## Overview
This system predicts public transport delays using a hybrid approach that combines historical analysis with real-time error correction. The prediction model accounts for various factors including:
- Time of day
- Day of week
- Event impacts (e.g., sports matches)
- Recent delay patterns
- Peak hour effects

## Core Prediction Components

### 1. Base Prediction
The base prediction is calculated using historical data filtered for similar conditions:
- Same hour of day
- Same day of week
- Same direction (if specified)
- Same stop (if specified)

From this filtered dataset, we compute:
- Base mean delay
- Standard deviation
- Confidence intervals using Student's t-distribution
- Sample size for reliability assessment

### 2. Error Correction
The model implements a dynamic error correction mechanism that:
1. Analyzes recent data (previous 60 minutes)
2. Calculates the difference between recent actual delays and historical averages
3. Adjusts the base prediction using this error correction term:
```python
error_correction = recent_mean - base_mean
adjusted_prediction = base_mean + error_correction
```

### 3. Reliability Assessment
Each prediction includes a reliability score (0-100%) based on:
- Sample size (40% weight)
- Confidence interval width (40% weight)
- Conditions score (20% weight)

Reliability penalties are applied for:
- Peak hours (-20%)
- Match days (-10%)
- Small sample sizes
- Wide confidence intervals

## Prediction Types

### Short-term Predictions
- Generates predictions for the next 3 hours
- 15-minute intervals
- Includes confidence intervals
- Focuses on immediate traffic patterns

### Weekly Predictions
- Generates predictions across a full week
- Identifies patterns in:
  - Morning peak (7:00-9:00)
  - Evening peak (16:00-18:00)
  - Off-peak hours
- Filters low-reliability predictions

## Usage Examples

### Basic Prediction
```python
predictor = DelayPredictor()
predictor.load_data(historical_data, events_df)
prediction = predictor.compute_prediction(
    target_datetime=datetime.now(),
    stop_id="STOP123",
    direction=1
)
```

### Weekly Pattern Analysis
```python
weekly_predictions = predictor.generate_weekly_predictions(
    start_datetime=datetime.now(),
    stop_id="STOP123",
    interval_minutes=15,
    min_reliability=70.0
)
```

## Model Performance Metrics

The prediction includes several quality metrics:
- Confidence intervals (95% confidence level)
- Reliability score
- Sample size
- Error correction magnitude
- Peak/off-peak designation
- Event day impact

## Limitations and Considerations

1. Data Requirements
   - Minimum 5 historical samples for prediction
   - Recent data (within 60 minutes) for error correction
   - Event schedule for match day impacts

2. Known Limitations
   - Assumes similar patterns on same weekdays
   - Limited handling of special events beyond matches
   - Weather effects not directly modeled

3. Best Practices
   - Regular model retraining with new data
   - Monitoring of error correction magnitudes
   - Validation against actual delays
   - Use of reliability scores for filtering

## Future Improvements

Planned enhancements include:
1. Weather impact integration
2. Multiple event type handling
3. Dynamic reliability thresholds
4. Machine learning integration for pattern recognition
5. Automated model performance monitoring

## Related Components

The prediction system integrates with:
- Real-time data collection system
- Event scraping module
- DuckDB storage backend
- Streamlit visualization interface