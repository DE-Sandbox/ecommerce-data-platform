# DynamoDB Module

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "tables" {
  description = "Map of table configurations"
  type = map(object({
    hash_key  = string
    range_key = optional(string)
  }))
}

# Create DynamoDB tables
resource "aws_dynamodb_table" "tables" {
  for_each = var.tables
  
  name         = "${var.project_name}-${var.environment}-${each.key}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = each.value.hash_key
  range_key    = each.value.range_key
  
  attribute {
    name = each.value.hash_key
    type = "S"
  }
  
  dynamic "attribute" {
    for_each = each.value.range_key != null ? [each.value.range_key] : []
    content {
      name = attribute.value
      type = "S"
    }
  }
  
  tags = {
    Name        = "${var.project_name}-${var.environment}-${each.key}"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Outputs
output "table_names" {
  value = { for k, v in aws_dynamodb_table.tables : k => v.name }
}

output "table_arns" {
  value = { for k, v in aws_dynamodb_table.tables : k => v.arn }
}