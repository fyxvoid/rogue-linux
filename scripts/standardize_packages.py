#!/usr/bin/env python3
import os
import sys
import re
import shutil

# CONFIGURATION
ROOT = "/home/rogue/workspace/rogue-linux"
PACKAGES_DIR = os.path.join(ROOT, "packages")
ROOT_TAR_DIR = os.path.join(ROOT, "tar")

def standardize_pkg(pkg_path, pkg_name, cat_name):
    toml_file = os.path.join(pkg_path, f"{pkg_name}.toml")
    if not os.path.exists(toml_file):
        return

    print(f"Standardizing {cat_name}/{pkg_name}...")
    
    # 1. Create Directory Structure
    for d in ["tar", "source", "build", "pkgroot", "logs"]:
        os.makedirs(os.path.join(pkg_path, d), exist_ok=True)

    # 2. Relocate Tarball if exists in root
    # We look for any file starting with pkg_name in root tar
    actual_tar = None
    if os.path.exists(ROOT_TAR_DIR):
        for f in os.listdir(ROOT_TAR_DIR):
            if f.startswith(pkg_name) and (f.endswith(".tar.gz") or f.endswith(".tar.xz") or f.endswith(".tar.bz2")):
                # Double check it matches basically
                src_path = os.path.join(ROOT_TAR_DIR, f)
                dest_path = os.path.join(pkg_path, "tar", f)
                print(f"  Moving {f} to local tar/...")
                shutil.move(src_path, dest_path)
                actual_tar = f
                break

    # 3. Process Metadata as Text
    with open(toml_file, "r") as f:
        lines = f.readlines()

    new_lines = []
    in_builder_steps = False
    
    for line in lines:
        stripped = line.strip()
        
        # [builder] -> [build]
        if stripped == "[builder]":
            new_lines.append("[build]\n")
            continue
            
        # [builder.steps] -> [build]
        if stripped == "[builder.steps]":
            in_builder_steps = True
            continue
            
        # commands = [...] -> steps = [...]
        if in_builder_steps and stripped.startswith("commands"):
            line = line.replace("commands", "steps")
            
        # Update source file if we found the actual tar
        if actual_tar and stripped.startswith("file = "):
            line = f'file = "{actual_tar}"\n'
            
        # Normalize tar extraction paths
        # Replace absolute /home/rogue/workspace/rogue-linux/tar/ with relative tar/
        if "tar -xf" in line:
            # Match any path before /tar/ and replace with relative tar/
            line = re.sub(r'tar -xf \S+/tar/', 'tar -xf tar/', line)
            # Also ensure it uses the actual filename if we have it
            if actual_tar:
                line = re.sub(r'tar -xf tar/\S+', f'tar -xf tar/{actual_tar}', line)

        # Reset builder steps flag if we hit a new header
        if stripped.startswith("[") and stripped != "[builder.steps]":
            in_builder_steps = False
            
        new_lines.append(line)

    # 4. Save Normalized Metadata
    with open(toml_file, "w") as f:
        f.writelines(new_lines)

    # 5. Add README.md
    readme_path = os.path.join(pkg_path, "README.md")
    if not os.path.exists(readme_path):
        with open(readme_path, "w") as f:
            f.write(f"# {pkg_name}\n\nStandardized build layout for Cogman.\n\n")
            f.write("- `tar/`: Source archives\n")
            f.write("- `source/`: Extracted code\n")
            f.write("- `build/`: Isolated build directory\n")
            f.write("- `pkgroot/`: Staged installation root\n")

def main():
    if not os.path.exists(PACKAGES_DIR):
        print(f"Packages dir not found: {PACKAGES_DIR}")
        return

    for cat in os.listdir(PACKAGES_DIR):
        cat_dir = os.path.join(PACKAGES_DIR, cat)
        if not os.path.isdir(cat_dir): continue
        
        for pkg in os.listdir(cat_dir):
            pkg_dir = os.path.join(cat_dir, pkg)
            if not os.path.isdir(pkg_dir): continue
            
            standardize_pkg(pkg_dir, pkg, cat)
    
    # Clean up empty root tar dir if needed
    if os.path.exists(ROOT_TAR_DIR) and not os.listdir(ROOT_TAR_DIR):
        os.rmdir(ROOT_TAR_DIR)

if __name__ == "__main__":
    main()
