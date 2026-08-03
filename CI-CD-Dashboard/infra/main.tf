# Main Terraform entrypoint for the Azure deployment.
# This file defines the core Azure resources required for the CI/CD dashboard project.

# Create the Azure resource group for the CI/CD dashboard environment.
resource "azurerm_resource_group" "ci_dashboard" {
  # Use the resource group name provided via Terraform variables.
  name = var.resource_group_name

  # Use the Azure region provided via Terraform variables.
  location = var.location

  # Apply standard tags for governance and management.
  tags = {
    Environment = "Development"
    Project     = "CI-CD Dashboard"
    ManagedBy   = "Terraform"
  }
}
