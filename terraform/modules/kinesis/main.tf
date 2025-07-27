# Kinesis Module

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "streams" {
  description = "Map of stream configurations"
  type = map(object({
    shard_count      = number
    retention_period = optional(number, 24)
  }))
}

# Create Kinesis data streams
resource "aws_kinesis_stream" "streams" {
  for_each = var.streams

  name             = "${var.project_name}-${var.environment}-${each.key}"
  shard_count      = each.value.shard_count
  retention_period = each.value.retention_period

  encryption_type = "KMS"
  kms_key_id      = "alias/aws/kinesis"

  shard_level_metrics = [
    "IncomingBytes",
    "OutgoingBytes",
  ]

  stream_mode_details {
    stream_mode = "PROVISIONED"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-${each.key}"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Outputs
output "stream_names" {
  value = { for k, v in aws_kinesis_stream.streams : k => v.name }
}

output "stream_arns" {
  value = { for k, v in aws_kinesis_stream.streams : k => v.arn }
}
