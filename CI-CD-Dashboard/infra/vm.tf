# Compute resources for the CI/CD dashboard Azure VM.

# Create the Ubuntu Linux virtual machine using the specified size and authentication settings.
resource "azurerm_linux_virtual_machine" "ci_dashboard_vm" {
  name                = var.vm_name
  resource_group_name = azurerm_resource_group.ci_dashboard.name
  location            = azurerm_resource_group.ci_dashboard.location
  size                = var.vm_size
  admin_username      = var.admin_username
  network_interface_ids = [
    azurerm_network_interface.ci_dashboard_nic.id
  ]

  depends_on = [azurerm_network_interface.ci_dashboard_nic]

  disable_password_authentication = true

  # Load the provisioning script through cloud-init custom data so it runs during VM creation.
  custom_data = base64encode(file("${path.module}/docker-install.sh"))

  admin_ssh_key {
    username   = var.admin_username
    public_key = var.ssh_public_key
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts-gen2"
    version   = "latest"
  }

  tags = {
    Environment = "Development"
    Project     = "CI-CD Dashboard"
    ManagedBy   = "Terraform"
  }
}
