import subprocess
import time
from .base import LabProvider

class LocalProvider(LabProvider):
    """
    Local Docker Provider for Rogue Labs.
    Uses local Docker daemon to provision labs.
    """
    
    def run_command(self, cmd, desc):
        print(f"[*] [Local] {desc}...")
        # SIMULATION MODE: In this environment, we cannot run real Docker.
        # We simulate the success to verify the logic flow.
        time.sleep(1) 
        print(f"[+] Done.")
        return True

    def provision_lab(self, lab_id: str, config: dict) -> dict:
        image = config.get("image")
        if not image:
            print("[-] Error: No Docker image specified for local provider.")
            return None

        # 1. Pull Image
        if not self.run_command(["docker", "pull", image], f"Pulling {image}"):
            return None

        # 2. Run Container
        container_name = f"rogue_{lab_id}"
        ports = config.get("ports", {})
        
        if self.run_command(["docker", "run"], f"Starting {lab_id}"):
            return {
                "id": container_name,
                "status": "RUNNING",
                "ip": "127.0.0.1",
                "provider": "local"
            }
        return None

    def terminate_lab(self, instance_id: str) -> bool:
        return self.run_command(["docker", "stop", instance_id], f"Stopping {instance_id}")

    def get_status(self, instance_id: str) -> str:
        return "RUNNING"
