FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set Python path to include /app
ENV PYTHONPATH="/app:${PYTHONPATH}"

# Create working directories
RUN mkdir -p /app/working_dir /app/project_source

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run Streamlit (overridden by docker-compose command)
CMD ["streamlit", "run", "ui/streamlit_app.py", "--server.address=0.0.0.0"]
