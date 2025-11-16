# ============================================
# ECS Services & Task Definitions
# ============================================
# Fargate services and task definitions for UI and API

# ============================================
# ECS Services
# ============================================

# UI Service
resource "aws_ecs_service" "ui" {
  name            = "${var.project_name}-ui-svc"
  cluster         = aws_ecs_cluster.foundry.id
  task_definition = aws_ecs_task_definition.ui.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = [aws_subnet.public_a.id, aws_subnet.public_b.id]
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.ui.arn
    container_name   = "ui"
    container_port   = 3000
  }

  depends_on = [
    aws_lb_listener.https,
    aws_iam_role.ecs_task_execution
  ]

  lifecycle {
    ignore_changes = [task_definition]
  }
}

# API Service
resource "aws_ecs_service" "api" {
  name            = "${var.project_name}-api-svc"
  cluster         = aws_ecs_cluster.foundry.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = [aws_subnet.public_a.id, aws_subnet.public_b.id]
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = 8000
  }

  depends_on = [
    aws_lb_listener.https,
    aws_iam_role.ecs_task_execution
  ]

  lifecycle {
    ignore_changes = [task_definition]
  }
}

# ============================================
# Task Definitions
# ============================================

# UI Task Definition
resource "aws_ecs_task_definition" "ui" {
  family                   = "${var.project_name}-ui-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn

  container_definitions = jsonencode([
    {
      name      = "ui"
      image     = "${aws_ecr_repository.ui.repository_url}:${var.ui_image_tag}"
      essential = true
      portMappings = [
        {
          containerPort = 3000
          hostPort      = 3000
          protocol      = "tcp"
        }
      ]
      environment = [
        {
          name  = "NEXT_PUBLIC_API_URL"
          value = "https://foundry.ravenhelm.ai/api"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/${var.project_name}-ui"
          "awslogs-region"        = "us-east-1"
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])
}

# API Task Definition
resource "aws_ecs_task_definition" "api" {
  family                   = "${var.project_name}-api-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn

  container_definitions = jsonencode([
    {
      name      = "api"
      image     = "${aws_ecr_repository.backend.repository_url}:${var.backend_image_tag}"
      essential = true
      portMappings = [
        {
          containerPort = 8000
          hostPort      = 8000
          protocol      = "tcp"
        }
      ]
      environment = [
        { name = "PORT", value = "8000" }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/${var.project_name}-api"
          "awslogs-region"        = "us-east-1"
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])
}
