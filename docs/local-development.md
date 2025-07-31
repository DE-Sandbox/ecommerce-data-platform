# Local Development with LocalStack (2025)

LocalStack has definitively won the local AWS development battle in 2025, offering comprehensive coverage of 90+ AWS services compared to limited alternatives. This guide covers setting up a complete local development environment that mirrors production AWS infrastructure.

## Why LocalStack in 2025

- **90+ AWS services** supported locally
- **Identical code** for local and production environments
- **85-95% cost reduction** compared to cloud development ($25/month vs $500-2000/month)
- **Faster development** with instant feedback loops
- **Complete data platform** development without cloud resources

## Installation and Setup

### LocalStack Installation

```bash
# Install LocalStack CLI
pip install localstack

# Or via Docker (recommended)
docker pull localstack/localstack:latest

# Install AWS CLI for LocalStack interaction
pip install awscli-local  # Provides 'awslocal' command
```

### Basic Configuration

```bash
# Environment variables
export LOCALSTACK_HOST=localhost.localstack.cloud
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
export AWS_ENDPOINT_URL=http://localhost:4566
```

## Docker Compose Configuration

### Complete Data Platform Stack

```yaml
# docker-compose.yml
version: '3.8'

services:
  # LocalStack - AWS services emulation
  localstack:
    image: localstack/localstack:latest
    container_name: localstack
    environment:
      # Core services for data engineering
      - SERVICES=s3,dynamodb,kinesis,glue,athena,lambda,iam,sts,cloudformation
      - DEBUG=1
      - DATA_DIR=/tmp/localstack/data
      - HOST_TMP_FOLDER=${TMPDIR:-/tmp}/localstack
      - DOCKER_HOST=unix:///var/run/docker.sock
      # Enable persistence
      - PERSISTENCE=1
      # Pro features (optional, requires license)
      - LOCALSTACK_API_KEY=${LOCALSTACK_API_KEY:-}
    ports:
      - "4566:4566"            # LocalStack Gateway
      - "4510-4559:4510-4559"  # External services port range
    volumes:
      - localstack_data:/tmp/localstack
      - /var/run/docker.sock:/var/run/docker.sock
    networks:
      - data-platform

  # PostgreSQL for OLTP workloads
  postgres:
    image: postgres:16-alpine
    container_name: postgres
    environment:
      POSTGRES_DB: ecommerce
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_INITDB_ARGS: "--data-checksums"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init_postgres.sql:/docker-entrypoint-initdb.d/01-init.sql
      - ./scripts/seed_data.sql:/docker-entrypoint-initdb.d/02-seed.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - data-platform

  # Redpanda (Kafka alternative) for streaming
  redpanda:
    image: redpandadata/redpanda:latest
    container_name: redpanda
    command:
      - redpanda start
      - --smp 1
      - --memory 1G
      - --overprovisioned
      - --node-id 0
      - --kafka-addr PLAINTEXT://0.0.0.0:29092,OUTSIDE://0.0.0.0:9092
      - --advertise-kafka-addr PLAINTEXT://redpanda:29092,OUTSIDE://localhost:9092
      - --pandaproxy-addr 0.0.0.0:8082
      - --advertise-pandaproxy-addr localhost:8082
    ports:
      - "9092:9092"   # Kafka
      - "8082:8082"   # HTTP Proxy
      - "9644:9644"   # Admin API
    volumes:
      - redpanda_data:/var/lib/redpanda/data
    networks:
      - data-platform

  # Redpanda Console for Kafka management
  redpanda-console:
    image: redpandadata/console:latest
    container_name: redpanda-console
    environment:
      KAFKA_BROKERS: redpanda:29092
    ports:
      - "8080:8080"
    depends_on:
      - redpanda
    networks:
      - data-platform

  # Dagster for orchestration
  dagster:
    build:
      context: .
      target: development
    container_name: dagster
    environment:
      - DAGSTER_POSTGRES_USER=postgres
      - DAGSTER_POSTGRES_PASSWORD=postgres
      - DAGSTER_POSTGRES_DB=dagster
      - DAGSTER_POSTGRES_HOSTNAME=postgres
      - AWS_ENDPOINT_URL=http://localstack:4566
      - AWS_ACCESS_KEY_ID=test
      - AWS_SECRET_ACCESS_KEY=test
      - AWS_DEFAULT_REGION=us-east-1
    ports:
      - "3000:3000"   # Dagster UI
      - "3001:3001"   # Dagster daemon
    volumes:
      - .:/app
      - dagster_home:/opt/dagster/dagster_home
    depends_on:
      postgres:
        condition: service_healthy
      localstack:
        condition: service_started
    networks:
      - data-platform

  # Jupyter for data exploration
  jupyter:
    build:
      context: .
      target: development
    container_name: jupyter
    command: uv run jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root
    environment:
      - AWS_ENDPOINT_URL=http://localstack:4566
      - AWS_ACCESS_KEY_ID=test
      - AWS_SECRET_ACCESS_KEY=test
    ports:
      - "8888:8888"
    volumes:
      - .:/app
      - jupyter_data:/home/jovyan/work
    networks:
      - data-platform

  # MinIO UI for S3 exploration (alternative to LocalStack UI)
  minio-ui:
    image: minio/minio:latest
    container_name: minio-ui
    command: server /data --console-address ":9001"
    environment:
      - MINIO_ACCESS_KEY=test
      - MINIO_SECRET_KEY=test
    ports:
      - "9000:9000"   # MinIO API
      - "9001:9001"   # MinIO Console
    volumes:
      - minio_data:/data
    networks:
      - data-platform

volumes:
  localstack_data:
  postgres_data:
  redpanda_data:
  dagster_home:
  jupyter_data:
  minio_data:

networks:
  data-platform:
    driver: bridge
```

