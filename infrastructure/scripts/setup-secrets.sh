#!/bin/bash
set -euo pipefail

# W.W.H.D. Secrets Setup Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="$(dirname "$SCRIPT_DIR")/terraform"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}INFO:${NC} $1"; }
log_success() { echo -e "${GREEN}SUCCESS:${NC} $1"; }
log_warning() { echo -e "${YELLOW}WARNING:${NC} $1"; }
log_error() { echo -e "${RED}ERROR:${NC} $1"; }

# Generate JWT secret
generate_jwt_secret() {
    openssl rand -base64 64 | tr -d '\n'
}

# Set secret value
set_secret() {
    local secret_arn="$1"
    local secret_value="$2"
    local secret_name="$3"

    log_info "Setting secret: $secret_name"

    aws secretsmanager put-secret-value \
        --secret-id "$secret_arn" \
        --secret-string "{\"value\":\"$secret_value\"}" \
        --output text --query 'VersionId' > /dev/null

    log_success "Secret $secret_name updated successfully"
}

# Interactive secret setup
interactive_setup() {
    echo "============================================="
    echo "W.W.H.D. Secrets Configuration"
    echo "============================================="
    echo ""

    # Check if terraform outputs exist
    if [[ ! -f "$TERRAFORM_DIR/terraform.tfstate" ]]; then
        log_error "Terraform state not found. Please run infrastructure setup first."
        exit 1
    fi

    # Get secret ARNs from Terraform
    cd "$TERRAFORM_DIR"
    SECRETS_JSON=$(terraform output -json secrets_arns 2>/dev/null || echo "{}")

    if [[ "$SECRETS_JSON" == "{}" ]]; then
        log_error "No secrets found in Terraform state. Please apply infrastructure first."
        exit 1
    fi

    # JWT Secret
    JWT_ARN=$(echo "$SECRETS_JSON" | jq -r '.jwt_secret // empty')
    if [[ -n "$JWT_ARN" ]]; then
        JWT_SECRET=$(generate_jwt_secret)
        set_secret "$JWT_ARN" "$JWT_SECRET" "JWT Secret"
    fi

    # OpenAI API Key
    OPENAI_ARN=$(echo "$SECRETS_JSON" | jq -r '.openai_api_key // empty')
    if [[ -n "$OPENAI_ARN" ]]; then
        echo ""
        echo "Please enter your OpenAI API key:"
        echo "(Get it from: https://platform.openai.com/api-keys)"
        read -s -p "OpenAI API Key: " OPENAI_KEY
        echo ""

        if [[ -n "$OPENAI_KEY" ]]; then
            set_secret "$OPENAI_ARN" "$OPENAI_KEY" "OpenAI API Key"
        else
            log_warning "Skipping OpenAI API Key (empty input)"
        fi
    fi

    # OpenRouter API Key
    OPENROUTER_ARN=$(echo "$SECRETS_JSON" | jq -r '.openrouter_api_key // empty')
    if [[ -n "$OPENROUTER_ARN" ]]; then
        echo ""
        echo "Please enter your OpenRouter API key (optional):"
        echo "(Get it from: https://openrouter.ai/keys)"
        read -s -p "OpenRouter API Key (or press Enter to skip): " OPENROUTER_KEY
        echo ""

        if [[ -n "$OPENROUTER_KEY" ]]; then
            set_secret "$OPENROUTER_ARN" "$OPENROUTER_KEY" "OpenRouter API Key"
        else
            log_warning "Skipping OpenRouter API Key"
        fi
    fi

    # Qdrant API Key
    QDRANT_ARN=$(echo "$SECRETS_JSON" | jq -r '.qdrant_api_key // empty')
    if [[ -n "$QDRANT_ARN" ]]; then
        echo ""
        echo "Please enter your Qdrant API key:"
        echo "(Get it from: https://cloud.qdrant.io/)"
        read -s -p "Qdrant API Key: " QDRANT_KEY
        echo ""

        if [[ -n "$QDRANT_KEY" ]]; then
            set_secret "$QDRANT_ARN" "$QDRANT_KEY" "Qdrant API Key"
        else
            log_warning "Skipping Qdrant API Key (empty input)"
        fi
    fi

    # Database URL
    DATABASE_ARN=$(echo "$SECRETS_JSON" | jq -r '.database_url // empty')
    if [[ -n "$DATABASE_ARN" ]]; then
        DATABASE_URL="sqlite:///./data/app.db"
        set_secret "$DATABASE_ARN" "$DATABASE_URL" "Database URL"
    fi

    echo ""
    log_success "Secrets configuration completed!"
    echo ""
    echo "Next steps:"
    echo "1. Set up Qdrant Cloud instance"
    echo "2. Build and deploy the application"
}

# Verify secrets
verify_secrets() {
    log_info "Verifying secrets..."

    cd "$TERRAFORM_DIR"
    SECRETS_JSON=$(terraform output -json secrets_arns 2>/dev/null || echo "{}")

    if [[ "$SECRETS_JSON" == "{}" ]]; then
        log_error "No secrets found"
        return 1
    fi

    local all_good=true

    echo "$SECRETS_JSON" | jq -r 'to_entries[]' | while read -r entry; do
        local name=$(echo "$entry" | jq -r '.key')
        local arn=$(echo "$entry" | jq -r '.value')

        if aws secretsmanager get-secret-value --secret-id "$arn" --query 'SecretString' --output text | grep -q "PLACEHOLDER"; then
            log_warning "Secret $name still has placeholder value"
            all_good=false
        else
            log_success "Secret $name is configured"
        fi
    done

    if [[ "$all_good" == "true" ]]; then
        log_success "All secrets are properly configured"
    else
        log_warning "Some secrets need configuration"
    fi
}

# Main execution
main() {
    case "${1:-interactive}" in
        "interactive"|"setup")
            interactive_setup
            ;;
        "verify")
            verify_secrets
            ;;
        "help"|"-h"|"--help")
            echo "Usage: $0 [setup|verify|help]"
            echo ""
            echo "Commands:"
            echo "  setup     - Interactive setup of all secrets"
            echo "  verify    - Verify that secrets are configured"
            echo "  help      - Show this help message"
            echo ""
            ;;
        *)
            log_error "Unknown command: $1"
            echo "Run '$0 help' for usage information"
            exit 1
            ;;
    esac
}

main "$@"