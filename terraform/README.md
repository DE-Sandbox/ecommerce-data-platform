# Infrastructure as Code

This directory contains Terraform configurations for the e-commerce data platform infrastructure.

## Directory Structure

```
terraform/
├── modules/              # Reusable Terraform modules
│   ├── s3_data_lake/    # S3 buckets for data lake
│   ├── dynamodb/        # DynamoDB tables
│   ├── kinesis/         # Kinesis data streams
│   ├── sqs/             # SQS queues
│   └── lambda/          # Lambda functions
├── environments/         # Environment-specific configurations
│   ├── local/           # LocalStack development
│   ├── dev/             # AWS development environment
│   └── prod/            # AWS production environment
└── versions.tf          # Provider version constraints
```

## Local Development with LocalStack

For local development, we use LocalStack to emulate AWS services:

```bash
# Initialize Terraform
just tf-init

# Plan changes
just tf-plan

# Apply infrastructure
just tf-apply

# Destroy infrastructure
just tf-destroy

# Full setup (start services + create infrastructure)
just infra-up

# Full teardown
just infra-down
```

## AWS Deployment

For real AWS environments:

```bash
# Development environment
cd terraform/environments/dev
aws-vault exec dev -- terraform init
aws-vault exec dev -- terraform plan
aws-vault exec dev -- terraform apply

# Production environment (requires approval)
cd terraform/environments/prod
aws-vault exec prod -- terraform init
aws-vault exec prod -- terraform plan
aws-vault exec prod -- terraform apply
```

## Module Usage

Each module is designed to be reusable across environments:

```hcl
module "data_lake" {
  source = "../../modules/s3_data_lake"

  project_name = var.project_name
  environment  = var.environment

  bucket_names = {
    raw       = "${var.project_name}-${var.environment}-raw"
    processed = "${var.project_name}-${var.environment}-processed"
    curated   = "${var.project_name}-${var.environment}-curated"
  }
}
```

## Security Best Practices

1. **State Management**:
   - Local: State stored locally (gitignored)
   - AWS: Use S3 backend with encryption and DynamoDB locking

2. **Secrets Management**:
   - Never hardcode secrets in Terraform
   - Use AWS Secrets Manager or Parameter Store
   - Reference secrets dynamically

3. **IAM Principles**:
   - Least privilege access
   - Use roles instead of users where possible
   - Enable MFA for production

## Cost Optimization

1. **Resource Tagging**: All resources tagged with:
   - Environment
   - Project
   - Owner
   - CostCenter

2. **Lifecycle Policies**:
   - S3: Transition to Glacier for old data
   - DynamoDB: Auto-scaling enabled
   - Lambda: Appropriate memory allocation

3. **Monitoring**:
   - CloudWatch alarms for cost anomalies
   - Budget alerts configured
