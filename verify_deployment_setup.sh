#!/usr/bin/env bash
# verify_deployment_setup.sh - Verify deployment infrastructure is ready

set -euo pipefail

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { echo -e "${GREEN}✅${NC} $1"; }
fail() { echo -e "${RED}❌${NC} $1"; }
warn() { echo -e "${YELLOW}⚠️${NC}  $1"; }

PROJECT_ROOT="/Users/nwalker/Development/Projects/agentfoundry"

echo "=========================================="
echo "Agent Foundry - Deployment Setup Verification"
echo "=========================================="
echo ""

# Check files exist
echo "📁 Checking deployment files..."
FILES=(
    "scripts/env_to_ssm.py"
    "deploy/fetch_env_from_ssm.sh"
    "deploy/deploy.sh"
    "terraform/main.tf"
    "terraform/user_data.sh"
    "terraform/terraform.tfvars.example"
    ".gitignore"
    "DEPLOYMENT.md"
)

for file in "${FILES[@]}"; do
    if [[ -f "$PROJECT_ROOT/$file" ]]; then
        pass "$file"
    else
        fail "$file (MISSING)"
    fi
done

echo ""
echo "🔧 Checking script permissions..."
SCRIPTS=(
    "scripts/env_to_ssm.py"
    "deploy/fetch_env_from_ssm.sh"
    "deploy/deploy.sh"
)

for script in "${SCRIPTS[@]}"; do
    if [[ -x "$PROJECT_ROOT/$script" ]]; then
        pass "$script (executable)"
    else
        warn "$script (not executable - run: chmod +x $script)"
    fi
done

echo ""
echo "🔑 Checking prerequisites..."

# Check .env
if [[ -f "$PROJECT_ROOT/.env" ]]; then
    pass ".env file exists"
    ENV_LINES=$(wc -l < "$PROJECT_ROOT/.env")
    echo "   Contains $ENV_LINES lines"
else
    fail ".env file missing - create from .env.example"
fi

# Check AWS CLI
if command -v aws >/dev/null 2>&1; then
    pass "AWS CLI installed"
    if aws sts get-caller-identity >/dev/null 2>&1; then
        pass "AWS credentials configured"
        AWS_IDENTITY=$(aws sts get-caller-identity --query 'Arn' --output text)
        echo "   $AWS_IDENTITY"
    else
        fail "AWS credentials not configured"
    fi
else
    fail "AWS CLI not installed"
fi

# Check Terraform
if command -v terraform >/dev/null 2>&1; then
    pass "Terraform installed"
    TERRAFORM_VERSION=$(terraform version -json | grep -o '"terraform_version":"[^"]*' | cut -d'"' -f4)
    echo "   Version: $TERRAFORM_VERSION"
else
    fail "Terraform not installed"
fi

# Check Docker
if command -v docker >/dev/null 2>&1; then
    pass "Docker installed"
    if docker ps >/dev/null 2>&1; then
        pass "Docker daemon running"
    else
        warn "Docker daemon not running"
    fi
else
    fail "Docker not installed"
fi

# Check Terraform config
if [[ -f "$PROJECT_ROOT/terraform/terraform.tfvars" ]]; then
    pass "terraform.tfvars configured"
else
    warn "terraform.tfvars not created - copy from terraform.tfvars.example"
fi

echo ""
echo "=========================================="
echo "📊 Summary"
echo "=========================================="

if [[ -f "$PROJECT_ROOT/.env" ]] && \
   command -v aws >/dev/null 2>&1 && \
   aws sts get-caller-identity >/dev/null 2>&1 && \
   command -v terraform >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Ready for deployment!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Push secrets to SSM:"
    echo "   ./scripts/env_to_ssm.py --env-file .env --prefix /foundry/dev --format bash --overwrite > deploy/bootstrap_secrets.sh"
    echo "   chmod +x deploy/bootstrap_secrets.sh"
    echo "   ./deploy/bootstrap_secrets.sh"
    echo ""
    echo "2. Configure Terraform:"
    echo "   cd terraform"
    echo "   cp terraform.tfvars.example terraform.tfvars"
    echo "   nano terraform.tfvars"
    echo ""
    echo "3. Deploy infrastructure:"
    echo "   terraform init"
    echo "   terraform apply"
    echo ""
    echo "4. Deploy application:"
    echo "   cd .."
    echo "   ./deploy/deploy.sh"
else
    echo -e "${RED}❌ Prerequisites missing${NC}"
    echo ""
    echo "Required actions:"
    [[ ! -f "$PROJECT_ROOT/.env" ]] && echo "- Create .env file"
    ! command -v aws >/dev/null 2>&1 && echo "- Install AWS CLI"
    ! aws sts get-caller-identity >/dev/null 2>&1 && echo "- Configure AWS credentials"
    ! command -v terraform >/dev/null 2>&1 && echo "- Install Terraform"
fi

echo ""
echo "📚 Documentation:"
echo "- Quick Reference: DEPLOYMENT.md"
echo "- Full Guide: deploy/AWS_DEPLOYMENT_GUIDE.md"
echo ""
