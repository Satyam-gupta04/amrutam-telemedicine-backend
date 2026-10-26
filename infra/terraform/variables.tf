variable "aws_region" {
  type        = string
  default     = "ap-south-1"
}

variable "environment" {
  type        = string
  default     = "production"
}

variable "db_username" {
  type        = string
  default     = "amrutam_admin"
}

variable "db_password" {
  type        = string
  sensitive   = true
}

variable "app_name" {
  type        = string
  default     = "amrutam-telemedicine"
}
