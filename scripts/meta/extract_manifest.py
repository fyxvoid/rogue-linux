#!/usr/bin/env python3
import os
import re
import cogman_utils as butler

# CONFIGURATION
ROOT = "/home/rogue/workspace/rogue-linux"
PACKAGES_DIR = os.path.join(ROOT, "packages")

def get_pkg_info(pkg_path, pkg_name):
    toml_file = os.path.join(pkg_path, f"{pkg_name}.toml")
    if not os.path.exists(toml_file):
        return None

    with open(toml_file, "r") as f:
        content = f.read()

    name = re.search(r'name\s*=\s*"([^"]+)"', content)
    version = re.search(r'version\s*=\s*"([^"]+)"', content)
    filename = re.search(r'file\s*=\s*"([^"]+)"', content)

    if not (name and version and filename):
        return None

    return {
        "name": name.group(1),
        "version": version.group(1),
        "file": filename.group(1),
        "path": pkg_path
    }

def main():
    butler.log_check("Scanning the package repository for valid definitions")
    pkgs = []
    for root, dirs, files in os.walk(PACKAGES_DIR):
        for d in dirs:
            pkg_dir = os.path.join(root, d)
            # Only if it's a leaf package dir (has name.toml)
            if os.path.exists(os.path.join(pkg_dir, f"{d}.toml")):
                info = get_pkg_info(pkg_dir, d)
                if info:
                    pkgs.append(info)
    
    # Save to a temporary list
    with open("pkg_manifest.txt", "w") as f:
        for p in pkgs:
            f.write(f"{p['name']}|{p['version']}|{p['file']}|{p['path']}\n")
    
    butler.log_success(f"I have successfully extracted information for {len(pkgs)} package entities")

if __name__ == "__main__":
    main()
