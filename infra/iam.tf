# ============================================
# IAM Roles & Policies
# ============================================
# IAM roles for ECS task execution (ECR pulls, CloudWatch logs)

# Trust policy: Allow ECS tasks to assume this role
data "aws_iam_policy_document" "ecs_task_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

# Execution role for ECS tasks (pulling images, writing logs)
resource "aws_iam_role" "ecs_task_execution" {
  name               = "${var.project_name}-ecs-task-exec"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume.json

  tags = {
    Name = "${var.project_name}-ecs-task-exec"
  }
}

# Attach AWS-managed ECS task execution policy
resource "aws_iam_role_policy_attachment" "ecs_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}
