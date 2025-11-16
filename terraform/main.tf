terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Variables
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.small"
}

variable "domain" {
  description = "Domain name for the platform"
  type        = string
  default     = "foundry.ravenhelm.dev"
}

variable "ssh_key_name" {
  description = "Name of existing SSH key pair for EC2 access"
  type        = string
}

# Data sources
data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# IAM Role for EC2 Instance
resource "aws_iam_role" "foundry_ec2" {
  name = "foundry-ec2-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })

  tags = {
    Name        = "foundry-ec2-role"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# IAM Policy for SSM Parameter Access
resource "aws_iam_role_policy" "ssm_access" {
  name = "foundry-ssm-access"
  role = aws_iam_role.foundry_ec2.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters",
          "ssm:GetParametersByPath"
        ]
        Resource = "arn:aws:ssm:${var.aws_region}:*:parameter/foundry/${var.environment}/*"
      }
    ]
  })
}

# IAM Instance Profile
resource "aws_iam_instance_profile" "foundry" {
  name = "foundry-ec2-profile-${var.environment}"
  role = aws_iam_role.foundry_ec2.name
}

# Security Group
resource "aws_security_group" "foundry" {
  name        = "foundry-sg-${var.environment}"
  description = "Security group for Agent Foundry platform"

  # SSH
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "SSH access"
  }

  # HTTP
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP"
  }

  # HTTPS
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS"
  }

  # LiveKit HTTP/WebSocket
  ingress {
    from_port   = 7880
    to_port     = 7880
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "LiveKit HTTP/WebSocket"
  }

  # LiveKit RTC
  ingress {
    from_port   = 7881
    to_port     = 7881
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "LiveKit RTC TCP"
  }

  # LiveKit WebRTC UDP
  ingress {
    from_port   = 50000
    to_port     = 60000
    protocol    = "udp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "LiveKit WebRTC UDP"
  }

  # Outbound - Allow all
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound"
  }

  tags = {
    Name        = "foundry-security-group"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# Elastic IP
resource "aws_eip" "foundry" {
  domain = "vpc"

  tags = {
    Name        = "foundry-eip"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# EC2 Instance
resource "aws_instance" "foundry" {
  ami                    = data.aws_ami.amazon_linux_2023.id
  instance_type          = var.instance_type
  key_name               = var.ssh_key_name
  vpc_security_group_ids = [aws_security_group.foundry.id]
  iam_instance_profile   = aws_iam_instance_profile.foundry.name

  root_block_device {
    volume_size = 30
    volume_type = "gp3"
  }

  user_data = templatefile("${path.module}/user_data.sh", {
    environment = var.environment
    domain      = var.domain
  })

  tags = {
    Name        = "foundry-platform-${var.environment}"
    Environment = var.environment
    ManagedBy   = "terraform"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Associate Elastic IP
resource "aws_eip_association" "foundry" {
  instance_id   = aws_instance.foundry.id
  allocation_id = aws_eip.foundry.id
}

# Outputs
output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.foundry.id
}

output "instance_public_ip" {
  description = "Public IP address"
  value       = aws_eip.foundry.public_ip
}

output "instance_public_dns" {
  description = "Public DNS name"
  value       = aws_instance.foundry.public_dns
}

output "ssh_connection" {
  description = "SSH connection command"
  value       = "ssh -i ~/.ssh/${var.ssh_key_name}.pem ec2-user@${aws_eip.foundry.public_ip}"
}

output "next_steps" {
  description = "Next steps after deployment"
  value       = <<-EOT
    ✅ Infrastructure deployed successfully!
    
    Next steps:
    1. Update DNS: Point ${var.domain} → ${aws_eip.foundry.public_ip}
    2. SSH to instance: ssh -i ~/.ssh/${var.ssh_key_name}.pem ec2-user@${aws_eip.foundry.public_ip}
    3. Check logs: docker-compose logs -f
    4. Access platform: https://${var.domain}
  EOT
}
