FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy forge service code
COPY forge_service /app/forge_service

# Create directories for agents and data
RUN mkdir -p /app/agents /app/data/forge

# Expose port
EXPOSE 8003

# Run the forge service
CMD ["python", "-m", "uvicorn", "forge_service.main:app", "--host", "0.0.0.0", "--port", "8003", "--reload"]
