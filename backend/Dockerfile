FROM python:3.12-slim

WORKDIR /app

# Install system dependencies and database tools
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    postgresql-client \
    gnupg \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install MongoDB Database Tools (direct download for arm64/amd64 compatibility)
# Using Ubuntu binaries which are compatible with Debian
RUN ARCH=$(dpkg --print-architecture) && \
    echo "Detected architecture: $ARCH" && \
    if [ "$ARCH" = "arm64" ]; then \
        MONGO_TOOLS_URL="https://fastdl.mongodb.org/tools/db/mongodb-database-tools-ubuntu2204-arm64-100.9.5.tgz"; \
    else \
        MONGO_TOOLS_URL="https://fastdl.mongodb.org/tools/db/mongodb-database-tools-ubuntu2204-x86_64-100.9.5.tgz"; \
    fi && \
    echo "Downloading from: $MONGO_TOOLS_URL" && \
    wget --verbose $MONGO_TOOLS_URL -O mongodb-tools.tgz && \
    echo "Extracting MongoDB tools..." && \
    tar -zxf mongodb-tools.tgz && \
    mv mongodb-database-tools-*/bin/* /usr/local/bin/ && \
    rm -rf mongodb-tools.tgz mongodb-database-tools-* && \
    echo "MongoDB tools installed successfully"

# Copy and install Python dependencies (includes LiveKit)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY agent/ ./agent/
COPY mcp/ ./mcp/

# Create data directory
RUN mkdir -p /app/data /app/agents

# Expose ports
EXPOSE 8000 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run FastAPI server
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
