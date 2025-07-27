#!/bin/bash
# Terraform wrapper for LocalStack development

set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m'

# Configuration
TF_DIR="${TF_DIR:-terraform/environments/local}"
LOCALSTACK_URL="${AWS_ENDPOINT_URL:-http://localhost:4566}"

# Check if LocalStack is running
check_localstack() {
    if curl -s "${LOCALSTACK_URL}/_localstack/health" | grep -q "running"; then
        echo -e "${GREEN}✅ LocalStack is running${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  LocalStack is not running. Starting it now...${NC}"
        just up
        sleep 10
        return 0
    fi
}

# Main execution
main() {
    echo -e "${BLUE}🏗️  Terraform LocalStack Wrapper${NC}"
    echo "================================"

    # Check LocalStack
    check_localstack

    # Change to Terraform directory
    cd "$TF_DIR"

    # Export LocalStack configuration
    export AWS_ACCESS_KEY_ID=test
    export AWS_SECRET_ACCESS_KEY=test
    export AWS_REGION=${AWS_REGION:-us-east-1}
    export AWS_DEFAULT_REGION=${AWS_REGION:-us-east-1}

    # Run Terraform command
    case "${1:-help}" in
        init)
            echo -e "${GREEN}Initializing Terraform...${NC}"
            terraform init
            ;;
        plan)
            echo -e "${GREEN}Planning Terraform changes...${NC}"
            terraform plan
            ;;
        apply)
            echo -e "${GREEN}Applying Terraform changes...${NC}"
            terraform apply -auto-approve
            ;;
        destroy)
            echo -e "${YELLOW}Destroying Terraform resources...${NC}"
            terraform destroy -auto-approve
            ;;
        output)
            terraform output -json
            ;;
        *)
            echo "Usage: $0 {init|plan|apply|destroy|output}"
            exit 1
            ;;
    esac
}

main "$@"
