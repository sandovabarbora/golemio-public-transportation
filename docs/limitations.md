# Limitations and Future Work
## Public Transport Analysis Platform

## Current Limitations

### Deployment Constraints

#### Cloud Platform Limitations
- Unable to deploy to Heroku due to memory requirements exceeding free and hobby tier limits
- Streamlit.io cloud deployment attempts failed due to:
  - Memory usage exceeding 1GB limit on free tier
  - Large dataset processing requirements
  - Real-time computation needs

#### Resource Requirements
1. Memory Usage:
   - Peak memory consumption: 2-3GB
   - Batch processing needs: 1.5GB minimum
   - Cache requirements: 500MB-1GB
   - Current optimizations reduce but don't eliminate these requirements

2. Computational Resources:
   - CPU intensive for real-time calculations
   - High I/O requirements for data processing
   - Significant bandwidth needs for data updates

3. Storage Requirements:
   - Growing dataset size
   - Cache storage needs
   - Temporary processing files

### Financial Constraints
- Cloud hosting costs exceed current budget
- Data storage costs for complete historical data
- API usage limitations on free tiers
- Development and maintenance resource constraints

## Potential Data Source Expansions

### Waze Integration
- Real-time traffic data from Waze API
- Crowd-sourced incident reports
- Traffic flow information
- Construction and road closure updates

### FCD (Floating Car Data)
- GPS data from vehicle fleets
- Real-time vehicle positions
- Speed and direction information
- Route utilization patterns

### NDIC (National Traffic Information Center) Dataset
- National traffic infrastructure data
- Incident reports and road works
- Traffic intensity measurements
- Weather impact information

### Integration Challenges
1. Data Volume:
   - Increased storage requirements
   - Higher processing needs
   - Additional memory usage

2. Technical Requirements:
   - API integration development
   - Data transformation pipelines
   - Enhanced processing capabilities

3. Resource Implications:
   - Additional computational needs
   - Increased memory requirements
   - Higher storage costs

## AI Usage Disclosure

### Development Assistance
We utilized AI (specifically Claude) for:
- Code refactoring suggestions
- Debugging assistance
- Documentation improvements
- Performance optimization recommendations

### Original Contributions
The following remain entirely our work:
- Core application concept and design
- Algorithm development and implementation
- Data analysis methodology
- System architecture decisions
- Business logic implementation

### AI Integration Process
- AI suggestions were reviewed and validated
- Code recommendations were tested extensively
- Documentation was customized to our needs
- Original concepts were preserved

## Future Improvements

### Technical Optimizations
1. Memory Management:
   - Implement data streaming
   - Optimize cache usage
   - Improve garbage collection
   - Add data compression

2. Processing Efficiency:
   - Parallel processing implementation
   - Query optimization
   - Improved caching strategies
   - Resource usage optimization

### Infrastructure Improvements
1. Cloud Deployment:
   - Explore container orchestration
   - Investigate serverless options
   - Consider hybrid solutions
   - Implement microservices architecture

2. Scalability:
   - Database sharding
   - Load balancing
   - Distributed processing
   - Cache distribution

### Data Source Integration
1. New Data Sources:
   - Waze integration
   - FCD implementation
   - NDIC data incorporation
   - Weather data integration

2. Processing Pipeline:
   - Enhanced ETL processes
   - Real-time processing
   - Data validation
   - Quality assurance

## Energy Considerations

### Current Energy Impact
- High computational power requirements
- Continuous processing needs
- Data center energy usage
- Cooling requirements

### Optimization Opportunities
1. Processing Efficiency:
   - Optimize algorithms
   - Implement batch processing
   - Reduce computational waste
   - Improve resource utilization

2. Infrastructure:
   - Energy-efficient hardware
   - Optimal resource allocation
   - Green energy usage
   - Cooling optimization

## Next Steps

### Short-term Goals
1. Memory optimization
2. Local deployment improvements
3. Documentation updates
4. Performance enhancements

### Medium-term Goals
1. New data source integration
2. Processing pipeline optimization
3. Resource usage improvements
4. Feature enhancements

### Long-term Vision
1. Cloud deployment solution
2. Full data source integration
3. Advanced analytics implementation
4. Scalable architecture deployment

## Acknowledgments

We gratefully acknowledge the support of various AI tools that assisted with code optimization, as well as our data providers who made this project possible. However, the code base and the main idea still lies in our heads, and our heads only. Despite current technical and resource limitations, our work demonstrates the potential for comprehensive public transport analysis. We remain committed to continuous improvement through resource optimization, feature enhancement, and performance refinement as we work toward a more scalable solution.