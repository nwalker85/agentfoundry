# ============================================
# Terraform Outputs
# ============================================
# Output values for reference and debugging

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.foundry.dns_name
}

output "foundry_url" {
  description = "Public URL for Agent Foundry application"
  value       = "https://foundry.ravenhelm.ai"
}

output "ecr_ui_repo" {
  description = "ECR repository URL for UI images"
  value       = aws_ecr_repository.ui.repository_url
}

output "ecr_backend_repo" {
  description = "ECR repository URL for backend/API images"
  value       = aws_ecr_repository.backend.repository_url
}

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.foundry.id
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.foundry.name
}
