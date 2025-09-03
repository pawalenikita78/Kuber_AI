FROM python:3.12-slim
WORKDIR /app

# Install build tools for FAISS and other ML dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \  # FAISS often requires cmake
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from the API_rag directory
COPY API_rag/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy only the API_rag directory contents
COPY API_rag/ /app/

EXPOSE 8002

# Check case - usually it's "app" (lowercase) in FastAPI
CMD ["uvicorn", "rag_gold_api:app", "--host", "0.0.0.0", "--port", "8002", "--reload"]