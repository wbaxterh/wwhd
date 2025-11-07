# Variables for W.W.H.D. Infrastructure

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "wwhd"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

variable "domain_name" {
  description = "Domain name for the application (optional)"
  type        = string
  default     = ""
}

# App Runner Configuration
variable "app_runner_config" {
  description = "App Runner service configuration"
  type = object({
    cpu                = string
    memory             = string
    max_concurrency    = number
    max_size          = number
    min_size          = number
  })
  default = {
    cpu             = "1 vCPU"
    memory          = "2 GB"
    max_concurrency = 100
    max_size        = 10
    min_size        = 1
  }
}

# S3 Configuration
variable "s3_buckets" {
  description = "S3 bucket names"
  type = object({
    frontend  = string
    documents = string
  })
  default = {
    frontend  = ""  # Will be auto-generated if empty
    documents = ""  # Will be auto-generated if empty
  }
}

# Secrets
variable "secrets" {
  description = "Secret names and descriptions"
  type = map(object({
    description = string
    type        = string
  }))
  default = {
    jwt_secret = {
      description = "JWT signing secret"
      type        = "string"
    }
    openai_api_key = {
      description = "OpenAI API key for chat and embeddings"
      type        = "string"
    }
    openrouter_api_key = {
      description = "OpenRouter API key as OpenAI alternative"
      type        = "string"
    }
    qdrant_api_key = {
      description = "Qdrant vector database API key"
      type        = "string"
    }
    database_url = {
      description = "Database connection URL"
      type        = "string"
    }
  }
}

# Tags
variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}