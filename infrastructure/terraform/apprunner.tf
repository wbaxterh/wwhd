# AWS App Runner Service for W.W.H.D. Backend

resource "aws_apprunner_service" "backend" {
  service_name = "${local.name_prefix}-backend"

  source_configuration {
    authentication_configuration {
      access_role_arn = aws_iam_role.apprunner_service.arn
    }

    image_repository {
      image_identifier      = "${aws_ecr_repository.backend.repository_url}:latest"
      image_repository_type = "ECR"

      image_configuration {
        port = "8000"

        runtime_environment_variables = {
          APP_ENV                = var.environment
          LOG_LEVEL             = var.environment == "prod" ? "INFO" : "DEBUG"
          ALLOW_ORIGINS         = var.environment == "prod" ? "https://*.wwhd.ai" : "*"
          AWS_DEFAULT_REGION    = local.region
          S3_DOCUMENTS_BUCKET   = aws_s3_bucket.documents.bucket
        }

# Commented out for health check deployment - uncomment when we need secrets
        # runtime_environment_secrets = {
        #   JWT_SECRET         = aws_secretsmanager_secret.app_secrets["jwt_secret"].arn
        #   OPENAI_API_KEY     = aws_secretsmanager_secret.app_secrets["openai_api_key"].arn
        #   OPENROUTER_API_KEY = aws_secretsmanager_secret.app_secrets["openrouter_api_key"].arn
        #   QDRANT_API_KEY     = aws_secretsmanager_secret.app_secrets["qdrant_api_key"].arn
        #   DATABASE_URL       = aws_secretsmanager_secret.app_secrets["database_url"].arn
        # }

        start_command = "uvicorn main:app --host 0.0.0.0 --port 8000"
      }
    }

    auto_deployments_enabled = false  # We'll handle deployments via GitHub Actions
  }

  instance_configuration {
    cpu    = var.app_runner_config.cpu
    memory = var.app_runner_config.memory
    # No instance role needed for health check app
    # instance_role_arn = aws_iam_role.apprunner_instance.arn
  }

  auto_scaling_configuration_arn = aws_apprunner_auto_scaling_configuration_version.backend.arn

  health_check_configuration {
    healthy_threshold   = 1
    interval            = 10
    path                = "/health"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 5
  }

  tags = merge(var.common_tags, {
    Purpose = "Backend API service"
  })

  depends_on = [
    aws_iam_role_policy_attachment.apprunner_ecr,
    aws_iam_role_policy_attachment.apprunner_instance_policy
  ]
}

# Auto Scaling Configuration
resource "aws_apprunner_auto_scaling_configuration_version" "backend" {
  auto_scaling_configuration_name = "${local.name_prefix}-backend"

  max_concurrency = var.app_runner_config.max_concurrency
  max_size        = var.app_runner_config.max_size
  min_size        = var.app_runner_config.min_size

  tags = merge(var.common_tags, {
    Purpose = "Backend auto scaling"
  })
}

# VPC Connector (for future RDS connectivity)
resource "aws_apprunner_vpc_connector" "backend" {
  count = var.environment == "prod" ? 1 : 0

  vpc_connector_name = "${local.name_prefix}-vpc-connector"
  subnets           = []  # Will be populated when VPC is created
  security_groups   = []  # Will be populated when security groups are created

  tags = merge(var.common_tags, {
    Purpose = "VPC connectivity for App Runner"
  })
}

# Custom Domain Association (when domain is available)
resource "aws_apprunner_custom_domain_association" "backend" {
  count = var.domain_name != "" ? 1 : 0

  domain_name = "api.${var.domain_name}"
  service_arn = aws_apprunner_service.backend.arn

  depends_on = [aws_apprunner_service.backend]
}