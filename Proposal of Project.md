# **Public Transport Delay Analysis for Event-Driven Scenarios**

## **Overview**

This project analyzes how Sparta Prague football matches affect public transport delays in the Letná district of Prague. Using data from the Golemio API, including public transport delays, stop information, and match attendance, we aim to uncover patterns and correlations. Historical transport data stored in Parquet files will be processed with DuckDB for efficient analysis. A machine learning-based predictive model, incorporating techniques like Random Forest, regression, or Kalman Filter, will be developed to forecast delays. The findings will be visualized through charts and interactive maps, providing actionable insights to improve public transport operations during major events.

---

## **Objectives**

1. Focus only on public transport stops within the Letná district:
   - **Stops:** Hradčanská, Sparta, Korunovační, Letenské náměstí, Kamenická, Strossmayerovo náměstí, Nábřeží Kapitána Jaroše, Vltavská, Veletržní, Veletržní palác.
   
2. Collect Sparta Prague match data:
   - **Data Points:** Match schedules, attendance, and timing.

3. Retrieve data to analyze public transport delays from:
   - **Available API Endpoints:**
     - `/v2/public/stoptimes`
     - `/v2/public/stops`
     - `/v1/parkings`
     - `/v2/pedestrians/measurements`
     - `/v2/fcd/info`
   - **Parquet Files** Stop times in history in parquet files, readable via DuckDB. Parquet file is provided by Golemio itself.

**Key Metrics:** Delays at selected stops during match days vs. non-match days.

4. Develop a predictive algorithm to model delays based on:
   - Match attendance, timing, and location.
   - Historical delay data at Letná district stops.
   - Model to predict delays.

5. **Visualizing Findings and Insights**

- **Tools**:
  - **Matplotlib**: For graphs and charts, enabling time-series analysis and comparisons of delays on match days versus regular days.
  - **Folium**: For geospatial visualizations, such as interactive maps to highlight delay intensity and identify hotspots at affected public transport stops.

- **Package**:
  - The greater idea behind the model is to create a reusable Python package. This package would analyze and predict public transport delays related to various cultural events, providing a scalable solution for event-driven transport optimization.

---

## **Proposed Technologies**

### **Data Collection and Storage**
- **APIs and Data Sources:**
  - Golemio Public Transport API for delays and stop data.
  - Official Sparta Prague match schedules and attendance reports.
- (Optional) **Databases:**
  - based on the data size
  - **DuckDB:** For lightweight, in-memory data analysis, parquet reading.

### **Data Processing and Analysis**
- **Python Libraries:**
  - **Requests:** For API calls.
  - **Pandas:** For data manipulation and analysis.
  - **NumPy:** For numerical calculations.
  - **GeoPandas:** For geospatial analysis and mapping.
  - **ML Libraries** (e.g. scikit-learn)

### **Visualization**
- **Matplotlib:** For time-series and delay analysis charts.
- **Folium:** For interactive geospatial visualizations of delays at Letná stops.

---

## **Approach**

### **Phase 1: Data Collection**
1. **Stop Data:**
   - Retrieve delay and vehicle data for Letná district stops via the Golemio API.
   - Filter relevant endpoints such as:
     - `/v2/public/stops`
     - `/v2/public/stoptimes`
     - parquet files by Golemio

2. **Match Data:**
   - Collect match schedules, start times, and attendance numbers for Sparta Prague.

3. **Additional Data Sources:**
   - Utilize supplementary endpoints:
     - `/v1/parkings`
     - `/v2/pedestrians/measurements`
     - `/v2/fcd/info`

---

### **Phase 2: Data Preprocessing**
1. **Data Cleaning:**
   - Standardize timestamps across datasets.
   - Filter data for Letná district stops only.

2. **Feature Engineering:**
   - Create features like:
     - Match timing and attendance.
     - Average delays by hour and day of the week.
     - Historical delay trends.

3. **Exploratory Data Analysis:**
   - Compare delay patterns on match days versus non-match days.
   - Visualize correlations between match attendance and delays.

---

### **Phase 3: Predictive Algorithm**
1. **Model Development:**
   - Use historical delay data, match attendance, and timing as inputs.
   - Develop regression models (e.g., Linear Regression, Random Forest) to predict delays.

2. **Algorithm Refinement:**
   - Test and optimize models using metrics like RMSE and R².
   - Incorporate additional features from various API endpoints.

3. (Optional) **Scenario Simulation:** 
   - Simulate delay scenarios for future matches based on attendance and other inputs.

---

### **Phase 4: Visualization**
1. **Matplotlib:**
   - Plot delay trends and travel times by time and stop.
   - Display comparative bar graphs for match and non-match days.

2. **Folium:**
   - Create an interactive map showing delay intensity at each stop in Letná.
   - Use color-coded markers to represent delay severity.

---

### **Phase 5: Insights and Recommendations**
1. **Insights:**
   - Identify specific stops and times with the most significant delays during match days.
   - Highlight trends between match attendance and public transport delays.

2. **Recommendations:**
   - Suggest improvements in public transport scheduling during match days.
   - Propose scalable delay prediction algorithm.

---

## **Success Metrics**

The success of this project will be evaluated using the following academic-oriented criteria:

1. **Model Performance:** 
   - Achieve a statistically robust predictive model and decide model performance by R^2.

2. **Statistical Correlation:** 
   - Demonstrate correlation between match-related variables (e.g., attendance, timing) and public transport delays.

3. **Reproducibility and Methodological Soundness:** 
   - Ensure the methodology is thoroughly documented, enabling replication of results by other researchers or practitioners.

4. **Visualization Impact:** 
   - Deliver clear and actionable visualizations with a focus on interpretability and utility.

5. **Practical Insights:** 
   - Provide transport management recommendations backed by quantifiable improvements in service predictability or reduced delay variance during match events.

---

## **Contact**

Vojtěch Strachota, Barbora Šandová