# Technical Methodology: Transit Delay Analysis

## Table of Contents
1. [Statistical Analysis](#statistical-analysis)
2. [Prediction Methodology](#prediction-methodology)
3. [Error Correction Approach](#error-correction-approach)
4. [Event Impact Analysis](#event-impact-analysis)
5. [Performance Metrics](#performance-metrics)

## Statistical Analysis

### Basic Delay Statistics
- **Temporal Aggregation**: Data is aggregated at multiple levels:
  - Hourly averages
  - Daily patterns
  - Weekly trends
  - Event-specific statistics

- **Key Metrics**:
  ```python
  {
      'avg_delay': mean delay in seconds,
      'std_delay': standard deviation of delays,
      'total_records': number of observations,
      'unique_stops': count of distinct stops
  }
  ```

### Statistical Significance Testing
- **T-tests** for comparing match days vs. regular days
- **Cohen's d** for effect size measurement
- **Confidence Intervals**: 95% CI for all predictions
```python
t_stat, p_value = stats.ttest_ind(event_delays, non_event_delays, equal_var=False)
pooled_std = np.sqrt((event_delays.std() ** 2 + non_event_delays.std() ** 2) / 2)
cohen_d = (event_delays.mean() - non_event_delays.mean()) / pooled_std
```

## Prediction Methodology

### Core Prediction Model
The `DelayPredictor` class implements a sophisticated prediction system with the following components:

1. **Historical Pattern Analysis**
```python
similar = self.data[
    (self.data["hour"] == target_hour) & 
    (self.data["weekday"] == target_weekday)
].copy()
```

2. **Base Prediction**
```python
base_mean = delays.mean()
std_delay = delays.std()
margin = t_val * (std_delay / (sample_size ** 0.5))
```

3. **Confidence Intervals**
- Using Student's t-distribution for small sample sizes
- 95% confidence level by default
- Margin of error calculation incorporating sample size

### Feature Engineering
Key features used in predictions:
- Hour of day
- Day of week
- Event occurrence
- Peak hours (7-10 AM, 16-19 PM)
- Recent delay patterns

## Error Correction Approach

### Real-time Error Correction
The system implements a dynamic error correction mechanism:

1. **Recent Window Analysis**
```python
recent_window_minutes = 60
recent_start = target_dt - timedelta(minutes=self.recent_window_minutes)
recent = self.data[self.data["current_stop_departure"] >= recent_start]
```

2. **Error Calculation**
```python
if len(recent) >= 3:
    recent_mean = recent["current_stop_dep_delay"].mean()
    error_corr = recent_mean - base_mean
else:
    error_corr = 0
```

3. **Adjusted Prediction**
```python
adjusted_mean = base_mean + error_corr
```

### Reliability Scoring
Each prediction includes a reliability score (0-100%) based on:

```python
def calculate_reliability(
    self, mean_delay: float, margin_error: float, 
    sample_size: int, is_peak_hour: bool, is_match_day: bool
) -> float:
    sample_score = min(1.0, sample_size / 30)
    rel_ci = (2 * margin_error) / (abs(mean_delay) + 1)
    ci_score = 1 - min(1.0, rel_ci)
    
    # Condition adjustments
    cond_score = 1.0
    if is_peak_hour:
        cond_score *= 0.8
    if is_match_day:
        cond_score *= 0.9
        
    # Weighted combination
    weights = {
        "sample_size": 0.4,
        "ci_width": 0.4,
        "conditions": 0.2
    }
    reliability = (
        weights["sample_size"] * sample_score +
        weights["ci_width"] * ci_score +
        weights["conditions"] * cond_score
    ) * 100
    
    return round(reliability, 1)
```

## Event Impact Analysis

### Match Day Analysis
1. **Pre-match Period**: 3 hours before kickoff
2. **Post-match Period**: 2 hours after final whistle
3. **Comparison Periods**:
   - Same day/time in previous week
   - Same day/time in following week

### Impact Metrics
```python
event_stats = data.groupby("is_event").agg({
    "current_stop_dep_delay": [
        ("avg_delay", "mean"),
        ("median_delay", "median"),
        ("max_delay", "max"),
        ("min_delay", "min"),
        ("std_delay", "std"),
        ("total_records", "count")
    ]
})
```

## Performance Metrics

### Prediction Accuracy
- **RMSE** (Root Mean Square Error)
- **MAE** (Mean Absolute Error)
- **R²** score for model fit
- **Coverage Rate** of confidence intervals

### Model Validation
- **Cross-validation**: Time-series based
- **Out-of-sample testing**: Latest 20% of data
- **Event-specific validation**: Match day accuracy

### Uncertainty Quantification
1. **Statistical Uncertainty**
   - Confidence intervals
   - Prediction intervals
   - Sample size effects

2. **Systematic Uncertainty**
   - Weather effects
   - Special events
   - Service disruptions

## Future Improvements

1. **Enhanced Feature Engineering**
   - Weather data integration
   - Traffic condition incorporation
   - More granular event categorization

2. **Model Refinements**
   - Ensemble methods
   - Neural network integration
   - Bayesian uncertainty quantification

3. **Real-time Updates**
   - Streaming data processing
   - Dynamic model updates
   - Automated retraining