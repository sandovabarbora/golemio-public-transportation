from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import altair as alt
from dataclasses import dataclass
import streamlit as st


from functools import partial

@dataclass
class PredictionConfig:
    """Configuration for prediction parameters."""
    max_days: int = 7
    time_window_minutes: int = 15
    peak_hour_factor: float = 1.2
    match_impact_hours: int = 3
    confidence_level: float = 0.95


@dataclass
class PredictionResult:
    """Store prediction results with confidence intervals."""
    timestamp: datetime
    predicted_delay: float
    confidence_lower: float
    confidence_upper: float
    probability_factors: Dict[str, float]


def is_utc_timezone(tz) -> bool:
    """Check if a timezone is UTC, handling both datetime.timezone and pytz/dateutil timezones."""
    if tz is None:
        return False
    # Handle datetime.timezone objects
    if isinstance(tz, timezone):
        return tz.utcoffset(None) == timedelta(0)
    # Handle pytz/dateutil timezones
    return getattr(tz, 'zone', 'UTC') == 'UTC'


class DelayPredictor:
    """Enhanced delay prediction system with time-based analysis."""
    
    def __init__(self, config: PredictionConfig = PredictionConfig()):
        """Initialize the predictor with configuration."""
        self.config = config
        self.model = None
        self.feature_importances = None
        self.label_encoders = {}
        self.peak_hours = set(range(7, 10)) | set(range(16, 19))
        self.debug_info = None

    def prepare_features(
        self, 
        traffic_data: pd.DataFrame, 
        events_df: pd.DataFrame,
        is_training: bool = True
    ) -> pd.DataFrame:
        """Prepare enhanced features for the prediction model."""
        # Create a copy and ensure datetime
        data = traffic_data.copy()
        if not pd.api.types.is_datetime64_any_dtype(data['current_stop_departure']):
            data['current_stop_departure'] = pd.to_datetime(data['current_stop_departure'])

        # Drop rows with NaN in essential columns
        if is_training:
            data = data.dropna(subset=['current_stop_departure', 'current_stop_dep_delay', 'base_stop_id'])

        # Create basic features
        features = pd.DataFrame({
            'hour': data['current_stop_departure'].dt.hour,
            'minute': data['current_stop_departure'].dt.minute,
            'day_of_week': data['current_stop_departure'].dt.dayofweek,
            'is_weekend': data['current_stop_departure'].dt.dayofweek.isin([5, 6]).astype(int),
            'is_peak_hour': data['current_stop_departure'].dt.hour.isin(self.peak_hours).astype(int),
            'time_of_day': data['current_stop_departure'].dt.hour + 
                          data['current_stop_departure'].dt.minute / 60,
            'date': data['current_stop_departure'].dt.date,
            'stop_id': data['base_stop_id'].fillna('unknown')
        })

        # Process events data
        events_df = events_df.copy()
        if 'datetime' not in events_df.columns and 'date' in events_df.columns:
            events_df['datetime'] = pd.to_datetime(events_df['date'])
        events_df['date'] = pd.to_datetime(events_df['datetime']).dt.date
        events_df['match_hour'] = pd.to_datetime(events_df['datetime']).dt.hour
        events_df['match_minute'] = pd.to_datetime(events_df['datetime']).dt.minute

        # Add event-related features
        features['is_match_day'] = features['date'].isin(events_df['date']).astype(int)
        
        # Calculate minutes to match
        match_times = events_df[['date', 'match_hour', 'match_minute']].set_index('date')
        features['minutes_to_match'] = features.apply(
            lambda row: self._calculate_minutes_to_match(row, match_times) 
            if row['is_match_day'] else 720,
            axis=1
        )

        # Encode categorical variables
        for col in ['stop_id']:
            if is_training or col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
                features[col] = self.label_encoders[col].fit_transform(features[col])
            else:
                # Handle unseen categories in prediction
                features[col] = features[col].map(
                    lambda x: x if x in self.label_encoders[col].classes_ else 'unknown'
                )
                features[col] = self.label_encoders[col].transform(features[col])

        return features

    def train_model_with_date_range(
        self, 
        traffic_data: pd.DataFrame, 
        events_df: pd.DataFrame,
        end_date: datetime,
        training_window_days: int = 14,
        min_samples: int = 100
    ) -> Tuple[RandomForestRegressor, pd.DataFrame]:
        """Train the prediction model using data from a specific date range."""
        # Convert end_date to pandas Timestamp if it isn't already
        if not isinstance(end_date, pd.Timestamp):
            end_date = pd.to_datetime(end_date)
        
        # Handle timezone for end_date
        if end_date.tz is None:
            end_date = end_date.tz_localize('UTC')
        elif not is_utc_timezone(end_date.tz):
            end_date = end_date.tz_convert('UTC')
        
        # Calculate start date
        start_date = end_date - pd.Timedelta(days=training_window_days)
        
        # Handle traffic data timestamps
        traffic_data = traffic_data.copy()
        if not pd.api.types.is_datetime64_any_dtype(traffic_data['current_stop_departure']):
            traffic_data['current_stop_departure'] = pd.to_datetime(traffic_data['current_stop_departure'])
        
        # Convert traffic data timestamps to UTC if needed
        if traffic_data['current_stop_departure'].dt.tz is None:
            traffic_data['current_stop_departure'] = traffic_data['current_stop_departure'].dt.tz_localize('UTC')
        elif not is_utc_timezone(traffic_data['current_stop_departure'].dt.tz):
            traffic_data['current_stop_departure'] = traffic_data['current_stop_departure'].dt.tz_convert('UTC')
        
        # Try different window sizes until we get enough data
        current_window = training_window_days
        max_window = 365  # Maximum window size of 1 year
        filtered_traffic_data = pd.DataFrame()
        
        while len(filtered_traffic_data) < min_samples and current_window <= max_window:
            start_date = end_date - pd.Timedelta(days=current_window)
            
            # Filter traffic data
            mask = (traffic_data['current_stop_departure'] >= start_date) & \
                   (traffic_data['current_stop_departure'] <= end_date)
            filtered_traffic_data = traffic_data[mask].copy()
            
            if len(filtered_traffic_data) < min_samples:
                current_window *= 2  # Double the window size
        
        # If we still don't have enough data, use all available data
        if len(filtered_traffic_data) < min_samples:
            filtered_traffic_data = traffic_data.copy()
            start_date = traffic_data['current_stop_departure'].min()
            end_date = traffic_data['current_stop_departure'].max()
        
        # Handle events data
        events_df = events_df.copy()
        if 'datetime' not in events_df.columns:
            if 'date' in events_df.columns:
                events_df['datetime'] = pd.to_datetime(events_df['date'])
            else:
                raise ValueError("Events DataFrame must have either 'datetime' or 'date' column")
        
        # Convert events timestamps to UTC
        if not pd.api.types.is_datetime64_any_dtype(events_df['datetime']):
            events_df['datetime'] = pd.to_datetime(events_df['datetime'])
        
        if events_df['datetime'].dt.tz is None:
            events_df['datetime'] = events_df['datetime'].dt.tz_localize('UTC')
        elif not is_utc_timezone(events_df['datetime'].dt.tz):
            events_df['datetime'] = events_df['datetime'].dt.tz_convert('UTC')
        
        # Filter events
        events_mask = (events_df['datetime'] >= start_date) & \
                     (events_df['datetime'] <= end_date)
        filtered_events_df = events_df[events_mask].copy()
        
        # Store debug information
        self.debug_info = {
            'data_size': len(filtered_traffic_data),
            'date_range': (start_date.isoformat(), end_date.isoformat()),
            'events_count': len(filtered_events_df),
            'window_size': current_window
        }
        
        return self.train_model(filtered_traffic_data, filtered_events_df)

    def train_model(
        self, 
        traffic_data: pd.DataFrame, 
        events_df: pd.DataFrame
    ) -> Tuple[RandomForestRegressor, pd.DataFrame]:
        """Train the prediction model."""
        # Prepare features
        features = self.prepare_features(traffic_data, events_df, is_training=True)
        target = traffic_data['current_stop_dep_delay'].dropna()
        
        # Ensure alignment
        features = features[features.index.isin(target.index)]
        target = target[target.index.isin(features.index)]
        
        if len(features) == 0 or len(target) == 0:
            raise ValueError("No valid training data available after preprocessing")
        
        # Split training data
        X = features.drop('date', axis=1)
        
        # Adjust test_size based on data size
        test_size = min(0.2, 1.0 - (100.0 / len(X)))  # Ensure at least 100 training samples
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, target, test_size=test_size, random_state=42
        )
        
        # Train model
        self.model = RandomForestRegressor(
            n_estimators=200,
            max_depth=20,
            min_samples_split=4,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
            bootstrap=True
        )
        
        self.model.fit(X_train, y_train)
        
        # Calculate feature importance
        self.feature_importances = pd.DataFrame({
            'feature': X.columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        return self.model, self.feature_importances

    def predict_future_delays(
        self,
        traffic_data: pd.DataFrame,
        events_df: pd.DataFrame,
        start_time: datetime = None
    ) -> List[PredictionResult]:
        """Predict future delays."""
        if start_time is None:
            start_time = datetime.now()
        
        end_time = start_time + timedelta(days=self.config.max_days)
        
        # Generate timestamps
        timestamps = []
        current_time = start_time
        while current_time < end_time:
            timestamps.append(current_time)
            current_time += timedelta(minutes=self.config.time_window_minutes)

        # Create prediction data
        valid_stops = traffic_data['base_stop_id'].dropna().unique()
        future_data = []
        
        for timestamp in timestamps:
            for stop_id in valid_stops:
                future_data.append({
                    'current_stop_departure': timestamp,
                    'base_stop_id': stop_id,
                    'current_stop_dep_delay': 0  # Placeholder
                })

        future_df = pd.DataFrame(future_data)
        future_features = self.prepare_features(future_df, events_df, is_training=False)
        
        predictions = []
        for idx, row in future_features.iterrows():
            features_for_prediction = row.drop('date')
            X = features_for_prediction.values.reshape(1, -1)
            
            # Make prediction
            pred = self.model.predict(X)[0]
            
            # Calculate confidence intervals
            tree_predictions = np.array([
                tree.predict(X)[0] for tree in self.model.estimators_
            ])
            confidence_lower = np.percentile(
                tree_predictions, 
                (1 - self.config.confidence_level) * 100 / 2
            )
            confidence_upper = np.percentile(
                tree_predictions, 
                (1 + self.config.confidence_level) * 100 / 2
            )
            
            # Calculate probability factors
            peak_prob = 1.0 if row['is_peak_hour'] else max(
                0.0, 
                1.0 - min(abs(row['hour'] - peak) for peak in self.peak_hours) * 0.2
            )
            
            match_impact = 1.0 if (
                row['is_match_day'] and 
                abs(row['minutes_to_match']) <= self.config.match_impact_hours * 60
            ) else 0.0
            
            predictions.append(PredictionResult(
                timestamp=future_df['current_stop_departure'].iloc[idx],
                predicted_delay=pred,
                confidence_lower=confidence_lower,
                confidence_upper=confidence_upper,
                probability_factors={
                    'peak_hour': peak_prob,
                    'match_impact': match_impact,
                    'historical_reliability': 0.8
                }
            ))
        
        return predictions
    def get_immediate_prediction(
        self,
        traffic_data: pd.DataFrame,
        events_df: pd.DataFrame,
        stop_id: str,
        current_time: datetime = None
    ) -> Dict[str, any]:
        """Get immediate prediction for a specific stop."""
        if current_time is None:
            current_time = datetime.now()

        # Create prediction data for next 2 hours
        future_data = []
        for minute in range(0, 120, 15):  # Check every 15 minutes for next 2 hours
            future_time = current_time + timedelta(minutes=minute)
            future_data.append({
                'current_stop_departure': future_time,
                'base_stop_id': stop_id,
                'current_stop_dep_delay': 0
            })

        future_df = pd.DataFrame(future_data)
        future_features = self.prepare_features(future_df, events_df, is_training=False)

        predictions = []
        for idx, row in future_features.iterrows():
            features_for_prediction = row.drop('date')
            X = features_for_prediction.values.reshape(1, -1)
            
            pred = self.model.predict(X)[0]
            tree_predictions = np.array([
                tree.predict(X)[0] for tree in self.model.estimators_
            ])
            
            predictions.append({
                'time': future_df['current_stop_departure'].iloc[idx],
                'delay': pred,
                'confidence': np.std(tree_predictions),
                'is_peak': row['is_peak_hour'],
                'is_match_day': row['is_match_day'],
                'minutes_to_match': row['minutes_to_match']
            })

        # Find best departure time
        best_prediction = min(predictions, key=lambda x: x['delay'])
        worst_prediction = max(predictions, key=lambda x: x['delay'])

        return {
            'current_prediction': predictions[0],
            'best_departure': best_prediction,
            'worst_departure': worst_prediction,
            'all_predictions': predictions
        }

    def _calculate_minutes_to_match(
        self,
        row: pd.Series,
        match_times: pd.DataFrame
    ) -> float:
        """Calculate minutes until/after match."""
        if row['date'] in match_times.index:
            match_time = match_times.loc[row['date']]
            current_minutes = row['hour'] * 60 + row['minute']
            match_minutes = match_time['match_hour'] * 60 + match_time['match_minute']
            return current_minutes - match_minutes
        return 720  # 12 hours (max distance)
    
def ensure_utc(timestamp) -> pd.Timestamp:
    """Ensure a timestamp is UTC, handling both naive and tz-aware cases."""
    if timestamp is None:
        return None
        
    if not isinstance(timestamp, pd.Timestamp):
        timestamp = pd.to_datetime(timestamp)
        
    if timestamp.tz is None:
        return timestamp.tz_localize('UTC')
    else:
        return timestamp.tz_convert('UTC')

@st.cache_data(ttl=3600)
def prepare_base_data(data: pd.DataFrame, min_date: pd.Timestamp = None, max_date: pd.Timestamp = None, 
                     min_samples: int = 1000) -> pd.DataFrame:
    """Preprocess and cache the base data with consistent timezone handling."""
    data = data.copy()
    
    # Ensure min_date and max_date are UTC
    min_date = ensure_utc(min_date) if min_date is not None else None
    max_date = ensure_utc(max_date) if max_date is not None else None
    
    # Convert timestamps and ensure UTC timezone
    if not pd.api.types.is_datetime64_any_dtype(data['current_stop_departure']):
        data['current_stop_departure'] = pd.to_datetime(data['current_stop_departure'])
    
    # Convert to UTC if needed
    if data['current_stop_departure'].dt.tz is None:
        data['current_stop_departure'] = data['current_stop_departure'].dt.tz_localize('UTC')
    else:
        data['current_stop_departure'] = data['current_stop_departure'].dt.tz_convert('UTC')
    
    # Initial data filtering
    if min_date is not None and max_date is not None:
        mask = (data['current_stop_departure'] >= min_date) & \
               (data['current_stop_departure'] <= max_date)
        filtered_data = data[mask].copy()
        
        # If we don't have enough samples, gradually expand the window
        if len(filtered_data) < min_samples:
            days_to_expand = 7
            while len(filtered_data) < min_samples and days_to_expand <= 60:
                expanded_min_date = min_date - pd.Timedelta(days=days_to_expand)
                mask = (data['current_stop_departure'] >= expanded_min_date) & \
                       (data['current_stop_departure'] <= max_date)
                filtered_data = data[mask].copy()
                days_to_expand *= 2
            
            if len(filtered_data) >= min_samples:
                st.info(f"Extended training window to get sufficient data. Using {days_to_expand} days of historical data.")
            else:
                st.warning(f"Could not find enough samples even with extended window. Using all available data.")
                filtered_data = data.copy()
    else:
        filtered_data = data.copy()
    
    # Drop rows with NaN in essential columns
    filtered_data = filtered_data.dropna(subset=['current_stop_departure', 'current_stop_dep_delay', 'base_stop_id'])
    
    # Pre-calculate common features
    filtered_data['hour'] = filtered_data['current_stop_departure'].dt.hour
    filtered_data['day_of_week'] = filtered_data['current_stop_departure'].dt.dayofweek
    filtered_data['is_weekend'] = filtered_data['day_of_week'].isin([5, 6]).astype(int)
    
    return filtered_data

@st.cache_resource
def get_cached_predictor_for_date_range(_traffic_data: pd.DataFrame, 
                                        _events_df: pd.DataFrame, 
                                        _start_date: pd.Timestamp, 
                                        _end_date: pd.Timestamp) -> DelayPredictor:
    """Get or create a cached predictor for a specific date range."""
    predictor = DelayPredictor()
    predictor.train_model_with_date_range(
        _traffic_data,
        _events_df,
        _end_date,
        training_window_days=(_end_date - _start_date).days + 14  # Include buffer
    )
    return predictor


@st.cache_resource(ttl=3600)  # Cache for 1 hour
def get_cached_model(_traffic_data: pd.DataFrame, _events_df: pd.DataFrame, _end_date: datetime, debug: bool = False) -> DelayPredictor:
    """Get or create a cached predictor model for a specific date range."""
    # Convert end_date to pandas Timestamp if it isn't already
    if not isinstance(_end_date, pd.Timestamp):
        _end_date = pd.to_datetime(_end_date)
    
    # Convert to UTC if needed
    if _end_date.tz is None:
        _end_date = _end_date.tz_localize('UTC')
    elif not is_utc_timezone(_end_date.tz):
        _end_date = _end_date.tz_convert('UTC')
    
    predictor = DelayPredictor()
    predictor.train_model_with_date_range(_traffic_data, _events_df, _end_date)
    return predictor


def initialize_predictor(key: str, traffic_data: pd.DataFrame, events_df: pd.DataFrame, prediction_date: datetime, debug: bool = False) -> DelayPredictor:
    """Initialize a predictor with caching based on prediction date."""
    # Convert to pandas Timestamp for consistent timezone handling
    if not isinstance(prediction_date, pd.Timestamp):
        prediction_date = pd.to_datetime(prediction_date)
        
    # Handle timezone
    if prediction_date.tz is None:
        prediction_date = prediction_date.tz_localize('UTC')
    elif not is_utc_timezone(prediction_date.tz):
        prediction_date = prediction_date.tz_convert('UTC')
        
    return get_cached_model(traffic_data, events_df, prediction_date, debug=debug)


def display_detailed_predictions(data: pd.DataFrame, events_df: pd.DataFrame):
    """Display detailed predictions with optimized performance."""
    st.subheader("📊 Detailed Delay Predictions")
    
    # Add unique key for debug checkbox
    show_debug = st.checkbox("Show Debug Info", value=False, key="detailed_predictions_debug")
    
    # Date range selector with default values
    default_start = pd.Timestamp.now().floor('D')
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=default_start.date(),
            help="Select start date for predictions",
            key="detailed_predictions_date"
        )
    
    with col2:
        days_ahead = st.slider(
            "Days to Predict",
            min_value=1,
            max_value=7,
            value=3,
            help="Number of days to predict ahead",
            key="detailed_predictions_days"
        )
    
    # Calculate date range
    start_time = pd.Timestamp(start_date)
    end_time = start_time + pd.Timedelta(days=days_ahead)
    
    # Show loading progress
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Prepare and cache base data
        status_text.text("Preparing data...")
        progress_bar.progress(20)
        
        # Calculate the range for data preparation (including training window)
        data_start = start_time - pd.Timedelta(days=14)  # 14 days before for training
        prepared_data = prepare_base_data(data, data_start, end_time)
        
        progress_bar.progress(40)
        status_text.text("Initializing predictor...")
        
        # Get cached predictor for the date range
        predictor = get_cached_predictor_for_date_range(
            prepared_data,
            events_df,
            start_time,
            end_time
        )
        
        progress_bar.progress(60)
        status_text.text("Generating predictions...")
        
        # Generate predictions
        predictions = predictor.predict_future_delays(prepared_data, events_df, start_time)
        
        if not predictions:
            st.warning("No predictions were generated. Please check the data and date range.")
            return
        
        progress_bar.progress(80)
        status_text.text("Creating visualizations...")
        
        # Create prediction DataFrame
        pred_df = pd.DataFrame([{
            'timestamp': p.timestamp,
            'predicted_delay': p.predicted_delay,
            'confidence_lower': p.confidence_lower,
            'confidence_upper': p.confidence_upper,
            'peak_probability': p.probability_factors['peak_hour'],
            'match_impact': p.probability_factors['match_impact']
        } for p in predictions if p.timestamp.date() < end_time.date()])
        
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["Summary", "Detailed Analysis", "Model Insights"])
        
        with tab1:
            # Display summary metrics
            display_summary_metrics(pred_df, events_df)
        
        with tab2:
            # Display detailed analysis
            display_detailed_analysis(pred_df, predictor)
        
        with tab3:
            # Display model insights
            display_model_insights(predictor, pred_df)
        
        progress_bar.progress(100)
        status_text.empty()
        
        # Add export options
        if st.button("Export Predictions", key="export_predictions"):
            csv = pred_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"delay_predictions_{start_date.strftime('%Y%m%d')}.csv",
                mime="text/csv",
                key="download_predictions"
            )
            
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"Error in predictions: {str(e)}")
        if show_debug:
            st.exception(e)

