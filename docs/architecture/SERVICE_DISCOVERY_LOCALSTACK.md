# LocalStack Integration with Service Discovery

## Overview

LocalStack is fully integrated with the **Infrastructure as Registry** service
discovery pattern. This ensures consistent service communication between
LocalStack and other services in the system.

## Configuration

### Service Registry

LocalStack is defined in `backend/config/services.py`:

```python
class ServiceConfig:
    # Infrastructure services
    LOCALSTACK = os.getenv("SVC_LOCALSTACK_HOST", "localstack")

    # LocalStack gateway port
    LOCALSTACK_PORT = int(os.getenv("LOCALSTACK_PORT", "4566"))

    @classmethod
    def get_service_url(cls, service_name: str) -> str:
        if service_name == "LOCALSTACK":
            return f"http://{cls.LOCALSTACK}:{cls.LOCALSTACK_PORT}"
```

### Docker Compose

```yaml
localstack:
  image: localstack/localstack:latest
  ports:
    - '4566:4566' # External port mapping only
  networks:
    - foundry

foundry-backend:
  environment:
    # Service discovery - DNS name only
    - SVC_LOCALSTACK_HOST=localstack
    - LOCALSTACK_PORT=4566
  depends_on:
    localstack:
      condition: service_healthy
```

## Usage

### Backend (Secrets Manager)

```python
from backend.config.services import SERVICES

# Get LocalStack endpoint via service discovery
endpoint_url = SERVICES.get_service_url("LOCALSTACK")
# Returns: http://localstack:4566

# Use with boto3
import boto3
client = boto3.client(
    'secretsmanager',
    endpoint_url=endpoint_url,  # Service discovery!
    region_name='us-east-1',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)
```

### Automatic Environment Detection

The secrets manager automatically uses the correct endpoint:

```python
# backend/config/secrets.py
def _create_client(self):
    if self.environment in ("development", "dev", "local"):
        # Development: Use service discovery to find LocalStack
        from backend.config.services import SERVICES
        endpoint_url = SERVICES.get_service_url("LOCALSTACK")
        # endpoint_url = http://localstack:4566

        client = boto3.client(
            'secretsmanager',
            endpoint_url=endpoint_url,
            ...
        )
    else:
        # Production: Use AWS Secrets Manager (no endpoint needed)
        client = boto3.client('secretsmanager', ...)
```

## Benefits

### ✅ Consistent with Service Discovery Pattern

```python
# All services use the same pattern
backend_url = SERVICES.get_service_url("BACKEND")      # http://foundry-backend:8080
compiler_url = SERVICES.get_service_url("COMPILER")    # http://foundry-compiler:8080
localstack_url = SERVICES.get_service_url("LOCALSTACK") # http://localstack:4566
```

### ✅ No Hardcoded URLs

**Before (❌ Bad):**

```python
endpoint_url = os.getenv("LOCALSTACK_ENDPOINT", "http://localstack:4566")
```

**After (✅ Good):**

```python
from backend.config.services import SERVICES
endpoint_url = SERVICES.get_service_url("LOCALSTACK")
```

### ✅ Easy to Override

```bash
# Override LocalStack hostname (e.g., for external testing)
export SVC_LOCALSTACK_HOST=external-localstack.example.com
export LOCALSTACK_PORT=4566

# Code automatically uses: http://external-localstack.example.com:4566
```

### ✅ Works with Both Docker and Kubernetes

**Docker Compose:**

```yaml
# Service name: localstack
# Resolves to: http://localstack:4566
```

**Kubernetes:**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: localstack # ← Same name!
spec:
  ports:
    - port: 4566
```

Application code works identically in both environments.

## Service Communication Flow

```
Backend Service (Python)
  ↓
SERVICES.get_service_url("LOCALSTACK")
  ↓
Docker/K8s DNS Resolution
  ↓
localstack service (http://localstack:4566)
  ↓
LocalStack Container
```

## Configuration Reference

### Environment Variables

| Variable              | Default      | Description  |
| --------------------- | ------------ | ------------ |
| `SVC_LOCALSTACK_HOST` | `localstack` | DNS hostname |
| `LOCALSTACK_PORT`     | `4566`       | Gateway port |
| `AWS_REGION`          | `us-east-1`  | AWS region   |

### Service URLs

```python
from backend.config.services import SERVICES

# Get full URL
url = SERVICES.get_service_url("LOCALSTACK")
# http://localstack:4566

# Get hostname only
host = SERVICES.LOCALSTACK
# localstack

# Get port only
port = SERVICES.LOCALSTACK_PORT
# 4566

# Build custom endpoint
endpoint = f"http://{SERVICES.LOCALSTACK}:{SERVICES.LOCALSTACK_PORT}/custom"
# http://localstack:4566/custom
```

## Testing Service Discovery

### Verify DNS Resolution

```bash
# From backend container
docker-compose exec foundry-backend ping localstack

# Should resolve to LocalStack container IP
```

### Verify Service URL

```bash
# From backend container
docker-compose exec foundry-backend python -c "
from backend.config.services import SERVICES
print(SERVICES.get_service_url('LOCALSTACK'))
"

# Should print: http://localstack:4566
```

### Test Connection

```bash
# From backend container
docker-compose exec foundry-backend curl http://localstack:4566/_localstack/health

# Should return health status
```

## Troubleshooting

### Service Not Found

```bash
# Check LocalStack is running
docker-compose ps localstack

# Check DNS resolution
docker-compose exec foundry-backend nslookup localstack

# Verify on same network
docker network inspect agentfoundry_foundry
```

### Wrong Endpoint

```python
# Debug: Print resolved URL
from backend.config.services import SERVICES
print(f"LocalStack URL: {SERVICES.get_service_url('LOCALSTACK')}")

# Check environment variables
import os
print(f"Host: {os.getenv('SVC_LOCALSTACK_HOST', 'localstack')}")
print(f"Port: {os.getenv('LOCALSTACK_PORT', '4566')}")
```

### Cannot Connect

```bash
# Test from host
curl http://localhost:4566/_localstack/health

# Test from backend container
docker-compose exec foundry-backend curl http://localstack:4566/_localstack/health

# Check health status
docker-compose ps localstack
```

## Production Notes

### AWS Secrets Manager

In production, the secrets manager automatically bypasses LocalStack:

```python
# backend/config/secrets.py
if self.environment == "production":
    # No endpoint_url needed - uses AWS directly
    client = boto3.client('secretsmanager', region_name=self.region)
```

No code changes needed - controlled by `ENVIRONMENT` variable.

### Service Discovery Still Works

Even in production, the SERVICES config remains consistent:

```python
# Works in both dev and prod
from backend.config.services import SERVICES

# Development: Returns LocalStack URL
# Production: Would return production service URL (if needed)
url = SERVICES.get_service_url("LOCALSTACK")
```

This maintains consistency across all environments.

## Summary

LocalStack integration follows the same service discovery pattern as all other
services:

✅ **DNS-based naming** (`localstack` service name)  
✅ **Centralized configuration** (`SERVICES.LOCALSTACK`)  
✅ **No hardcoded URLs** in application code  
✅ **Environment-aware** (dev = LocalStack, prod = AWS)  
✅ **Portable** (Docker Compose → Kubernetes)  
✅ **Consistent** with other infrastructure services

This ensures LocalStack is treated as a first-class infrastructure service with
the same patterns as Redis, PostgreSQL, LiveKit, etc.
