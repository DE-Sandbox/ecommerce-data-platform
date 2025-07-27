# LocalStack Configuration for Local Development
terraform {
  required_version = ">= 1.9.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region                      = var.aws_region
  access_key                  = "test"  # pragma: allowlist secret
  secret_key                  = "test"  # pragma: allowlist secret
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  s3_use_path_style           = true

  endpoints {
    s3             = "http://s3.localhost.localstack.cloud:4566"
    dynamodb       = "http://localhost:4566"
    lambda         = "http://localhost:4566"
    iam            = "http://localhost:4566"
    sns            = "http://localhost:4566"
    sqs            = "http://localhost:4566"
    kinesis        = "http://localhost:4566"
    firehose       = "http://localhost:4566"
    glue           = "http://localhost:4566"
    athena         = "http://localhost:4566"
    redshift       = "http://localhost:4566"
    secretsmanager = "http://localhost:4566"  # pragma: allowlist secret
    stepfunctions  = "http://localhost:4566"
    cloudwatch     = "http://localhost:4566"
    events         = "http://localhost:4566"
  }
}

# Variables
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "local"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "ecommerce-data-platform"
}

# Data Lake S3 Buckets
module "data_lake" {
  source = "../../modules/s3_data_lake"

  project_name = var.project_name
  environment  = var.environment

  bucket_names = {
    raw       = "${var.project_name}-${var.environment}-raw"
    processed = "${var.project_name}-${var.environment}-processed"
    curated   = "${var.project_name}-${var.environment}-curated"
    artifacts = "${var.project_name}-${var.environment}-artifacts"
    logs      = "${var.project_name}-${var.environment}-logs"
  }
}

# DynamoDB Tables
module "dynamodb" {
  source = "../../modules/dynamodb"

  project_name = var.project_name
  environment  = var.environment

  tables = {
    job_metadata = {
      hash_key  = "job_id"
      range_key = "timestamp"
    }
    data_catalog = {
      hash_key  = "dataset_id"
      range_key = "version"
    }
    user_sessions = {
      hash_key = "session_id"
    }
    product_catalog = {
      hash_key = "product_id"
    }
  }
}

# Kinesis Streams
module "kinesis" {
  source = "../../modules/kinesis"

  project_name = var.project_name
  environment  = var.environment

  streams = {
    order_events = {
      shard_count      = 1
      retention_period = 24
    }
    user_activity = {
      shard_count      = 1
      retention_period = 24
    }
  }
}

# SQS Queues
module "sqs" {
  source = "../../modules/sqs"

  project_name = var.project_name
  environment  = var.environment

  queues = {
    ingestion_queue = {
      visibility_timeout = 300
      message_retention  = 345600 # 4 days
      has_dlq            = true
    }
    processing_queue = {
      visibility_timeout = 300
      message_retention  = 345600
      has_dlq            = true
    }
  }
}

# Outputs
output "s3_buckets" {
  value = module.data_lake.bucket_names
}

output "dynamodb_tables" {
  value = module.dynamodb.table_names
}

output "kinesis_streams" {
  value = module.kinesis.stream_names
}

output "sqs_queues" {
  value = module.sqs.queue_urls
}
