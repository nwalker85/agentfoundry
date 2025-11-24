## LEGACY / ARCHIVE – Single EC2 Deployment Flow

> **Note:** This document preserves the original **single‑EC2 + docker‑compose**
> deployment pattern.  
> The **current, supported** AWS deployment path uses **ECR + ECS Fargate +
> ALB** via `infra/` and is documented in `DEPLOYMENT.md`.

# Agent Foundry - Deployment Quick Reference (Legacy EC2)

## 🚀 First-Time Deployment (5 Steps)

### 1️⃣ Push Secrets to AWS SSM

```bash
# Generate bootstrap script
./scripts/env_to_ssm.py \
  --env-file .env \
  --prefix /foundry/dev \
  --format bash \
  --overwrite > deploy/bootstrap_secrets.sh

# Execute
chmod +x deploy/bootstrap_secrets.sh
./deploy/bootstrap_secrets.sh

# Verify
aws ssm get-parameters-by-path --path /foundry/dev --with-decryption
```

### 2️⃣ Create SSH Key (if needed)

```bash
aws ec2 create-key-pair \
  --key-name foundry-dev \
  --query 'KeyMaterial' \
  --output text > ~/.ssh/foundry-dev.pem

chmod 400 ~/.ssh/foundry-dev.pem
```

### 3️⃣ Configure & Deploy Infrastructure

```bash
cd terraform

# Copy and edit variables
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars

# Deploy
terraform init
terraform plan
terraform apply

# Save IP
terraform output -raw instance_public_ip
```

### 4️⃣ Update DNS

```bash
# Point your domain to the Elastic IP
ELASTIC_IP=$(terraform output -raw instance_public_ip)
echo "Point foundry.ravenhelm.dev → $ELASTIC_IP"
```

### 5️⃣ Deploy Application

```bash
cd ..
./deploy/deploy.sh
```

---

## 🔄 Regular Deployments

```bash
# One command deployment
./deploy/deploy.sh
```

---

## 🔐 Update Secrets

```bash
# Edit .env locally, then:
./scripts/env_to_ssm.py \
  --env-file .env \
  --prefix /foundry/dev \
  --format bash \
  --overwrite > deploy/update_secrets.sh

chmod +x deploy/update_secrets.sh
./deploy/update_secrets.sh

# Restart services on EC2
ssh -i ~/.ssh/foundry-dev.pem ec2-user@YOUR_IP \
  'cd /opt/agent-foundry && ENVIRONMENT=dev ./deploy/fetch_env_from_ssm.sh && docker-compose restart'
```

---

## 📊 Monitoring

```bash
# SSH to instance
ssh -i ~/.ssh/foundry-dev.pem ec2-user@YOUR_IP

# View logs
docker-compose logs -f

# Check status
docker-compose ps

# Health checks
curl localhost:8000/health
curl localhost:7880
```

---

## 🔧 Troubleshooting

### Secrets not loading?

```bash
# From EC2 instance
aws ssm get-parameters-by-path --path /foundry/dev --with-decryption
ENVIRONMENT=dev ./deploy/fetch_env_from_ssm.sh
cat .env
```

### Services not starting?

```bash
docker-compose down
docker-compose pull
docker-compose up -d --build
docker-compose logs -f
```

### Can't SSH?

```bash
# Check security group
aws ec2 describe-security-groups --filters Name=group-name,Values=foundry-sg-dev

# Check instance status
aws ec2 describe-instances --instance-ids YOUR_INSTANCE_ID
```

---

## 💰 Cost Management

```bash
# Stop instance (dev only)
aws ec2 stop-instances --instance-ids YOUR_INSTANCE_ID

# Start when needed
aws ec2 start-instances --instance-ids YOUR_INSTANCE_ID
```

**Monthly cost (historical estimate):** ~$17–20 for a single dev instance.

---

## 🗑️ Teardown

```bash
cd terraform
terraform destroy

# Optional: Delete secrets
aws ssm delete-parameters \
  --names $(aws ssm get-parameters-by-path \
    --path /foundry/dev \
    --query 'Parameters[*].Name' \
    --output text)
```

---

## 📚 Full Documentation (Legacy)

- `deploy/AWS_DEPLOYMENT_GUIDE.md` – original EC2‑centric deployment guide
