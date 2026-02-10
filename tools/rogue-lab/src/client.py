"""
Client Module
Handles flag submission and API interaction.
"""
def submit_flag(flag):
    if not flag.startswith("ROGUE{") or not flag.endswith("}"):
        print("[-] Invalid flag format. Must be ROGUE{...}")
        return

    print(f"[*] Encrypting flag submission...")
    print(f"[*] Sending to secure node...")
    # Mock network call
    print(f"[+] Flag ACCEPTED. 100 Points awarded.")
