# Azure VM Configuration with Ansible & Bicep

This project demonstrates a hybrid Cloud/DevOps workflow: provisioning infrastructure on **Microsoft Azure** using **Bicep** (IaC), and then configuring the OS using **Ansible** (Configuration Management).

## Components
- **vm.bicep**: Defines an Ubuntu Virtual Machine, VNet, and Public IP.
- **playbook.yml**: Ansible configuration to install Nginx, secure the firewall, and deploy content.

## How to Run

### 1. Provision Infrastructure
Requires [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli).
```bash
az group create --name PortfolioGroup --location eastus
az deployment group create --resource-group PortfolioGroup --template-file vm.bicep
```
*Note the Public IP address from the output.*

### 2. Configure Server
Update `inventory.ini` with the Public IP from step 1.

```bash
ansible-playbook -i inventory.ini playbook.yml
```

### 3. Verify
Visit `http://<YOUR_AZURE_VM_IP>` in your browser. You should see "Deployed via Ansible on Azure!".

## Key Skills
- **Bicep/ARM**: Native Azure Infrastructure as Code.
- **Ansible**: Idempotent server configuration.
- **Hybrid Workflow**: Splitting "Creation" vs "Configuration".
