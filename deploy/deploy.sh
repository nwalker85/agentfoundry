#!/usr/bin/env bash
# deploy.sh - Automated deployment script for Agent Foundry
set -euo pipefail

# Configuration
ENVIRONMENT="${ENVIRONMENT:-dev}"
TERRAFORM_DIR="terraform"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Check prerequisites
info "Checking prerequisites..."

command -v terraform >/dev/null 2>&1 || error "Terraform not installed"
command -v docker >/dev/null 2>&1 || error "Docker not installed"
command -v aws >/dev/null 2>&1 || error "AWS CLI not installed"

if [[ ! -f "$PROJECT_ROOT/.env" ]]; then
    error ".env file not found. Create one from .env.example"
fi

# Get instance IP from Terraform
cd "$PROJECT_ROOT/$TERRAFORM_DIR"

if [[ ! -f "terraform.tfstate" ]]; then
    error "Terraform state not found. Run 'terraform apply' first"
fi

info "Getting instance IP from Terraform..."
INSTANCE_IP=$(terraform output -raw instance_public_ip 2>/dev/null || error "Could not get instance IP")
SSH_KEY=$(terraform output -raw ssh_connection 2>/dev/null | sed -n 's/.*-i \(.*\.pem\).*/\1/p')

if [[ -z "$INSTANCE_IP" ]]; then
    error "Could not determine instance IP"
fi

info "Target instance: $INSTANCE_IP"
info "SSH key: $SSH_KEY"

cd "$PROJECT_ROOT"

# Test SSH connection
info "Testing SSH connection..."
if ! ssh -i "$SSH_KEY" -o ConnectTimeout=5 -o StrictHostKeyChecking=no \
    ec2-user@"$INSTANCE_IP" "echo SSH connection successful" >/dev/null 2>&1; then
    error "Cannot connect to instance via SSH"
fi

# Build Docker images (optional)
read -p "Build Docker images locally? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    info "Building Docker images..."
    docker-compose build
fi

# Deploy code
info "Deploying code to EC2..."
rsync -avz --progress \
    --exclude 'node_modules' \
    --exclude '.git' \
    --exclude '.env' \
    --exclude 'venv' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '.pytest_cache' \
    --exclude 'data' \
    -e "ssh -i $SSH_KEY -o StrictHostKeyChecking=no" \
    . ec2-user@"$INSTANCE_IP":/opt/agent-foundry/

# Restart services on EC2
info "Restarting services..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ec2-user@"$INSTANCE_IP" << 'REMOTE_SCRIPT'
cd /opt/agent-foundry

# Pull latest images
docker-compose pull

# Restart services with rebuild
docker-compose up -d --build

# Wait for health checks
echo "Waiting for services to be healthy..."
sleep 10

# Show status
docker-compose ps
REMOTE_SCRIPT

# Verify deployment
info "Verifying deployment..."
if ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ec2-user@"$INSTANCE_IP" \
    "curl -sf http://localhost:8000/health" >/dev/null 2>&1; then
    info "✅ Backend health check passed"
else
    warn "⚠️  Backend health check failed"
fi

if ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ec2-user@"$INSTANCE_IP" \
    "curl -sf http://localhost:7880" >/dev/null 2>&1; then
    info "✅ LiveKit health check passed"
else
    warn "⚠️  LiveKit health check failed"
fi

# Show logs
read -p "View service logs? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ec2-user@"$INSTANCE_IP" \
        "cd /opt/agent-foundry && docker-compose logs --tail=50"
fi

info "=========================================="
info "✅ Deployment complete!"
info "=========================================="
info "Instance: $INSTANCE_IP"
info "SSH: ssh -i $SSH_KEY ec2-user@$INSTANCE_IP"
info "Logs: ssh ... 'cd /opt/agent-foundry && docker-compose logs -f'"
