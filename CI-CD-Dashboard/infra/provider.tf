# Terraform version constraint for the Azure infrastructure configuration.
terraform {
  required_version = ">= 1.5"

  required_providers {
    # Azure Resource Manager provider for creating Azure resources.
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

# AzureRM provider configuration.
# The features block is required for the provider to function correctly.
provider "azurerm" {
  features {}
}
