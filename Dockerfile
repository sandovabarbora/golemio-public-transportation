# Use an official Python runtime as a base image.
FROM python:3.11-slim

# Update package list and install system dependencies, including CA certificates.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set an environment variable so Python uses the system CA certificates.
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

# Set the working directory.
WORKDIR /app

# Copy requirements.txt first to leverage Docker's caching.
COPY requirements.txt /app/requirements.txt

# Upgrade pip and install dependencies.
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code.
COPY . /app

# Expose the port that Streamlit uses.
EXPOSE 8501

# Command to run your Streamlit app.
CMD ["streamlit", "run", "app.py", "--server.enableCORS", "false"]
