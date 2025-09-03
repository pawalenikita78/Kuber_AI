FROM python:3.12-slim
WORKDIR /app

# Install system dependencies including netcat for health checks
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    netcat-openbsd \  # Added for better dependency handling
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY API_plans/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \  # Added pip upgrade
    pip install --no-cache-dir -r /app/requirements.txt

# Copy the entire API_plans directory
COPY API_plans/ /app/

# Make entrypoint script executable
RUN chmod +x entrypoint.sh  # Added this line

EXPOSE 8001

# Changed from direct uvicorn to entrypoint script
CMD ["/app/entrypoint.sh"]  # Changed this line