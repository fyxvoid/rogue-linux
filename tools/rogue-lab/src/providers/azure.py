import time
from .base import LabProvider

class AzureProvider(LabProvider):
    """
    Azure Cloud Provider for Rogue Labs.
    Uses Azure SDK to provision Resource Groups and VMs.
    """
    
    def __init__(self, location="eastus"):
        self.location = location

    def provision_lab(self, lab_id: str, config: dict) -> dict:
        print(f"[*] [Azure] Provisioning Lab: {lab_id} in {self.location}...")
        
        # Mocking Azure VM Creation
        vm_name = f"rogue-lab-{lab_id}-{int(time.time())}"
        print(f"[*] [Azure] Creating Resource Group: rg-{vm_name}...")
        print(f"[*] [Azure] Deploying VM: {vm_name}...")
        time.sleep(1)
        
        return {
            "id": vm_name,
            "status": "RUNNING",
            "ip": "20.45.192.11", # Mock IP
            "provider": "azure"
        }

    def terminate_lab(self, instance_id: str) -> bool:
        print(f"[*] [Azure] Deleting Resource Group for {instance_id}...")
        time.sleep(1)
        print(f"[+] [Azure] Resources cleaned up.")
        return True

    def get_status(self, instance_id: str) -> str:
        return "RUNNING"
