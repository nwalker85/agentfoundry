# ============================================
# ECR Container Registries
# ============================================
# ECR repositories for all Agent Foundry container images

resource "aws_ecr_repository" "ui" {
  name = "agentfoundry-ui"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name    = "agentfoundry-ui"
    Service = "ui"
  }
}

resource "aws_ecr_repository" "backend" {
  name = "agentfoundry-backend"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name    = "agentfoundry-backend"
    Service = "api"
  }
}

resource "aws_ecr_repository" "compiler" {
  name = "agentfoundry-compiler"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name    = "agentfoundry-compiler"
    Service = "compiler"
  }
}

resource "aws_ecr_repository" "forge" {
  name = "agentfoundry-forge"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name    = "agentfoundry-forge"
    Service = "forge"
  }
}
