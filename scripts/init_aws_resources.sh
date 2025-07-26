#!/bin/bash
# Initialize LocalStack AWS resources for development

set -euo pipefail

echo "=== Initializing LocalStack AWS Resources ==="

# Configuration
ENDPOINT_URL=${AWS_ENDPOINT_URL:-http://localhost:4566}

# Helper function for AWS commands
awslocal() {
    aws --endpoint-url="$ENDPOINT_URL" "$@"
}

# Wait for LocalStack
echo "Waiting for LocalStack..."
for i in {1..30}; do
    if awslocal s3 ls >/dev/null 2>&1; then
        echo "✓ LocalStack is ready"
        break
    fi
    echo -n "."
    sleep 2
done

echo ""
echo "Creating S3 buckets..."
for bucket in data-lake-raw data-lake-processed data-staging logs; do
    awslocal s3 mb "s3://$bucket" 2>/dev/null || echo "  $bucket already exists"
done

echo ""
echo "Creating DynamoDB tables..."
awslocal dynamodb create-table \
    --table-name user-sessions \
    --attribute-definitions AttributeName=session_id,AttributeType=S \
    --key-schema AttributeName=session_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    2>/dev/null || echo "  user-sessions already exists"

awslocal dynamodb create-table \
    --table-name product-catalog \
    --attribute-definitions AttributeName=product_id,AttributeType=S \
    --key-schema AttributeName=product_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    2>/dev/null || echo "  product-catalog already exists"

echo ""
echo "Creating Kinesis streams..."
awslocal kinesis create-stream \
    --stream-name order-events \
    --shard-count 1 \
    2>/dev/null || echo "  order-events already exists"

awslocal kinesis create-stream \
    --stream-name user-activity \
    --shard-count 1 \
    2>/dev/null || echo "  user-activity already exists"

echo ""
echo "Creating SQS queues..."
awslocal sqs create-queue --queue-name order-processing 2>/dev/null || echo "  order-processing already exists"
awslocal sqs create-queue --queue-name notifications 2>/dev/null || echo "  notifications already exists"

echo ""
echo "=== LocalStack Resources Ready ==="
echo ""
echo "S3 Buckets:"
awslocal s3 ls | awk '{print "  - " $3}'
echo ""
echo "DynamoDB Tables:"
awslocal dynamodb list-tables --query 'TableNames[]' --output text | tr '\t' '\n' | awk '{print "  - " $1}'
echo ""
echo "Kinesis Streams:"
awslocal kinesis list-streams --query 'StreamNames[]' --output text | tr '\t' '\n' | awk '{print "  - " $1}'
echo ""
echo "✓ All resources initialized!"
