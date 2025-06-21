FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy load testing files
COPY . .

# Expose Locust web interface port
EXPOSE 8089

# Set default command to run Locust with PaymentServiceUser only
CMD ["locust", "--host=http://payment-service:8000", "--web-host=0.0.0.0", "--web-port=8089", "PaymentServiceUser"]