# Network-related Terraform resources for the CI/CD dashboard VM.

# Create the virtual network for the VM and supporting services.
resource "azurerm_virtual_network" "ci_dashboard_vnet" {
  name                = "vnet-ci-dashboard"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.ci_dashboard.location
  resource_group_name = azurerm_resource_group.ci_dashboard.name

  depends_on = [azurerm_resource_group.ci_dashboard]

  tags = {
    Environment = "Development"
    Project     = "CI-CD Dashboard"
    ManagedBy   = "Terraform"
  }
}

# Create the subnet that will host the VM network interface.
resource "azurerm_subnet" "ci_dashboard_subnet" {
  name                 = "subnet-ci-dashboard"
  resource_group_name  = azurerm_resource_group.ci_dashboard.name
  virtual_network_name = azurerm_virtual_network.ci_dashboard_vnet.name
  address_prefixes     = ["10.0.1.0/24"]

  depends_on = [azurerm_virtual_network.ci_dashboard_vnet]
}

# Create the network security group to allow common inbound traffic for the VM.
resource "azurerm_network_security_group" "ci_dashboard_nsg" {
  name                = "nsg-ci-dashboard"
  location            = azurerm_resource_group.ci_dashboard.location
  resource_group_name = azurerm_resource_group.ci_dashboard.name

  security_rule {
    name                       = "SSH"
    priority                   = 1001
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "HTTP"
    priority                   = 1002
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "80"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "HTTPS"
    priority                   = 1003
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "443"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  

  tags = {
    Environment = "Development"
    Project     = "CI-CD Dashboard"
    ManagedBy   = "Terraform"
  }
}

resource "azurerm_network_security_rule" "allow_3000" {
  name                        = "Allow3000"
  priority                    = 1010
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "Tcp"
  source_port_range           = "*"
  destination_port_range      = "3000"
  source_address_prefix       = "*"
  destination_address_prefix  = "*"
  resource_group_name         = azurerm_resource_group.ci_dashboard.name
  network_security_group_name = azurerm_network_security_group.ci_dashboard_nsg.name
}

resource "azurerm_network_security_rule" "allow_8000" {
  name                        = "Allow8000"
  priority                    = 1011
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "Tcp"
  source_port_range           = "*"
  destination_port_range      = "8000"
  source_address_prefix       = "*"
  destination_address_prefix  = "*"
  resource_group_name         = azurerm_resource_group.ci_dashboard.name
  network_security_group_name = azurerm_network_security_group.ci_dashboard_nsg.name
}

# Associate the network security group with the subnet.
resource "azurerm_subnet_network_security_group_association" "ci_dashboard_subnet_nsg_assoc" {
  subnet_id                 = azurerm_subnet.ci_dashboard_subnet.id
  network_security_group_id = azurerm_network_security_group.ci_dashboard_nsg.id
}

# Create a public IP address for the VM's network interface.
resource "azurerm_public_ip" "ci_dashboard_public_ip" {
  name                = "pip-ci-dashboard"
  location            = azurerm_resource_group.ci_dashboard.location
  resource_group_name = azurerm_resource_group.ci_dashboard.name
  allocation_method   = "Static"
  sku                 = "Standard"

  depends_on = [azurerm_resource_group.ci_dashboard]

  tags = {
    Environment = "Development"
    Project     = "CI-CD Dashboard"
    ManagedBy   = "Terraform"
  }
}

# Create a network interface and attach it to the subnet and public IP.
resource "azurerm_network_interface" "ci_dashboard_nic" {
  name                = "nic-ci-dashboard"
  location            = azurerm_resource_group.ci_dashboard.location
  resource_group_name = azurerm_resource_group.ci_dashboard.name

  depends_on = [azurerm_subnet.ci_dashboard_subnet, azurerm_public_ip.ci_dashboard_public_ip]

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.ci_dashboard_subnet.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.ci_dashboard_public_ip.id
  }

  tags = {
    Environment = "Development"
    Project     = "CI-CD Dashboard"
    ManagedBy   = "Terraform"
  }
}
