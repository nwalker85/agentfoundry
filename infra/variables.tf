# ============================================
# Terraform Variables
# ============================================
# All input variables for the Agent Foundry infrastructure

# Project name prefix for resource naming
variable "project_name" {
  description = "Prefix for naming AWS resources"
  type        = string
  default     = "agentfoundry"
}

# ACM Certificate ARN for HTTPS
variable "foundry_cert_arn" {
  description = "ACM certificate ARN for foundry.ravenhelm.ai"
  type        = string
}

# ============================================
# Container Image Tags
# ============================================

variable "ui_image_tag" {
  description = "Docker image tag for UI container"
  type        = string
  default     = "latest"
}

variable "backend_image_tag" {
  description = "Docker image tag for backend/API container"
  type        = string
  default     = "latest"
}

variable "compiler_image_tag" {
  description = "Docker image tag for compiler service container"
  type        = string
  default     = "latest"
}

variable "forge_image_tag" {
  description = "Docker image tag for forge service container"
  type        = string
  default     = "latest"
}
