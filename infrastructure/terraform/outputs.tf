# Outputs for W.W.H.D. Infrastructure

# ECR Repository
output "ecr_repository_url" {
  description = "ECR repository URL for backend images"
  value       = aws_ecr_repository.backend.repository_url
}

# App Runner Service
output "apprunner_service_arn" {
  description = "App Runner service ARN"
  value       = aws_apprunner_service.backend.arn
}

output "apprunner_service_url" {
  description = "App Runner service URL"
  value       = "https://${aws_apprunner_service.backend.service_url}"
}

# S3 Buckets
output "frontend_bucket_name" {
  description = "Frontend S3 bucket name"
  value       = aws_s3_bucket.frontend.bucket
}

output "documents_bucket_name" {
  description = "Documents S3 bucket name"
  value       = aws_s3_bucket.documents.bucket
}

output "frontend_bucket_website_endpoint" {
  description = "Frontend S3 bucket website endpoint"
  value       = aws_s3_bucket_website_configuration.frontend.website_endpoint
}

# CloudFront
output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = aws_cloudfront_distribution.frontend.id
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.frontend.domain_name
}

# Domain and DNS
output "website_url" {
  description = "Primary website URL"
  value       = var.domain_name != "" ? "https://${var.domain_name}" : "https://${aws_cloudfront_distribution.frontend.domain_name}"
}

output "api_url" {
  description = "API endpoint URL"
  value       = var.domain_name != "" ? "https://api.${var.domain_name}" : "https://${aws_apprunner_service.backend.service_url}"
}

# Route53
output "nameservers" {
  description = "Route53 nameservers (if using custom domain)"
  value       = var.domain_name != "" ? aws_route53_zone.main[0].name_servers : []
}

# Secrets Manager
output "secrets_arns" {
  description = "ARNs of all created secrets"
  value       = local.secret_arns
  sensitive   = true
}

# IAM Roles
output "github_actions_role_arn" {
  description = "IAM role ARN for GitHub Actions"
  value       = aws_iam_role.github_actions.arn
}

output "apprunner_instance_role_arn" {
  description = "IAM role ARN for App Runner instance"
  value       = aws_iam_role.apprunner_instance.arn
}

# Environment Configuration
output "environment_variables" {
  description = "Environment variables for application deployment"
  value = {
    ECR_REPOSITORY        = aws_ecr_repository.backend.repository_url
    APP_RUNNER_ARN        = aws_apprunner_service.backend.arn
    S3_FRONTEND_BUCKET    = aws_s3_bucket.frontend.bucket
    S3_DOCUMENTS_BUCKET   = aws_s3_bucket.documents.bucket
    CLOUDFRONT_DISTRIBUTION_ID = aws_cloudfront_distribution.frontend.id
    AWS_REGION           = local.region
    AWS_ACCOUNT_ID       = local.account_id
  }
}

# GitHub Actions Environment Variables
output "github_actions_vars" {
  description = "Variables to set in GitHub Actions environment"
  value = {
    AWS_REGION                 = local.region
    AWS_ROLE_ARN              = aws_iam_role.github_actions.arn
    ECR_REPOSITORY            = aws_ecr_repository.backend.repository_url
    APP_RUNNER_ARN            = aws_apprunner_service.backend.arn
    S3_FRONTEND_BUCKET        = aws_s3_bucket.frontend.bucket
    CLOUDFRONT_DISTRIBUTION_ID = aws_cloudfront_distribution.frontend.id
  }
}

# Development URLs
output "development_urls" {
  description = "URLs for development and testing"
  value = {
    frontend_s3     = "http://${aws_s3_bucket_website_configuration.frontend.website_endpoint}"
    frontend_cdn    = "https://${aws_cloudfront_distribution.frontend.domain_name}"
    api_apprunner   = "https://${aws_apprunner_service.backend.service_url}"
    website         = var.domain_name != "" ? "https://${var.domain_name}" : "https://${aws_cloudfront_distribution.frontend.domain_name}"
  }
}