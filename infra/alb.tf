# ============================================
# Application Load Balancer
# ============================================
# ALB, target groups, listeners, and routing rules

# Application Load Balancer
resource "aws_lb" "foundry" {
  name               = "${var.project_name}-alb"
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = [aws_subnet.public_a.id, aws_subnet.public_b.id]

  tags = {
    Name = "${var.project_name}-alb"
  }
}

# ============================================
# Target Groups
# ============================================

# UI Target Group (port 3000)
resource "aws_lb_target_group" "ui" {
  name        = "${var.project_name}-ui-tg"
  port        = 3000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.foundry.id
  target_type = "ip"

  health_check {
    path                = "/"
    healthy_threshold   = 3
    unhealthy_threshold = 3
    interval            = 30
    timeout             = 5
    matcher             = "200-399"
  }

  tags = {
    Name = "${var.project_name}-ui-tg"
  }
}

# API Target Group (port 8000)
resource "aws_lb_target_group" "api" {
  name        = "${var.project_name}-api-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.foundry.id
  target_type = "ip"

  health_check {
    path                = "/health"
    healthy_threshold   = 3
    unhealthy_threshold = 3
    interval            = 30
    timeout             = 5
    matcher             = "200-399"
  }

  tags = {
    Name = "${var.project_name}-api-tg"
  }
}

# ============================================
# Listeners
# ============================================

# HTTPS Listener - Default action forwards to UI
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.foundry.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = var.foundry_cert_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.ui.arn
  }
}

# HTTP Listener - Redirect to HTTPS
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.foundry.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

# ============================================
# Listener Rules
# ============================================

# Route /api/* to API target group
resource "aws_lb_listener_rule" "api_path" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 10

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }

  condition {
    path_pattern {
      values = ["/api/*"]
    }
  }
}
