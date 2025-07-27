#!/bin/bash
# Source this file to set up LocalStack environment
# Usage: source scripts/localstack-env.sh

echo "🚀 Setting up LocalStack environment..."

# Load .env.local if it exists
if [ -f .env.local ]; then
    set -a  # automatically export all variables
    source .env.local
    set +a  # stop automatically exporting
    echo "✅ Loaded environment from .env.local"
else
    echo "⚠️  Warning: .env.local not found"
    # Set defaults
    export AWS_ACCESS_KEY_ID=test
    export AWS_SECRET_ACCESS_KEY=test
    export AWS_ENDPOINT_URL=http://localhost:4566
    export AWS_REGION=us-east-1
    export AWS_DEFAULT_REGION=us-east-1
fi

# Create an alias for aws-local
alias awslocal='aws --endpoint-url=$AWS_ENDPOINT_URL'

echo "✅ LocalStack environment ready!"
echo ""
echo "You can now use:"
echo "  - awslocal s3 ls"
echo "  - awslocal dynamodb list-tables"
echo "  - etc."
echo ""
echo "Or use 'just aws-local <command>' from the project root"
