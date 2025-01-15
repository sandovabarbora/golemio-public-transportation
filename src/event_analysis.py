import pandas as pd
import altair as alt
import streamlit as st
from datetime import timedelta
import numpy as np
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

def load_event_data(file_content):
    """Load and process Sparta Praha match schedule"""
    events_df = pd.read_csv(
        file_content,
        sep=';',
        encoding='utf-8',
        names=['Skip', 'Location', 'Date', 'Time', 'Opponent'],
        skiprows=1
    )
    
    events_df = events_df.drop('Skip', axis=1)
    events_df['Date'] = pd.to_datetime(events_df['Date'], format='%d.%m.%Y', errors='coerce')
    events_df['Time'] = pd.to_datetime(events_df['Time'], format='%H:%M', errors='coerce').dt.time
    
    events_df['datetime'] = events_df.apply(
        lambda x: pd.Timestamp.combine(x['Date'], x['Time']) if pd.notnull(x['Date']) and x['Time'] is not None else pd.NaT,
        axis=1
    )
    
    events_df['is_home'] = events_df['Location'].str.strip().str.lower() == 'd'
    events_df['Opponent'] = events_df['Opponent'].fillna('TBD')
    
    return events_df

def get_comparison_data(data, match_date):
    """Get comparison data for surrounding days"""
    # Expand comparison window
    day_before = match_date - timedelta(days=1)
    day_after = match_date + timedelta(days=1)
    week_before = match_date - timedelta(days=7)
    week_after = match_date + timedelta(days=7)
    
    comparison_data = {
        'Match Day': data[data['date'] == match_date],
        'Day Before': data[data['date'] == day_before],
        'Day After': data[data['date'] == day_after],
        'Week Before': data[data['date'] == week_before],
        'Week After': data[data['date'] == week_after]
    }
    
    return comparison_data

def calculate_peak_hours(data, threshold_percentile=75):
    """Enhanced peak delay hours analysis with statistical measures"""
    # Calculate hourly statistics
    hourly_stats = data.groupby(data['current_stop_departure'].dt.hour).agg({
        'current_stop_dep_delay': [
            ('mean', 'mean'),
            ('median', 'median'),
            ('std', 'std'),
            ('count', 'count'),
            ('q25', lambda x: x.quantile(0.25)),
            ('q75', lambda x: x.quantile(0.75))
        ]
    }).reset_index()
    
    # Flatten column names
    hourly_stats.columns = ['hour', 'mean', 'median', 'std', 'count', 'q25', 'q75']
    
    # Calculate IQR and identify outliers
    hourly_stats['iqr'] = hourly_stats['q75'] - hourly_stats['q25']
    hourly_stats['is_outlier_hour'] = (
        (hourly_stats['mean'] > hourly_stats['q75'] + 1.5 * hourly_stats['iqr']) |
        (hourly_stats['mean'] < hourly_stats['q25'] - 1.5 * hourly_stats['iqr'])
    )
    
    # Calculate z-scores for delay means
    hourly_stats['z_score'] = stats.zscore(hourly_stats['mean'])
    
    # Define peak hours using multiple criteria
    delay_threshold = hourly_stats['mean'].quantile(threshold_percentile/100)
    volume_threshold = hourly_stats['count'].quantile(0.5)  # Median volume
    
    hourly_stats['is_peak'] = (
        (hourly_stats['mean'] > delay_threshold) &
        (hourly_stats['count'] >= volume_threshold) &
        (abs(hourly_stats['z_score']) <= 3)  # Exclude extreme outliers
    )
    
    # Add confidence intervals
    confidence_level = 0.95
    t_value = stats.t.ppf((1 + confidence_level) / 2, df=hourly_stats['count'] - 1)
    hourly_stats['ci_lower'] = hourly_stats['mean'] - t_value * (hourly_stats['std'] / np.sqrt(hourly_stats['count']))
    hourly_stats['ci_upper'] = hourly_stats['mean'] + t_value * (hourly_stats['std'] / np.sqrt(hourly_stats['count']))
    
    return hourly_stats

