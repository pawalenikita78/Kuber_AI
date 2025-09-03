FROM python:3.12-slim
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install system dependencies - ADD netcat for health checks
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    netcat-openbsd \  # ← ADDED for better health checking
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Add after COPY . .
COPY wait-for-db.sh /app/wait-for-db.sh
RUN chmod +x /app/wait-for-db.sh

# Create non-root user for security
RUN useradd -m -r appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

# Update CMD
CMD ["sh", "-c", "/app/wait-for-db.sh db 3306 && python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]