FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install compiler-specific dependencies
RUN pip install --no-cache-dir \
    pyyaml \
    pydantic \
    python-multipart

# Copy compiler code
COPY compiler/ ./compiler/

# Create directories
RUN mkdir -p /app/agents /app/data

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8002/health || exit 1

# Run FastAPI server
CMD ["python", "-m", "uvicorn", "compiler.main:app", "--host", "0.0.0.0", "--port", "8002", "--reload"]