@st.cache_data(ttl=3600)
def display_summary_metrics(pred_df: pd.DataFrame, events_df: pd.DataFrame):
    """Display summary metrics (cached)."""
    daily_summary = pred_df.set_index('timestamp').resample('D').agg({
        'predicted_delay': ['mean', 'max', 'min'],
        'peak_probability': 'mean',
        'match_impact': 'max'
    }).round(2)
    
    st.markdown("### Daily Summary")
    for date, row in daily_summary.iterrows():
        with st.expander(f"📅 {date.strftime('%Y-%m-%d')}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "Avg Delay",
                    f"{row[('predicted_delay', 'mean')]:.1f}s",
                    delta=f"{row[('predicted_delay', 'mean')] - pred_df['predicted_delay'].mean():.1f}s",
                    delta_color="inverse"
                )
            with col2:
                st.metric("Max Delay", f"{row[('predicted_delay', 'max')]:.1f}s")
            with col3:
                st.metric(
                    "Peak Impact",
                    f"{row[('peak_probability', 'mean')]*100:.1f}%"
                )

@st.cache_data(ttl=3600)
def display_detailed_analysis(pred_df: pd.DataFrame, predictor: DelayPredictor):
    """Display detailed analysis charts (cached)."""
    # Create time series chart with confidence intervals
    chart = create_time_series_chart(pred_df)
    st.altair_chart(chart)

