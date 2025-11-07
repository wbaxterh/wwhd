#!/bin/bash
set -euo pipefail

# W.W.H.D. Infrastructure Setup Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
TERRAFORM_DIR="$PROJECT_DIR/infrastructure/terraform"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}INFO:${NC} $1"; }
log_success() { echo -e "${GREEN}SUCCESS:${NC} $1"; }
log_warning() { echo -e "${YELLOW}WARNING:${NC} $1"; }
log_error() { echo -e "${RED}ERROR:${NC} $1"; }

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI not found. Please install it first."
        exit 1
    fi

    # Check Terraform
    if ! command -v terraform &> /dev/null; then
        log_error "Terraform not found. Please install it first."
        exit 1
    fi

    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured. Run 'aws configure' first."
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# Initialize Terraform variables
setup_terraform_vars() {
    log_info "Setting up Terraform variables..."

    cd "$TERRAFORM_DIR"

    if [[ ! -f terraform.tfvars ]]; then
        cp terraform.tfvars.example terraform.tfvars
        log_warning "Created terraform.tfvars from example. Please review and update it."
        log_info "Edit $TERRAFORM_DIR/terraform.tfvars with your specific values"
        return 1
    fi

    log_success "Terraform variables configured"
}

# Initialize Terraform
init_terraform() {
    log_info "Initializing Terraform..."

    cd "$TERRAFORM_DIR"
    terraform init

    log_success "Terraform initialized"
}

# Plan infrastructure
plan_infrastructure() {
    log_info "Planning infrastructure..."

    cd "$TERRAFORM_DIR"
    terraform plan -out=tfplan

    log_success "Infrastructure plan created"
    log_info "Review the plan above. If it looks good, run: terraform apply tfplan"
}

# Apply infrastructure
apply_infrastructure() {
    log_info "Applying infrastructure..."

    cd "$TERRAFORM_DIR"

    if [[ ! -f tfplan ]]; then
        log_error "No terraform plan found. Run 'terraform plan -out=tfplan' first."
        exit 1
    fi

    terraform apply tfplan
    rm -f tfplan

    log_success "Infrastructure applied successfully!"
}

# Get outputs
get_outputs() {
    log_info "Getting infrastructure outputs..."

    cd "$TERRAFORM_DIR"

    echo ""
    echo "=== Infrastructure Outputs ==="
    terraform output -json | jq -r '
        "ECR Repository: " + .ecr_repository_url.value + "\n" +
        "App Runner URL: " + .apprunner_service_url.value + "\n" +
        "Frontend Bucket: " + .frontend_bucket_name.value + "\n" +
        "CloudFront URL: https://" + .cloudfront_domain_name.value + "\n" +
        "Website URL: " + .website_url.value
    '
    echo ""

    # Save outputs for GitHub Actions
    terraform output -json > "$PROJECT_DIR/.terraform-outputs.json"

    log_success "Outputs saved to .terraform-outputs.json"
}

# Setup secrets
setup_secrets() {
    log_info "Setting up secrets in AWS Secrets Manager..."

    cd "$TERRAFORM_DIR"

    # Get secret ARNs from Terraform output
    SECRETS=$(terraform output -json secrets_arns | jq -r 'to_entries[] | "\(.key):\(.value)"')

    echo ""
    echo "=== Required Secrets Setup ==="
    echo "Please set the following secrets in AWS Secrets Manager:"
    echo ""

    while IFS=: read -r name arn; do
        echo "Secret: $name"
        echo "ARN: $arn"
        echo "Command: aws secretsmanager put-secret-value --secret-id '$arn' --secret-string '{\"value\":\"YOUR_VALUE_HERE\"}'"
        echo ""
    done <<< "$SECRETS"

    log_warning "You must set these secrets before the application will work properly."
}

# Main execution
main() {
    echo "============================================="
    echo "W.W.H.D. Infrastructure Setup"
    echo "============================================="
    echo ""

    case "${1:-}" in
        "init")
            check_prerequisites
            setup_terraform_vars
            init_terraform
            ;;
        "plan")
            plan_infrastructure
            ;;
        "apply")
            apply_infrastructure
            get_outputs
            setup_secrets
            ;;
        "outputs")
            get_outputs
            ;;
        "secrets")
            setup_secrets
            ;;
        "all")
            check_prerequisites
            setup_terraform_vars || {
                log_error "Please update terraform.tfvars and run again"
                exit 1
            }
            init_terraform
            plan_infrastructure

            echo ""
            read -p "Apply infrastructure? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                apply_infrastructure
                get_outputs
                setup_secrets
            else
                log_info "Infrastructure not applied. Run './setup.sh apply' when ready."
            fi
            ;;
        *)
            echo "Usage: $0 {init|plan|apply|outputs|secrets|all}"
            echo ""
            echo "Commands:"
            echo "  init     - Initialize Terraform and check prerequisites"
            echo "  plan     - Create and review infrastructure plan"
            echo "  apply    - Apply infrastructure changes"
            echo "  outputs  - Display infrastructure outputs"
            echo "  secrets  - Show commands to set up secrets"
            echo "  all      - Run complete setup (init + plan + apply)"
            echo ""
            echo "Example: ./setup.sh all"
            exit 1
            ;;
    esac
}

main "$@"