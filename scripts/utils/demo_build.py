#!/usr/bin/env python3
import time
import sys
import os

# Ensure we can import cogman_utils
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
import cogman_utils as butler

def simulate_package_build(name):
    butler.log_info(f"Initializing build sequence for package: {name}")
    butler.log_check("External dependencies")
    butler.log_success("All dependencies satisfied.")

    # Phase 1: Downloading
    butler.log_info(f"Fetching source tarball for {name}...")
    for i in range(101):
        butler.show_progress(i, 100, "DOWNLOADING")
        time.sleep(0.03)
    butler.log_success("Source verification passed.")

    # Phase 2: Building
    butler.log_info("Executing NATIVE build variant...")
    for i in range(101):
        if i == 20: butler.log_native("CC", "main.o")
        if i == 45: butler.log_native("CC", "crypto.o")
        if i == 70: butler.log_native("CC", "net.o")
        butler.show_progress(i, 100, "COMPILING")
        time.sleep(0.04)

    # Phase 3: Linking
    butler.log_native("LD", f"bin/{name}")
    time.sleep(1)
    
    butler.log_success(f"Package {name} built and verified.")
    butler.advice(f"I've moved the binary to /usr/bin/{name}. Do try not to lose it, sir.")

if __name__ == "__main__":
    simulate_package_build("rogue-vpn")
