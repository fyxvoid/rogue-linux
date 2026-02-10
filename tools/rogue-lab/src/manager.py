from .providers.aws import AWSProvider
from .providers.azure import AzureProvider
from .providers.local import LocalProvider

LABS = {
    "metasploitable": {
        "name": "Metasploitable 2",
        "description": "The classic vulnerable VM.",
        "difficulty": "Easy",
        "points": 100,
        "ami": "ami-0abcdef1234567890", 
        "azure_image": "rogue-metasploitable-v1",
        "image": "tleemcjr/metasploitable2:latest",
        "ports": {"21/tcp": 21, "22/tcp": 22, "80/tcp": 80}
    },
    "juice-shop": {
        "name": "OWASP Juice Shop",
        "description": "Modern web application vulnerabilities.",
        "difficulty": "Medium",
        "points": 200,
        "ami": "ami-0987654321fedcba",
        "azure_image": "rogue-juice-shop-v1",
        "image": "bkimminich/juice-shop",
        "ports": {"3000/tcp": 3000}
    },
    "dvwa": {
        "name": "Damn Vulnerable Web App",
        "description": "PHP/MySQL web application.",
        "difficulty": "Easy",
        "points": 75,
        "ami": "ami-1122334455667788",
        "azure_image": "rogue-dvwa-v1",
        "image": "vulnerables/web-dvwa",
        "ports": {"80/tcp": 8080}
    }
}

ACTIVE_SESSIONS = {} # Track active labs: {lab_id: instance_id}

def get_provider(provider_name):
    if provider_name == "aws":
        return AWSProvider()
    elif provider_name == "azure":
        return AzureProvider()
    elif provider_name == "local":
        return LocalProvider()
    else:
        print(f"[-] Unknown provider: {provider_name}. Defaulting to Local.")
        return LocalProvider()

def list_labs(filter_category=None):
    print("\n[+] AVAILABLE ROGUE LABS")
    print("-" * 75)
    print(f"{'ID':<15} {'NAME':<25} {'DIFFICULTY':<10} {'POINTS'}")
    print("-" * 75)
    for lab_id, data in LABS.items():
        print(f"{lab_id:<15} {data['name']:<25} {data['difficulty']:<10} {data['points']}")
    print("-" * 75)

def start_lab(lab_id, provider_name="local"):
    if lab_id not in LABS:
        print(f"[-] Error: Lab '{lab_id}' not found.")
        return
    
    lab = LABS[lab_id]
    provider = get_provider(provider_name)
    
    print(f"[*] Requesting interface for {lab['name']} via {provider_name.upper()}...")
    
    config = {
        "ami": lab.get("ami"),
        "azure_image": lab.get("azure_image"),
        "image": lab.get("image"),
        "ports": lab.get("ports")
    }
    
    result = provider.provision_lab(lab_id, config)
    
    if result and result.get("status") == "RUNNING":
        ACTIVE_SESSIONS[lab_id] = result["id"]
        print(f"[+] Lab is ONLINE.")
        print(f"[+] Target IP: {result['ip']}")
        print(f"[+] Instance ID: {result['id']}")
        if provider_name == "local":
             print(f"[!] Access locally via mapped ports: {lab.get('ports')}")
        print(f"[!] Happy Hacking.")
    else:
        print("[-] Provisioning failed.")

def stop_lab(lab_id, provider_name="aws"):
    # In a real app, we'd look up the instance_id from a database or local state file
    # For this POC, we'll ask the provider to terminate based on a mock lookup or just pass the lab_id if mapped
    
    # Mock lookup
    instance_id = ACTIVE_SESSIONS.get(lab_id, f"i-mock-{lab_id}")
    
    provider = get_provider(provider_name)
    provider.terminate_lab(instance_id)

    if lab_id in ACTIVE_SESSIONS:
        del ACTIVE_SESSIONS[lab_id]
