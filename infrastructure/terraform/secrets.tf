# AWS Secrets Manager for W.W.H.D.

# Create secrets for all required configuration
resource "aws_secretsmanager_secret" "app_secrets" {
  for_each = var.secrets

  name        = "${local.name_prefix}/${each.key}"
  description = each.value.description

  recovery_window_in_days = var.environment == "prod" ? 30 : 0

  tags = merge(var.common_tags, {
    SecretType = each.value.type
  })
}

# Placeholder secret values (will need to be updated manually or via CLI)
resource "aws_secretsmanager_secret_version" "app_secrets" {
  for_each = var.secrets

  secret_id = aws_secretsmanager_secret.app_secrets[each.key].id
  secret_string = jsonencode({
    value = "PLACEHOLDER_${upper(each.key)}"
  })

  lifecycle {
    ignore_changes = [secret_string]
  }
}

# Database URL secret (for future PostgreSQL migration)
resource "aws_secretsmanager_secret" "database_config" {
  name        = "${local.name_prefix}/database-config"
  description = "Database connection configuration"

  recovery_window_in_days = var.environment == "prod" ? 30 : 0

  tags = merge(var.common_tags, {
    SecretType = "database"
  })
}

resource "aws_secretsmanager_secret_version" "database_config" {
  secret_id = aws_secretsmanager_secret.database_config.id
  secret_string = jsonencode({
    engine   = "sqlite"
    host     = ""
    port     = ""
    database = "/app/data/app.db"
    username = ""
    password = ""
    url      = "sqlite:///./data/app.db"
  })

  lifecycle {
    ignore_changes = [secret_string]
  }
}

# Output secret ARNs for reference
locals {
  secret_arns = {
    for name, secret in aws_secretsmanager_secret.app_secrets : name => secret.arn
  }
}