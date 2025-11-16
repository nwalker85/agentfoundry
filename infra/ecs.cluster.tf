# ============================================
# ECS Cluster
# ============================================
# Fargate cluster for all Agent Foundry services

resource "aws_ecs_cluster" "foundry" {
  name = "${var.project_name}-cluster"

  tags = {
    Name = "${var.project_name}-cluster"
  }
}
