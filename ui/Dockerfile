# Production Dockerfile for Render Streamlit Frontend
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download en_core_web_sm

# Copy application source
COPY . .

# Expose default port
EXPOSE 8501

# Run Streamlit with dynamic PORT environment variable provided by Render
CMD ["sh", "-c", "streamlit run ui/app.py --server.port=${PORT:-8501} --server.address=0.0.0.0"]
