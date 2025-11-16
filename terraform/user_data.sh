#!/bin/bash
# EC2 User Data Script - Agent Foundry Bootstrap
set -euo pipefail

# Configuration
ENVIRONMENT="${environment}"
DOMAIN="${domain}"
APP_DIR="/opt/agent-foundry"
REPO_URL="https://github.com/yourorg/agent-foundry.git"  # TODO: Update with actual repo

# Logging
exec > >(tee -a /var/log/foundry-bootstrap.log)
exec 2>&1

echo "=========================================="
echo "Agent Foundry Bootstrap - $(date)"
echo "Environment: $ENVIRONMENT"
echo "Domain: $DOMAIN"
echo "=========================================="

# Update system
echo "Updating system packages..."
yum update -y

# Install Docker
echo "Installing Docker..."
yum install -y docker
systemctl start docker
systemctl enable docker
usermod -aG docker ec2-user

# Install Docker Compose
echo "Installing Docker Compose..."
DOCKER_COMPOSE_VERSION="2.24.0"
curl -L "https://github.com/docker/compose/releases/download/v$${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose

# Install Git
echo "Installing Git..."
yum install -y git

# Install AWS CLI (should be pre-installed on AL2023, but ensure latest)
echo "Updating AWS CLI..."
yum install -y aws-cli

# Clone repository
echo "Cloning Agent Foundry repository..."
mkdir -p $APP_DIR
# TODO: Replace with actual git clone when repo is set up
# For now, we'll expect code to be deployed via another mechanism
# git clone $REPO_URL $APP_DIR

# For MVP, we'll assume code is deployed via rsync/scp from local machine
# Create directory structure
mkdir -p $APP_DIR/{backend,frontend,compiler,deploy,data,agents}

# Fetch secrets from SSM
echo "Fetching secrets from AWS SSM Parameter Store..."
# We'll create a temporary fetch script since the repo might not be cloned yet
cat > /tmp/fetch_secrets.sh << 'FETCH_EOF'
#!/usr/bin/env bash
set -euo pipefail

PREFIX="/foundry/$ENVIRONMENT"
OUTPUT_FILE="/opt/agent-foundry/.env"

echo "Fetching secrets from SSM path: $PREFIX"
mkdir -p "$(dirname "$OUTPUT_FILE")"
> "$OUTPUT_FILE"

aws ssm get-parameters-by-path \
  --path "$PREFIX" \
  --with-decryption \
  --query 'Parameters[*].[Name,Value]' \
  --output text | \
while IFS=$'\t' read -r name value; do
  key="$${name##*/}"
  echo "$${key}=$${value}" >> "$OUTPUT_FILE"
done

chmod 600 "$OUTPUT_FILE"
echo "✅ Secrets fetched to $OUTPUT_FILE ($(wc -l < "$OUTPUT_FILE") variables)"
FETCH_EOF

chmod +x /tmp/fetch_secrets.sh
ENVIRONMENT=$ENVIRONMENT /tmp/fetch_secrets.sh

# Pull Docker images
echo "Pulling Docker images..."
docker pull livekit/livekit-server:latest
docker pull redis:7-alpine

# Setup systemd service for automatic restart
echo "Creating systemd service..."
cat > /etc/systemd/system/foundry.service << 'SERVICE_EOF'
[Unit]
Description=Agent Foundry Platform
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/agent-foundry
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
ExecReload=/usr/local/bin/docker-compose restart
User=root

[Install]
WantedBy=multi-user.target
SERVICE_EOF

systemctl daemon-reload
systemctl enable foundry.service

# Note: We won't start the service yet since the application code needs to be deployed first

# Install Certbot for Let's Encrypt SSL (for later)
echo "Installing Certbot..."
yum install -y certbot python3-certbot-nginx

# Create log rotation
cat > /etc/logrotate.d/foundry << 'LOGROTATE_EOF'
/opt/agent-foundry/data/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 ec2-user ec2-user
}
LOGROTATE_EOF

# Set proper permissions
chown -R ec2-user:ec2-user $APP_DIR

echo "=========================================="
echo "✅ Bootstrap complete - $(date)"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Deploy application code to $APP_DIR"
echo "2. Ensure docker-compose.yml is present"
echo "3. Start services: systemctl start foundry"
echo "4. Check logs: journalctl -u foundry -f"
echo ""
echo "Access:"
echo "- SSH: ssh ec2-user@$DOMAIN"
echo "- HTTP: http://$DOMAIN"
echo ""
