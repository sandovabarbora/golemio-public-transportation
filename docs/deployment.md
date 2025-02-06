# Local and Docker Deployment Guide
## Public Transport Analysis Dashboard

### 1. Repository Setup

The application is structured as follows:
```
public-transport-analysis/
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose configuration
├── app.py                  # Main application
├── requirements.txt        # Dependencies
├── data/                  # Data files
│   ├── letna_stops.csv
│   └── sparta_matches.csv
└── src/                   # Source code
    ├── connectors/
    ├── models/
    ├── utils/
    └── views/
```

### 2. Local Development Setup

1. Clone the repository:
```bash
git clone https://github.com/sandovabarbora/golemio-public-transportation
cd golemio-public-transportation
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

4. Set up environment variables:
```bash
# Create .env file
cp .env.example .env

# Edit .env with your credentials:
# - parquetAzureTenantID
# - parquetAzureAppID
# - parquetAzureClientSecret
# - parquetStorageName
# - X-Access-Token-Golemio
```

5. Run the application:
```bash
streamlit run app.py
```

The application will be available at http://localhost:8501

### 3. Docker Deployment

1. Build and run using Docker Compose:
```bash
docker-compose up --build
```

Or build and run manually:

```bash
# Build the image
docker build -t transport-analysis .

# Run the container
docker run -p 8501:8501 --env-file .env transport-analysis
```

2. Access the application at http://localhost:8501

#### Docker Configuration

Dockerfile:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py"]
```

docker-compose.yml:
```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8501:8501"
    env_file:
      - .env
    volumes:
      - .:/app
```

### 4. Memory Management

The application requires significant memory resources due to:
- Large dataset processing
- Real-time analytics
- Interactive visualizations

Current limitations:
- Memory usage can exceed free tier limits of cloud platforms
- Large-scale deployments require careful resource management
- Working on optimizing memory footprint for cloud deployment

Memory optimization techniques implemented:
- Lazy loading of large datasets
- Data filtering at source
- Efficient data structure usage
- Regular garbage collection

### 5. Future Deployment Plans

Next steps for deployment optimization:
1. Implement data chunking for large datasets
2. Add database caching layer
3. Optimize memory usage patterns
4. Explore cloud deployment options with higher resource limits

### 6. Performance Monitoring

Monitor resource usage:
```bash
# Using docker stats
docker stats transport-analysis

# Or for local deployment
top -pid $(pgrep -f streamlit)
```

### 7. Troubleshooting

Common issues and solutions:

1. Memory errors:
   - Reduce data load size
   - Increase Docker container memory limit
   - Use data filtering

2. Connection issues:
   - Verify environment variables
   - Check network connectivity
   - Confirm Azure credentials

3. Performance issues:
   - Monitor resource usage
   - Adjust cache settings
   - Optimize query patterns

### 8. Resources

- GitHub Repository: https://github.com/sandovabarbora/golemio-public-transportation
- Documentation: See /docs folder in repository
- Issue Tracking: GitHub Issues

### 9. Security Notes

1. Environment Variables:
   - Never commit .env file
   - Use secrets management in production
   - Rotate credentials regularly

2. Data Protection:
   - Enable encryption at rest
   - Implement access controls
   - Follow security best practices

3. Container Security:
   - Keep base images updated
   - Scan for vulnerabilities
   - Follow least privilege principle
