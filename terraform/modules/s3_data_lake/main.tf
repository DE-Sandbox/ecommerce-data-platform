# S3 Data Lake Module

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "bucket_names" {
  description = "Map of bucket types to names"
  type        = map(string)
}

# Create S3 buckets
resource "aws_s3_bucket" "data_lake" {
  for_each = var.bucket_names
  
  bucket = each.value
  
  tags = {
    Name        = each.value
    Environment = var.environment
    Project     = var.project_name
    BucketType  = each.key
  }
}

# Enable versioning for artifacts bucket
resource "aws_s3_bucket_versioning" "artifacts" {
  bucket = aws_s3_bucket.data_lake["artifacts"].id
  
  versioning_configuration {
    status = "Enabled"
  }
}

# Lifecycle policies for data retention
resource "aws_s3_bucket_lifecycle_configuration" "data_lifecycle" {
  for_each = {
    raw       = 30   # Move to Glacier after 30 days
    processed = 90   # Move to Glacier after 90 days
    logs      = 7    # Delete after 7 days
  }
  
  bucket = aws_s3_bucket.data_lake[each.key].id
  
  rule {
    id     = "${each.key}-lifecycle"
    status = "Enabled"
    
    transition {
      days          = each.value
      storage_class = each.key == "logs" ? "GLACIER" : "GLACIER"
    }
    
    expiration {
      days = each.key == "logs" ? each.value : 365
    }
  }
}

# Block public access
resource "aws_s3_bucket_public_access_block" "data_lake" {
  for_each = var.bucket_names
  
  bucket = aws_s3_bucket.data_lake[each.key].id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Outputs
output "bucket_names" {
  value = { for k, v in aws_s3_bucket.data_lake : k => v.id }
}

output "bucket_arns" {
  value = { for k, v in aws_s3_bucket.data_lake : k => v.arn }
}