@st.cache_data(ttl=3600)
def display_model_insights(predictor: DelayPredictor, pred_df: pd.DataFrame):
    """Display model insights and feature importance (cached)."""
    if predictor.feature_importances is not None:
        st.markdown("### 🎯 Feature Importance")
        fig_importance = create_feature_importance_chart(predictor.feature_importances)
        st.altair_chart(fig_importance)

@st.cache_data(ttl=3600)
def create_time_series_chart(pred_df: pd.DataFrame):
    """Create and cache time series chart."""
    base = alt.Chart(pred_df).encode(x=alt.X('timestamp:T', title='Time'))
    
    # Confidence interval area
    confidence_area = base.mark_area(opacity=0.3, color='blue').encode(
        y=alt.Y('confidence_lower:Q', title='Delay (seconds)'),
        y2=alt.Y2('confidence_upper:Q')
    )
    
    # Main prediction line
    prediction_line = base.mark_line(color='darkblue').encode(
        y=alt.Y('predicted_delay:Q')
    )
    
    return (confidence_area + prediction_line).properties(
        width=600,
        height=300,
        title='Predicted Delays with Confidence Intervals'
    ).interactive()

def display_travel_advice(predictor: DelayPredictor, data: pd.DataFrame, events_df: pd.DataFrame):
    """Display travel advice for immediate journey planning."""
    st.subheader("🚊 Real-Time Travel Advisor")
    
    # Get unique stops
    stops = data['stop_name'].unique()
    selected_stop = st.selectbox(
        "Select your departure stop",
        options=stops,
        help="Choose the stop you're traveling from",
        key="travel_advice_stop"
    )
    
    if selected_stop:
        try:
            # Get the base_stop_id for the selected stop
            stop_id = data[data['stop_name'] == selected_stop]['base_stop_id'].iloc[0]
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                current_time = datetime.now()
                prediction_results = predictor.get_immediate_prediction(
                    data, events_df, stop_id, current_time
                )
                
                if prediction_results:
                    current_pred = prediction_results['current_prediction']
                    best_pred = prediction_results['best_departure']
                    worst_pred = prediction_results['worst_departure']
                    
                    # Display immediate prediction
                    st.info(f"🕒 If you leave now ({current_time.strftime('%H:%M')})")
                    expected_delay = current_pred['delay']
                    delay_severity = "Low" if expected_delay < 60 else "Moderate" if expected_delay < 180 else "High"
                    delay_color = "green" if expected_delay < 60 else "orange" if expected_delay < 180 else "red"
                    
                    st.markdown(f"""
                    ### Current Conditions
                    - Expected delay: **:{delay_color}[{expected_delay:.0f} seconds]**
                    - Delay level: **:{delay_color}[{delay_severity}]**
                    - {'🏟️ Match day impact!' if current_pred['is_match_day'] else ''}
                    - {'⚠️ Peak hour!' if current_pred['is_peak'] else ''}
                    """)
                    
                    # Travel recommendations
                    st.divider()
                    st.markdown("### 📋 Travel Recommendations")
                    
                    if best_pred['time'] != current_pred['time']:
                        wait_time = (best_pred['time'] - current_time).total_seconds() / 60
                        st.success(f"""
                        ✅ **Best departure time:** {best_pred['time'].strftime('%H:%M')} 
                        - Wait {wait_time:.0f} minutes for better conditions
                        - Expected delay: {best_pred['delay']:.0f} seconds
                        """)
                    
                    if current_pred['is_peak']:
                        st.warning("""
                        ⚠️ **Peak Hour Alert**
                        - Currently in peak hours
                        - Consider flexible departure times
                        - Expect increased delays
                        """)
                    
                    if current_pred['is_match_day']:
                        match_time = events_df[
                            events_df['date'] == current_time.date()
                        ]['Time'].iloc[0] if not events_df.empty else "Unknown"
                        
                        if abs(current_pred['minutes_to_match']) <= 180:  # Within 3 hours of match
                            st.warning(f"""
                            ⚡ **Match Day Impact**
                            - High traffic expected
                            - Match time: {match_time}
                            - Consider alternative routes
                            """)
                    
                    # Show alternative options if delays are high
                    if expected_delay > 180:
                        st.error("""
                        🚨 **High Delay Alert**
                        Recommendations:
                        - Consider alternative transportation
                        - Work remotely if possible
                        - Plan for significant delays
                        """)
            
            with col2:
                # Show next 2 hours prediction chart
                predictions = prediction_results['all_predictions']
                pred_df = pd.DataFrame(predictions)
                
                chart = alt.Chart(pred_df).mark_line(point=True).encode(
                    x=alt.X('time:T', title='Time'),
                    y=alt.Y('delay:Q', title='Expected Delay (seconds)'),
                    color=alt.condition(
                        alt.datum.is_peak,
                        alt.value('orange'),
                        alt.value('blue')
                    ),
                    tooltip=[
                        alt.Tooltip('time:T', title='Time'),
                        alt.Tooltip('delay:Q', title='Expected Delay', format='.0f'),
                        alt.Tooltip('is_peak:N', title='Peak Hour'),
                        alt.Tooltip('is_match_day:N', title='Match Day')
                    ]
                ).properties(
                    width=300,
                    height=200,
                    title='Delay Forecast (Next 2 Hours)'
                )
                
                # Add peak hour markers
                peak_start = current_time.replace(hour=8, minute=0)
                peak_end = current_time.replace(hour=10, minute=0)
                
                peak_period = alt.Chart(pd.DataFrame([
                    {'start': peak_start, 'end': peak_end}
                ])).mark_rect(
                    opacity=0.2,
                    color='orange'
                ).encode(
                    x='start:T',
                    x2='end:T',
                    y=alt.value(0),
                    y2=alt.value(300)
                )
                
                st.altair_chart(chart + peak_period)
                
                # Additional metrics
                with st.container():
                    st.markdown("### Quick Stats")
                    metrics = {
                        "Average Delay": f"{np.mean([p['delay'] for p in predictions]):.0f}s",
                        "Match Impact": "Yes" if any(p['is_match_day'] for p in predictions) else "No"
                    }
                    
                    for metric, value in metrics.items():
                        st.metric(
                            metric,
                            value,
                            delta_color="inverse" if "Delay" in metric else "off"
                        )
                        
        except Exception as e:
            st.error(f"Error generating predictions: {str(e)}")
            st.exception(e)


def display_travel_advice_wrapper(data: pd.DataFrame, events_df: pd.DataFrame):
    """Wrapper for travel advice with debug option."""
    # Add unique key for debug checkbox
    show_debug = st.checkbox("Show Debug Info", value=False, key="travel_advice_debug")
    
    current_time = datetime.now()
    predictor = initialize_predictor('travel', data, events_df, current_time, debug=show_debug)
    
    if show_debug and hasattr(predictor, 'debug_info'):
        st.write("Debug Information:")
        st.json(predictor.debug_info)
    
    display_travel_advice(predictor, data, events_df)