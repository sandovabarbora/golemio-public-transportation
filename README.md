# **Project Proposal: Examining the Impact of Sparta Prague Matches on Public Transport Delays in Letná District**

## **Overview**

This project aims to analyze the correlation between Sparta Prague football matches and public transport delays at specific stops in the Letná district. By combining match data, public transport delays, and other relevant data sources, we will develop a predictive algorithm to improve delay forecasting and provide actionable visualizations using tools like Matplotlib and Folium.

---

## **Objectives**

1. Focus only on public transport stops within the Letná district:
   - **Stops:** Hradčanská, Sparta, Korunovační, Letenské náměstí, Kamenická, Strossmayerovo náměstí, Nábřeží Kapitána Jaroše, Vltavská, Veletržní, Veletržní palác.
   
2. Collect Sparta Prague match data:
   - **Data Points:** Match schedules, attendance, and timing.

3. Retrieve data from the Golemio API to analyze public transport delays:
   - **Available Endpoints:**
     - `/v2/public/departureboards`
     - `/v2/public/stoptimes`
     - `/v2/public/stops`
     - `/v1/parkings`
     - `/v2/pedestrians/measurements`
     - `/v2/fcd/info`
   - **Key Metrics:** Delays at selected stops during match days vs. non-match days.

4. Develop a predictive algorithm to model delays based on:
   - Match attendance, timing, and location.
   - Historical delay data at Letná district stops.
   - Model to predict delays.

5. Visualize findings and insights:
   - **Tools:** Matplotlib for graphs and charts, Folium for geospatial visualizations.

---

## **Proposed Technologies**

### **Data Collection and Storage**
- **APIs and Data Sources:**
  - Golemio Public Transport API for delays and stop data.
  - Official Sparta Prague match schedules and attendance reports.
- (Optional) **Databases:**
  - based on the data size
  - **DuckDB:** For lightweight, in-memory data analysis.

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
- **Plotly/Dash:** Optional for creating web-based interactive visualizations.

---

## **Approach**

### **Phase 1: Data Collection**
1. **Stop Data:**
   - Retrieve delay and vehicle data for Letná district stops via the Golemio API.
   - Filter relevant endpoints such as:
     - `/v2/public/stops`
     - `/v2/public/departureboards`
     - `/v2/public/stoptimes`

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