def analyze_event_impact(data, events):
    """Enhanced analysis of event impact on transport delays"""
    data['date'] = data['current_stop_departure'].dt.date
    events['date'] = events['datetime'].dt.date
    data['is_event'] = data['date'].isin(events['date'])
    
    # Calculate basic statistics
    event_stats = data.groupby('is_event').agg({
        'current_stop_dep_delay': [
            ('avg_delay', 'mean'),
            ('median_delay', 'median'),
            ('max_delay', 'max'),
            ('min_delay', 'min'),
            ('std_delay', 'std'),
            ('total_records', 'count')
        ]
    }).reset_index()
    
    # Flatten column names
    event_stats.columns = ['is_event', 'avg_delay', 'median_delay', 'max_delay', 'min_delay', 'std_delay', 'total_records']
    
    # Add statistical significance test
    event_delays = data[data['is_event']]['current_stop_dep_delay']
    non_event_delays = data[~data['is_event']]['current_stop_dep_delay']
    
    t_stat, p_value = stats.ttest_ind(event_delays, non_event_delays)
    event_stats['t_statistic'] = t_stat
    event_stats['p_value'] = p_value
    
    # Calculate effect size (Cohen's d)
    pooled_std = np.sqrt((event_delays.std()**2 + non_event_delays.std()**2) / 2)
    cohen_d = (event_delays.mean() - non_event_delays.mean()) / pooled_std
    event_stats['effect_size'] = cohen_d
    
    # Hourly patterns with enhanced statistics
    hourly_stats = data.groupby(['is_event', data['current_stop_departure'].dt.hour]).agg({
        'current_stop_dep_delay': ['mean', 'median', 'std', 'count']
    }).reset_index()
    
    hourly_stats.columns = ['is_event', 'hour', 'mean_delay', 'median_delay', 'std_delay', 'count']
    hourly_stats['day_type'] = hourly_stats['is_event'].map({True: 'Match Days', False: 'Regular Days'})
    
    return event_stats, hourly_stats

def identify_delay_patterns(data):
    """Identify patterns in delay data using clustering"""
    # Prepare features for clustering
    features = pd.DataFrame({
        'hour': data['current_stop_departure'].dt.hour,
        'delay': data['current_stop_dep_delay'],
        'weekday': data['current_stop_departure'].dt.weekday
    })
    
    # Standardize features
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)
    
    # Apply KMeans clustering
    n_clusters = 3  # Can be adjusted based on needs
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    clusters = kmeans.fit_predict(features_scaled)
    
    # Add cluster information to features
    features['cluster'] = clusters
    
    # Calculate cluster characteristics
    cluster_stats = features.groupby('cluster').agg({
        'delay': ['mean', 'std', 'count'],
        'hour': ['mean', 'std'],
        'weekday': 'mean'
    }).round(2)
    
    return cluster_stats, features

