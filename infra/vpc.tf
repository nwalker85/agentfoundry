# ============================================
# VPC & Networking
# ============================================
# VPC, subnets, internet gateway, and route tables

resource "aws_vpc" "foundry" {
  cidr_block           = "10.42.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

resource "aws_internet_gateway" "foundry" {
  vpc_id = aws_vpc.foundry.id

  tags = {
    Name = "${var.project_name}-igw"
  }
}

# ============================================
# Public Subnets (2 AZs for HA)
# ============================================

resource "aws_subnet" "public_a" {
  vpc_id                  = aws_vpc.foundry.id
  cidr_block              = "10.42.0.0/24"
  availability_zone       = "us-east-1a"
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-public-a"
  }
}

resource "aws_subnet" "public_b" {
  vpc_id                  = aws_vpc.foundry.id
  cidr_block              = "10.42.1.0/24"
  availability_zone       = "us-east-1b"
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-public-b"
  }
}

# ============================================
# Routing
# ============================================

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.foundry.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.foundry.id
  }

  tags = {
    Name = "${var.project_name}-public-rt"
  }
}

resource "aws_route_table_association" "public_a" {
  subnet_id      = aws_subnet.public_a.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public_b" {
  subnet_id      = aws_subnet.public_b.id
  route_table_id = aws_route_table.public.id
}
