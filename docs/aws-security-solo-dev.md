# AWS Security Best Practices for Solo Developer

## Overview

This guide provides practical AWS security practices optimized for a solo developer, balancing security with simplicity and maintainability.

## Core Principles

1. **Never commit credentials** - Use aws-vault or environment variables
2. **Principle of least privilege** - Only grant permissions you actually need
3. **Use MFA** - Enable on your AWS root and IAM accounts
4. **Regular audits** - Review permissions and resources monthly

## Initial AWS Account Setup

### 1. Secure Root Account
```bash
# Root account should ONLY be used for:
# - Initial IAM user creation
# - Billing management
# - Account closure

# Enable MFA on root account immediately
# Store root credentials in password manager
# Never use root for daily operations
```

### 2. Create IAM Admin User
```bash
# Create admin user for daily operations
aws iam create-user --user-name admin
aws iam attach-user-policy --user-name admin --policy-arn arn:aws:iam::aws:policy/AdministratorAccess
aws iam create-access-key --user-name admin

# Enable MFA on admin user
# Use this for aws-vault setup
```

### 3. Create Development IAM User
```bash
# Create limited dev user for daily coding
aws iam create-user --user-name dev
aws iam create-access-key --user-name dev

# Attach custom policy (see below)
```

## AWS Vault Configuration

### Installation
```bash
# macOS
brew install aws-vault

# Linux
wget https://github.com/99designs/aws-vault/releases/latest/download/aws-vault-linux-amd64
chmod +x aws-vault-linux-amd64
sudo mv aws-vault-linux-amd64 /usr/local/bin/aws-vault
```

### Setup Profiles
```bash
# Add admin profile (use sparingly)
aws-vault add admin
# Enter Access Key ID and Secret Access Key when prompted

# Add dev profile (daily use)
aws-vault add dev
# Enter Access Key ID and Secret Access Key when prompted
```

### Configure MFA
```bash
# Edit ~/.aws/config
[profile admin]
mfa_serial = arn:aws:iam::123456789012:mfa/admin
region = us-east-1

[profile dev]
mfa_serial = arn:aws:iam::123456789012:mfa/dev
region = us-east-1
```

### Daily Usage
```bash
# Execute commands with temporary credentials
aws-vault exec dev -- aws s3 ls

# Start a shell with credentials
aws-vault exec dev -- $SHELL

# Use with Terraform
aws-vault exec dev -- terraform apply

# Use with Python scripts
aws-vault exec dev -- python my_script.py
```

## IAM Policies for Solo Dev

### Development Policy
Create `dev-policy.json`:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "S3Development",
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket",
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": [
                "arn:aws:s3:::ecommerce-*/*",
                "arn:aws:s3:::ecommerce-*"
            ]
        },
        {
            "Sid": "DynamoDBDevelopment",
            "Effect": "Allow",
            "Action": [
                "dynamodb:*"
            ],
            "Resource": [
                "arn:aws:dynamodb:*:*:table/ecommerce-*"
            ]
        },
        {
            "Sid": "LambdaDevelopment",
            "Effect": "Allow",
            "Action": [
                "lambda:*"
            ],
            "Resource": [
                "arn:aws:lambda:*:*:function:ecommerce-*"
            ]
        },
        {
            "Sid": "CloudWatchLogs",
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "logs:DescribeLogStreams"
            ],
            "Resource": "*"
        },
        {
            "Sid": "EC2ReadOnly",
            "Effect": "Allow",
            "Action": [
                "ec2:Describe*"
            ],
            "Resource": "*"
        }
    ]
}
```

Apply policy:
```bash
aws iam create-policy --policy-name dev-policy --policy-document file://dev-policy.json
aws iam attach-user-policy --user-name dev --policy-arn arn:aws:iam::123456789012:policy/dev-policy
```

## Cost Control

### 1. Set Budget Alerts
```bash
# Create $50/month budget alert
aws budgets create-budget --account-id 123456789012 --budget file://budget.json