## AWS Services Setup

### Initialize AWS Resources

```bash
# Create initialization script
cat > scripts/init_aws_resources.sh << 'EOF'
#!/bin/bash

# Wait for LocalStack to be ready
echo "Waiting for LocalStack to be ready..."
awslocal s3 ls 2>/dev/null
while [ $? -ne 0 ]; do
    sleep 2
    awslocal s3 ls 2>/dev/null
done

echo "Creating S3 buckets..."
awslocal s3 mb s3://data-lake
awslocal s3 mb s3://staging
awslocal s3 mb s3://processed
awslocal s3 mb s3://archive

echo "Creating DynamoDB tables..."
awslocal dynamodb create-table \
    --table-name user-sessions \
    --attribute-definitions \
        AttributeName=session_id,AttributeType=S \
    --key-schema \
        AttributeName=session_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST

echo "Creating Kinesis streams..."
awslocal kinesis create-stream \
    --stream-name user-events \
    --shard-count 2

awslocal kinesis create-stream \
    --stream-name order-events \
    --shard-count 2

echo "Creating Glue database..."
awslocal glue create-database \
    --database-input Name=ecommerce_db,Description="E-commerce data lake database"

echo "AWS resources initialized successfully!"
EOF

chmod +x scripts/init_aws_resources.sh
```

### Run Initialization

```bash
# Start LocalStack and initialize resources
docker-compose up -d localstack
sleep 10
./scripts/init_aws_resources.sh
```

## Development Workflow

### Daily Development Commands

```bash
# Start complete development environment
just up                     # Starts all services via docker-compose

# Check service health
docker-compose ps          # View all service statuses
docker-compose logs -f     # Follow all logs

# Individual service management
docker-compose up -d localstack postgres redpanda  # Start core services
docker-compose logs localstack                      # Check LocalStack logs
```

### Testing AWS Integration

```bash
# Test S3 connectivity
awslocal s3 ls
awslocal s3 cp test-file.txt s3://data-lake/

# Test DynamoDB
awslocal dynamodb list-tables
awslocal dynamodb scan --table-name user-sessions

# Test Kinesis
awslocal kinesis list-streams
awslocal kinesis put-record \
    --stream-name user-events \
    --data '{"event": "page_view", "user_id": 123}' \
    --partition-key user_123

# Test Glue
awslocal glue get-databases
```

## LocalStack Pro Features

### Advanced Features (with license)

```bash
# Cloud Pods - snapshot and share environments
localstack pods save my-dev-environment
localstack pods load my-dev-environment

# Lambda Hot Reloading
export LAMBDA_REMOTE_DOCKER=true

# Advanced IAM simulation
awslocal iam simulate-principal-policy \
    --policy-source-arn arn:aws:iam::000000000000:user/testuser \
    --action-names s3:GetObject \
    --resource-arns arn:aws:s3:::data-lake/*
```

