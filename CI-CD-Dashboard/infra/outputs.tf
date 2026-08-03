# Output values for the Terraform deployment.
# These values expose useful connection and resource details after apply.

# Output the Azure resource group name created by Terraform.
output "resource_group_name" {
  description = "Name of the Azure resource group"
  value       = azurerm_resource_group.ci_dashboard.name
}

# Output the Azure virtual machine name created by Terraform.
output "vm_name" {
  description = "Name of the Azure Linux virtual machine"
  value       = azurerm_linux_virtual_machine.ci_dashboard_vm.name
}

# Output the public IP address assigned to the VM.
output "public_ip_address" {
  description = "Public IP address of the VM"
  value       = azurerm_public_ip.ci_dashboard_public_ip.ip_address
}

# Output the SSH command to connect to the VM.
output "ssh_command" {
  description = "SSH command to connect to the VM"
  value       = "ssh ${var.admin_username}@${azurerm_public_ip.ci_dashboard_public_ip.ip_address}"
}
