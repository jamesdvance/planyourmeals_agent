# =============================================================================
# dev.tfvars - Variable values for the dev environment
# Usage: terraform plan -var-file="../environments/dev.tfvars"
# =============================================================================

# General
project_name = "planyourmeals"
environment  = "dev"
aws_region   = "us-east-1"

# Networking
vpc_cidr             = "10.0.0.0/16"
public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
private_subnet_cidrs = ["10.0.10.0/24", "10.0.11.0/24"]

# RDS / Database
db_name                = "planyourmeals"
db_instance_class      = "db.t3.micro"
db_allocated_storage   = 20
db_engine_version      = "16"
db_multi_az            = false
db_skip_final_snapshot = true

# NOTE: db_username and db_password are sensitive and should be provided
# via environment variables or a secrets manager, never committed to VCS.
#   export TF_VAR_db_username="your_username"
#   export TF_VAR_db_password="your_password"

# ECS
ecs_container_insights = true