# budget.json
{
    "BudgetName": "monthly-dev-budget",
    "BudgetLimit": {
        "Amount": "50",
        "Unit": "USD"
    },
    "TimeUnit": "MONTHLY",
    "BudgetType": "COST"
}
```

### 2. Use Resource Tags
```bash
# Tag all resources for cost tracking
aws s3api put-bucket-tagging --bucket my-bucket --tagging 'TagSet=[{Key=Project,Value=ecommerce},{Key=Environment,Value=dev}]'
```

### 3. Auto-shutdown for Development Resources
```python
# Lambda function to stop dev resources after hours
import boto3
from datetime import datetime

def lambda_handler(event, context):
    ec2 = boto3.client('ec2')
    
    # Stop all instances tagged as dev
    response = ec2.describe_instances(
        Filters=[
            {'Name': 'tag:Environment', 'Values': ['dev']},
            {'Name': 'instance-state-name', 'Values': ['running']}
        ]
    )
    
    instance_ids = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_ids.append(instance['InstanceId'])
    
    if instance_ids:
        ec2.stop_instances(InstanceIds=instance_ids)
        print(f"Stopped instances: {instance_ids}")
```

## Security Checklist

### Daily
- [ ] Use aws-vault for all AWS operations
- [ ] Never hardcode credentials in code
- [ ] Use environment variables from .env.local

### Weekly
- [ ] Review CloudTrail logs for unusual activity
- [ ] Check AWS Cost Explorer for anomalies
- [ ] Run security scan: `just security`

### Monthly
- [ ] Rotate access keys
- [ ] Review and remove unused resources
- [ ] Update dependencies: `just update`
- [ ] Review IAM permissions

### Quarterly
- [ ] Full security audit
- [ ] Review and update backup strategy
- [ ] Test disaster recovery procedures

## Environment Variables

### Development (.env.local)
```bash
# LocalStack for local development
AWS_PROFILE=localstack
AWS_ENDPOINT_URL=http://localhost:4566

# Never put real credentials here!
```

### Production
```bash
# Use aws-vault
aws-vault exec personal -- just deploy
```

## Git Security

### Pre-commit Checks
The project includes pre-push hooks that check for:
- AWS credentials in code
- Large files
- Security vulnerabilities
- Proper commit message format

### Secrets Management
```bash
# Use AWS Secrets Manager for application secrets
aws secretsmanager create-secret --name ecommerce/db-password --secret-string "your-password"

# Access in code
import boto3
client = boto3.client('secretsmanager')
response = client.get_secret_value(SecretId='ecommerce/db-password')
```

## Incident Response

### If Credentials Are Exposed
1. **Immediately deactivate** the exposed keys in AWS Console
2. **Create new keys** for the affected user
3. **Review CloudTrail** for any unauthorized usage
4. **Update** all applications using the old keys
5. **Rotate** all other keys as precaution

### Monitoring Setup
```bash
# Set up CloudWatch alarm for root account usage
aws cloudwatch put-metric-alarm \
    --alarm-name root-account-usage \
    --alarm-description "Alert on root account usage" \
    --metric-name UserName \
    --namespace CloudTrailMetrics \
    --statistic Sum \
    --period 300 \
    --evaluation-periods 1 \
    --threshold 1 \
    --comparison-operator GreaterThanOrEqualToThreshold
```

## Quick Commands

```bash
# Check current AWS identity
aws-vault exec dev -- aws sts get-caller-identity

# List all resources in region
aws-vault exec dev -- aws resourcegroupstaggingapi get-resources

# Quick security audit
aws-vault exec dev -- aws iam get-account-summary

# Check for public S3 buckets
aws-vault exec dev -- aws s3api list-buckets | jq -r '.Buckets[].Name' | \
  xargs -I {} aws-vault exec dev -- aws s3api get-bucket-acl --bucket {}
```

## Resources

- [AWS Security Best Practices](https://aws.amazon.com/architecture/security-identity-compliance/)
- [aws-vault Documentation](https://github.com/99designs/aws-vault)
- [AWS IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [Cost Optimization](https://aws.amazon.com/aws-cost-management/)