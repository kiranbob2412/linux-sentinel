output "instance_id" {
  value       = aws_instance.sentinel.id
  description = "EC2 instance ID."
}

output "public_ip" {
  value       = aws_instance.sentinel.public_ip
  description = "Public IP for the lab instance."
}

output "security_group_id" {
  value       = aws_security_group.sentinel.id
  description = "Security group attached to the instance."
}