# Input variables for the Azure infrastructure deployment.
# These values are used to configure the core naming, location, and compute settings.

variable "resource_group_name" {
  description = "Name of the Azure resource group that will contain the infrastructure resources."
  type        = string
  default     = "rg-ci-dashboard"

  validation {
    condition     = length(trimspace(var.resource_group_name)) > 0
    error_message = "resource_group_name must not be empty."
  }
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "Central India"

  validation {
    condition     = length(trimspace(var.location)) > 0
    error_message = "location must not be empty."
  }
}

variable "vm_name" {
  description = "Name of the Azure virtual machine to create."
  type        = string
  default     = "ci-dashboard-vm"

  validation {
    condition     = length(trimspace(var.vm_name)) > 0
    error_message = "vm_name must not be empty."
  }
}

variable "vm_size" {
  description = "Azure VM size to use for the compute instance."
  type        = string
  default     = "Standard_B1s"

  validation {
    condition     = length(trimspace(var.vm_size)) > 0
    error_message = "vm_size must not be empty."
  }
}

variable "admin_username" {
  description = "Administrative username for the Azure virtual machine."
  type        = string
  default     = "azureuser"

  validation {
    condition     = length(trimspace(var.admin_username)) > 0
    error_message = "admin_username must not be empty."
  }
}

variable "ssh_public_key" {
  description = "Public SSH key used to authenticate to the Azure VM."
  type        = string
  default     = ""
  sensitive   = true
}