## Integration with Infrastructure as Code

### Terraform with LocalStack

```bash
# Install tflocal wrapper
pip install terraform-local

# Use tflocal instead of terraform
tflocal init
tflocal plan
tflocal apply
```

### Terraform Configuration

```hcl
# terraform/main.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  # LocalStack configuration
  access_key                  = "test"
  secret_key                  = "test"
  region                     = "us-east-1"
  s3_use_path_style          = true
  skip_credentials_validation = true
  skip_metadata_api_check    = true
  skip_requesting_account_id  = true

  # LocalStack endpoints
  endpoints {
    apigateway     = "http://localhost:4566"
    cloudformation = "http://localhost:4566"
    cloudwatch     = "http://localhost:4566"
    dynamodb       = "http://localhost:4566"
    ec2            = "http://localhost:4566"
    elasticsearch  = "http://localhost:4566"
    firehose       = "http://localhost:4566"
    iam            = "http://localhost:4566"
    kinesis        = "http://localhost:4566"
    lambda         = "http://localhost:4566"
    rds            = "http://localhost:4566"
    redshift       = "http://localhost:4566"
    route53        = "http://localhost:4566"
    s3             = "http://localhost:4566"
    secretsmanager = "http://localhost:4566"
    ses            = "http://localhost:4566"
    sns            = "http://localhost:4566"
    sqs            = "http://localhost:4566"
    ssm            = "http://localhost:4566"
    stepfunctions  = "http://localhost:4566"
    sts            = "http://localhost:4566"
  }
}

# Example resources
resource "aws_s3_bucket" "data_lake" {
  bucket = "data-lake"
}

resource "aws_dynamodb_table" "user_sessions" {
  name           = "user-sessions"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "session_id"

  attribute {
    name = "session_id"
    type = "S"
  }
}
```

## Monitoring and Debugging

### LocalStack Dashboard

```bash
# Access LocalStack Web UI (Pro feature)
open http://localhost:4566/_localstack/health

# Check service status
curl http://localhost:4566/health
```

### Service Health Checks

```bash
# Comprehensive health check script
cat > scripts/health_check.sh << 'EOF'
#!/bin/bash

echo "=== LocalStack Health Check ==="
curl -s http://localhost:4566/health | jq '.'

echo -e "\n=== PostgreSQL Health Check ==="
docker exec postgres pg_isready -U postgres

echo -e "\n=== Redpanda Health Check ==="
curl -s http://localhost:8082/v3/clusters | jq '.'

echo -e "\n=== Dagster Health Check ==="
curl -s http://localhost:3000/graphql -d '{"query": "{ instance { info { dagsterVersion } } }"}' -H "Content-Type: application/json" | jq '.'

echo -e "\n=== S3 Buckets ==="
awslocal s3 ls

echo -e "\n=== DynamoDB Tables ==="
awslocal dynamodb list-tables

echo -e "\n=== Kinesis Streams ==="
awslocal kinesis list-streams
EOF

chmod +x scripts/health_check.sh
```

## Performance Optimization

### Resource Allocation

```yaml
# docker-compose.override.yml for development
services:
  localstack:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'

  postgres:
    environment:
      - POSTGRES_SHARED_BUFFERS=256MB
      - POSTGRES_EFFECTIVE_CACHE_SIZE=1GB
```

### Data Persistence

```bash
# Backup LocalStack data
docker exec localstack \
  tar -czf /tmp/localstack-backup.tar.gz /tmp/localstack/data

# Restore LocalStack data
docker exec localstack \
  tar -xzf /tmp/localstack-backup.tar.gz -C /
```

## Troubleshooting

### Common Issues

```bash
# LocalStack not starting
docker-compose logs localstack

# Port conflicts
netstat -tulpn | grep :4566
docker-compose down && docker-compose up -d

# AWS CLI not connecting
export AWS_ENDPOINT_URL=http://localhost:4566
awslocal s3 ls

# Clear LocalStack data
docker-compose down -v
docker volume rm $(docker volume ls -q | grep localstack)
```

### Reset Environment

```bash
# Complete reset
docker-compose down -v
docker system prune -f
docker-compose up -d
./scripts/init_aws_resources.sh
```

This LocalStack setup provides a complete local AWS development environment that mirrors production infrastructure while enabling fast, cost-effective development and testing of data engineering pipelines.