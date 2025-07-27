# SQS Module

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "queues" {
  description = "Map of queue configurations"
  type = map(object({
    visibility_timeout_seconds  = optional(number, 30)
    message_retention_seconds   = optional(number, 1209600)
    max_message_size            = optional(number, 262144)
    delay_seconds               = optional(number, 0)
    fifo_queue                  = optional(bool, false)
    content_based_deduplication = optional(bool, false)
  }))
}

# Create SQS queues
resource "aws_sqs_queue" "queues" {
  for_each = var.queues

  name                        = var.queues[each.key].fifo_queue ? "${var.project_name}-${var.environment}-${each.key}.fifo" : "${var.project_name}-${var.environment}-${each.key}"
  visibility_timeout_seconds  = each.value.visibility_timeout_seconds
  message_retention_seconds   = each.value.message_retention_seconds
  max_message_size            = each.value.max_message_size
  delay_seconds               = each.value.delay_seconds
  fifo_queue                  = each.value.fifo_queue
  content_based_deduplication = each.value.content_based_deduplication

  # Enable server-side encryption
  kms_master_key_id                 = "alias/aws/sqs"
  kms_data_key_reuse_period_seconds = 300

  tags = {
    Name        = "${var.project_name}-${var.environment}-${each.key}"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Create dead letter queues for main queues
resource "aws_sqs_queue" "deadletter_queues" {
  for_each = var.queues

  name                        = var.queues[each.key].fifo_queue ? "${var.project_name}-${var.environment}-${each.key}-dlq.fifo" : "${var.project_name}-${var.environment}-${each.key}-dlq"
  message_retention_seconds   = 1209600 # 14 days
  fifo_queue                  = each.value.fifo_queue
  content_based_deduplication = each.value.content_based_deduplication

  # Enable server-side encryption
  kms_master_key_id                 = "alias/aws/sqs"
  kms_data_key_reuse_period_seconds = 300

  tags = {
    Name        = "${var.project_name}-${var.environment}-${each.key}-dlq"
    Environment = var.environment
    Project     = var.project_name
    Type        = "DeadLetterQueue"
  }
}

# Add redrive policy to main queues
resource "aws_sqs_queue_redrive_policy" "redrive_policy" {
  for_each = var.queues

  queue_url = aws_sqs_queue.queues[each.key].id
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.deadletter_queues[each.key].arn
    maxReceiveCount     = 3
  })
}

# Outputs
output "queue_names" {
  value = { for k, v in aws_sqs_queue.queues : k => v.name }
}

output "queue_arns" {
  value = { for k, v in aws_sqs_queue.queues : k => v.arn }
}

output "queue_urls" {
  value = { for k, v in aws_sqs_queue.queues : k => v.id }
}

output "deadletter_queue_arns" {
  value = { for k, v in aws_sqs_queue.deadletter_queues : k => v.arn }
}
