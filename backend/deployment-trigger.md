# Deployment Trigger

This file is used to trigger backend deployments when needed.

**Last Update**: 2025-11-10 - Updated to pick up refreshed OPENAI_API_KEY from GitHub Secrets

The W.W.H.D. backend is deployed via GitHub Actions to AWS ECS Fargate.
Environment variables including API keys are injected from GitHub Secrets during deployment.