def display_event_analysis(data, events_df):
    """Enhanced display of event analysis with additional visualizations"""
    event_stats, hourly_stats = analyze_event_impact(data, events_df)
    
    tab_choice = st.radio("Select Analysis View:", 
                         ["Overall Impact", "Individual Matches", "Pattern Analysis"],
                         horizontal=True)
    
    if tab_choice == "Overall Impact":
        st.subheader("Overall Match Day Impact")
        
        # Calculate basic metrics
        match_avg_delay = event_stats.loc[event_stats['is_event'], 'avg_delay'].iloc[0]
        normal_avg_delay = event_stats.loc[~event_stats['is_event'], 'avg_delay'].iloc[0]
        delay_increase = ((match_avg_delay / normal_avg_delay) - 1) * 100
        
        # Display key metrics
        cols = st.columns(3)
        with cols[0]:
            st.metric(
                "Average Impact on Delays",
                f"{delay_increase:.1f}%",
                delta=f"{match_avg_delay - normal_avg_delay:.0f} sec longer",
                delta_color="normal"
            )
        
        with cols[1]:
            match_days = len(events_df)
            st.metric(
                "Matches Analyzed",
                f"{match_days} games",
                f"{len(events_df[events_df['is_home']])} home matches"
            )
        
        with cols[2]:
            # Find the most impacted hour
            worst_hour_stats = hourly_stats[hourly_stats['day_type'] == 'Match Days']
            worst_hour = worst_hour_stats.loc[worst_hour_stats['mean_delay'].idxmax()]
            st.metric(
                "Most Affected Time",
                f"{int(worst_hour['hour']):02d}:00",
                f"{worst_hour['mean_delay']:.0f} sec average delay"
            )

        # Key findings section
        st.subheader("Key Findings")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("##### 🚌 Transport Impact")
            # Calculate most affected stops
            match_stops = data[data['is_event']].groupby('stop_name')['current_stop_dep_delay'].agg(['mean', 'count']).reset_index()
            normal_stops = data[~data['is_event']].groupby('stop_name')['current_stop_dep_delay'].agg(['mean', 'count']).reset_index()
            
            # Compare match days vs normal days for each stop
            stop_comparison = pd.merge(match_stops, normal_stops, 
                                    on='stop_name', 
                                    suffixes=('_match', '_normal'))
            
            # Calculate percentage increase and filter for stops with sufficient data
            stop_comparison['delay_increase'] = ((stop_comparison['mean_match'] / stop_comparison['mean_normal']) - 1) * 100
            stop_comparison = stop_comparison[
                (stop_comparison['count_match'] >= 50) &  # Ensure sufficient data points
                (stop_comparison['count_normal'] >= 50)
            ]
            
            # Get top 5 most affected stops
            top_stops = stop_comparison.nlargest(5, 'delay_increase')
            
            findings = [
                f"• Average delays increase by {delay_increase:.1f}% on match days",
                f"• Most affected time is {int(worst_hour['hour']):02d}:00 with {worst_hour['mean_delay']:.0f} sec delays",
                "• Most affected stops:"
            ]
            
            for _, stop in top_stops.iterrows():
                findings.append(
                    f"  - {stop['stop_name']}: {stop['delay_increase']:.1f}% "
                    f"({stop['mean_match']:.0f} sec vs {stop['mean_normal']:.0f} sec)"
                )
            for finding in findings:
                st.write(finding)
        
        with col2:
            st.write("##### 💡 Recommendations")
            recommendations = [
                "• Adjust traffic light timing during peak match hours",
                "• Consider dedicated lanes for public transport",
                "• Deploy traffic officers at key intersections"
            ]
            for rec in recommendations:
                st.write(rec)

        # Simplified hourly visualization
        st.subheader("Delays Throughout the Day")
        
        # Prepare hourly comparison chart
        chart = alt.Chart(hourly_stats).mark_line(point=True).encode(
            x=alt.X('hour:Q', 
                    title='Hour of Day',
                    scale=alt.Scale(domain=[0, 23])),
            y=alt.Y('mean_delay:Q', 
                    title='Average Delay (seconds)'),
            color=alt.Color('day_type:N',
                        title='Day Type',
                        scale=alt.Scale(domain=['Match Days', 'Regular Days'],
                                        range=['#ff6b6b', '#4c6ef5'])),
            tooltip=[
                alt.Tooltip('hour:Q', title='Hour'),
                alt.Tooltip('mean_delay:Q', title='Average Delay', format='.0f'),
                alt.Tooltip('day_type:N', title='Day Type')
            ]
        ).properties(
            width=700,
            height=400,
            title='Average Transport Delays: Match Days vs Regular Days'
        )
        
        # Add a light gray band for rush hours (7-9 and 16-19)
        rush_hours = pd.DataFrame([
            {'start': 7, 'end': 9, 'label': 'Morning Rush Hour'},
            {'start': 16, 'end': 19, 'label': 'Evening Rush Hour'}
        ])
        
        rush_hour_bands = alt.Chart(rush_hours).mark_rect(opacity=0.2, color='gray').encode(
            x='start:Q',
            x2='end:Q',
            y=alt.value(0),
            y2=alt.value(300)
        )
        
        st.altair_chart(rush_hour_bands + chart)
        st.caption("Gray bands indicate typical rush hour periods")
        
        # Actionable conclusions
        # Add stop analysis visualization
        st.subheader("Most Affected Stops")
        
        # Prepare data for visualization
        top_stops_comparison = pd.melt(
            top_stops[['stop_name', 'mean_match', 'mean_normal']],
            id_vars=['stop_name'],
            value_vars=['mean_match', 'mean_normal'],
            var_name='day_type',
            value_name='delay'
        )
        top_stops_comparison['day_type'] = top_stops_comparison['day_type'].map({
            'mean_match': 'Match Days',
            'mean_normal': 'Regular Days'
        })
        
        # Create stop comparison chart
        stop_chart = alt.Chart(top_stops_comparison).mark_bar().encode(
            x=alt.X('stop_name:N', 
                    title='Stop Name',
                    sort='-y'),
            y=alt.Y('delay:Q',
                    title='Average Delay (seconds)'),
            color=alt.Color('day_type:N',
                        title='Day Type',
                        scale=alt.Scale(domain=['Match Days', 'Regular Days'],
                                        range=['#ff6b6b', '#4c6ef5'])),
            tooltip=[
                alt.Tooltip('stop_name:N', title='Stop'),
                alt.Tooltip('delay:Q', title='Average Delay', format='.0f'),
                alt.Tooltip('day_type:N', title='Day Type')
            ]
        ).properties(
            width=700,
            height=300,
            title='Top 5 Most Affected Stops: Match Days vs Regular Days'
        )
        
        st.altair_chart(stop_chart)
        st.caption("Analysis based on stops with at least 50 measurements on both match and regular days")
        
        # Add specific recommendations for most affected stops
        if not top_stops.empty:
            most_affected = top_stops.iloc[0]
            st.write(f"""
            ##### Priority Focus: {most_affected['stop_name']}
            This stop shows the highest impact with a {most_affected['delay_increase']:.1f}% increase in delays during matches.
            """)
        
        st.subheader("Suggested Actions")
        
        # Determine severity of impact
        if delay_increase > 30:
            impact_level = "Major"
        elif delay_increase > 15:
            impact_level = "Moderate"
        else:
            impact_level = "Minor"
        
        actions = {
            "Major": [
                "🚨 Immediate attention required for traffic management",
                "📊 Consider revising match day transport strategy",
                "👮 Deploy additional traffic officers",
                "🚌 Add extra public transport capacity",
            ],
            "Moderate": [
                "⚠️ Monitor key intersections during match days",
                "🚌 Consider additional buses on match days",
                "📢 Improve communication about alternative routes"
            ],
            "Minor": [
                "✅ Current measures appear adequate",
            ]
        }
        
        for action in actions[impact_level]:
            st.write(action)
    elif tab_choice == "Individual Matches":
        st.subheader("Match Day Impact Analysis")
        historical_matches = events_df[events_df['datetime'].dt.date <= pd.Timestamp.now().date()]
        
        if not historical_matches.empty:
            historical_matches = historical_matches.sort_values('datetime')
            selected_date = st.selectbox(
                "Select Match Date",
                options=historical_matches['datetime'].dt.date,
                format_func=lambda x: (
                    f"{x.strftime('%d.%m.%Y')} - {historical_matches[historical_matches['datetime'].dt.date == x]['Opponent'].iloc[0]} "
                    f"({'Home' if historical_matches[historical_matches['datetime'].dt.date == x]['is_home'].iloc[0] else 'Away'})"
                )
            )
            
            if selected_date:
                match_data = historical_matches[historical_matches['datetime'].dt.date == selected_date].iloc[0]
                comparison_data = get_comparison_data(data, selected_date)
                
                # Match info and key metrics
                st.write("### Match Information")
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"🏟️ **Location:** {'Home match at Letná' if match_data['is_home'] else 'Away match'}")
                    st.write(f"👥 **Opponent:** {match_data['Opponent']}")
                with col2:
                    st.write(f"📅 **Date:** {match_data['Date'].strftime('%d.%m.%Y')}")
                    st.write(f"⏰ **Kickoff:** {match_data['Time'].strftime('%H:%M')}")
                
                # Time Window Analysis
                st.subheader("Delays Around Match Time")
                
                match_hour = match_data['Time'].hour
                time_windows = {
                    '3 hours before': (match_hour - 3, match_hour),
                    '2 hours before': (match_hour - 2, match_hour),
                    '1 hour before': (match_hour - 1, match_hour),
                    '1 hour after': (match_hour, match_hour + 1),
                    '2 hours after': (match_hour, match_hour + 2),
                    '3 hours after': (match_hour, match_hour + 3)
                }
                
                window_stats = {}
                for window_name, (start_hour, end_hour) in time_windows.items():
                    match_window = comparison_data['Match Day'][
                        (comparison_data['Match Day']['current_stop_departure'].dt.hour >= start_hour) &
                        (comparison_data['Match Day']['current_stop_departure'].dt.hour < end_hour)
                    ]
                    regular_window = comparison_data['Week Before'][
                        (comparison_data['Week Before']['current_stop_departure'].dt.hour >= start_hour) &
                        (comparison_data['Week Before']['current_stop_departure'].dt.hour < end_hour)
                    ]
                    
                    match_avg = match_window['current_stop_dep_delay'].mean()
                    regular_avg = regular_window['current_stop_dep_delay'].mean()
                    increase = ((match_avg / regular_avg) - 1) * 100 if regular_avg > 0 else 0
                    
                    window_stats[window_name] = {
                        'match_avg': match_avg,
                        'regular_avg': regular_avg,
                        'increase': increase,
                        'sample_size': len(match_window)
                    }
                
                # Display time window analysis
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("##### Before Match")
                    for window in ['3 hours before', '2 hours before', '1 hour before']:
                        stats = window_stats[window]
                        st.metric(
                            window,
                            f"{stats['match_avg']:.0f} sec",
                            f"{stats['increase']:.1f}% vs normal",
                            help=f"Based on {stats['sample_size']} measurements",
                            delta_color="inverse"
                        )
                
                with col2:
                    st.write("##### After Match")
                    for window in ['1 hour after', '2 hours after', '3 hours after']:
                        stats = window_stats[window]
                        st.metric(
                            window,
                            f"{stats['match_avg']:.0f} sec",
                            f"{stats['increase']:.1f}% vs normal",
                            help=f"Based on {stats['sample_size']} measurements",
                            delta_color="inverse"
                        )
                
                # Add a visual summary of the time windows
                window_data = pd.DataFrame([
                    {
                        'window': window,
                        'delay': stats['match_avg'],
                        'increase': stats['increase'],
                        'is_before': 'Before' if 'before' in window else 'After'
                    }
                    for window, stats in window_stats.items()
                ])
                
                window_chart = alt.Chart(window_data).mark_bar().encode(
                    x=alt.X('window:N', 
                        sort=['3 hours before', '2 hours before', '1 hour before',
                                '1 hour after', '2 hours after', '3 hours after'],
                        title='Time Window'),
                    y=alt.Y('delay:Q', title='Average Delay (seconds)'),
                    color=alt.Color('is_before:N', 
                                scale=alt.Scale(domain=['Before', 'After'],
                                                range=['#5276A7', '#57A44C'])),
                    tooltip=[
                        alt.Tooltip('window:N', title='Time Window'),
                        alt.Tooltip('delay:Q', title='Average Delay', format='.1f'),
                        alt.Tooltip('increase:Q', title='Increase vs Normal', format='.1f')
                    ]
                ).properties(
                    width=700,
                    height=300,
                    title='Average Delays in Different Time Windows'
                )
                
                st.altair_chart(window_chart)
                st.caption(f"Analysis of delays before and after {match_data['Time'].strftime('%H:%M')} kickoff")
                
                # Traffic Impact Summary
                st.subheader("Overall Traffic Impact")
                
                # Calculate average delays
                match_avg = comparison_data['Match Day']['current_stop_dep_delay'].mean()
                regular_avg = comparison_data['Week Before']['current_stop_dep_delay'].mean()
                delay_increase = ((match_avg / regular_avg) - 1) * 100 if regular_avg > 0 else 0
                
                # Simple metrics that matter for city management
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(
                        "Overall Delay Impact",
                        f"{delay_increase:.1f}%",
                        delta=f"{match_avg - regular_avg:.0f} sec" if delay_increase > 0 else "Normal traffic",
                        delta_color="inverse"
                    )
                
                with col2:
                    # Calculate delays around match time (±2 hours)
                    match_hour = match_data['Time'].hour
                    match_window = comparison_data['Match Day'][
                        (comparison_data['Match Day']['current_stop_departure'].dt.hour >= match_hour - 2) &
                        (comparison_data['Match Day']['current_stop_departure'].dt.hour <= match_hour + 2)
                    ]
                    match_time_avg = match_window['current_stop_dep_delay'].mean()
                    
                    st.metric(
                        "Match Time Delays",
                        f"{match_time_avg:.0f} sec",
                        help="Average delays during ±2 hours around match time",
                        delta_color="inverse"
                    )
                
                with col3:
                    # Most affected hour
                    hourly_delays = comparison_data['Match Day'].groupby(
                        comparison_data['Match Day']['current_stop_departure'].dt.hour
                    )['current_stop_dep_delay'].mean()
                    worst_hour = hourly_delays.idxmax()
                    worst_delay = hourly_delays.max()
                    
                    st.metric(
                        "Peak Impact Hour",
                        f"{worst_hour:02d}:00",
                        f"{worst_delay:.0f} sec average delay"
                    )
                
                # Hourly delay visualization
                st.subheader("Hourly Delay Pattern")
                
                # Prepare hourly data
                hourly_data = []
                for day_type, day_data in {'Match Day': comparison_data['Match Day'], 
                                        'Regular Day': comparison_data['Week Before']}.items():
                    if not day_data.empty:
                        hourly = day_data.groupby(
                            day_data['current_stop_departure'].dt.hour
                        )['current_stop_dep_delay'].mean().reset_index()
                        hourly['day_type'] = day_type
                        hourly_data.append(hourly)
                
                if hourly_data:
                    hourly_df = pd.concat(hourly_data)
                    
                    chart = alt.Chart(hourly_df).mark_line(point=True).encode(
                        x=alt.X('current_stop_departure:Q', 
                            title='Hour of Day',
                            scale=alt.Scale(domain=[0, 23])),
                        y=alt.Y('current_stop_dep_delay:Q', 
                            title='Average Delay (seconds)'),
                        color=alt.Color('day_type:N', 
                                    title='Day Type'),
                        tooltip=['current_stop_departure:Q', 
                                'current_stop_dep_delay:Q', 
                                'day_type:N']
                    ).properties(
                        width=700,
                        height=400,
                        title='Hourly Delay Comparison'
                    )
                    
                    # Add match time marker
                    match_line = alt.Chart(pd.DataFrame({'x': [match_hour]})).mark_rule(
                        color='red',
                        strokeDash=[4, 4]
                    ).encode(x='x:Q')
                    
                    st.altair_chart(chart + match_line)
                    st.caption("Red dashed line shows match start time")
                    
                    # Recommendations
                    st.subheader("Recommendations")
                    if match_avg > regular_avg * 1.2:  # 20% or more increase
                        st.write("Based on the observed delays:")
                        recommendations = [
                            f"🚌 Consider additional public transport capacity {match_hour-1:02d}:00 - {match_hour+1:02d}:00",
                            "🚥 Review traffic light timing during peak impact hours",
                            "👮 Deploy additional traffic officers at key intersections"
                        ]
                        if match_data['is_home']:
                            recommendations.append("🅿️ Consider temporary parking restrictions in residential areas")
                        
                        for rec in recommendations:
                            st.write(rec)
                    else:
                        st.write("✅ Current traffic management measures appear adequate for this type of match")
        else:
            st.info("No historical match data available for analysis")