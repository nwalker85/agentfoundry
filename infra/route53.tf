# ============================================
# Route53 DNS Configuration
# ============================================
# Hosted zone and DNS records for ravenhelm.ai

# Hosted Zone for ravenhelm.ai
resource "aws_route53_zone" "ravenhelm_ai" {
  name    = "ravenhelm.ai"
  comment = "Managed by Terraform - Agent Foundry"

  tags = {
    Name    = "ravenhelm.ai"
    Project = var.project_name
  }
}

# A Record (Alias) for foundry.ravenhelm.ai → ALB
resource "aws_route53_record" "foundry_alias" {
  zone_id = aws_route53_zone.ravenhelm_ai.zone_id
  name    = "foundry.ravenhelm.ai"
  type    = "A"

  alias {
    name                   = aws_lb.foundry.dns_name
    zone_id                = aws_lb.foundry.zone_id
    evaluate_target_health = false
  }
}
