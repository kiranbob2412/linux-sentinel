variable "region" {
  description = "AWS region containing the default VPC and subnet."
  type        = string
  default     = "ap-south-1"
}

variable "ami_id" {
  description = "Region-specific Ubuntu or Amazon Linux AMI ID."
  type        = string
}

variable "subnet_id" {
  description = "Subnet ID in the default VPC where the instance will run."
  type        = string
}

variable "instance_type" {
  description = "Small instance type for the learning lab."
  type        = string
  default     = "t3.micro"
}

variable "key_name" {
  description = "Existing EC2 key pair name."
  type        = string
  default     = null
}

variable "ssh_cidr" {
  description = "Single trusted public IP in CIDR notation, for example 198.51.100.10/32."
  type        = string
}

variable "repository_url" {
  description = "Public GitHub URL for this repository."
  type        = string
}