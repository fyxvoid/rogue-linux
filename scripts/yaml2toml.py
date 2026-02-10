#!/usr/bin/env python3
import os
import sys
import yaml

ROOT = "/home/rogue/workspace/rogue-linux"
SRC = os.path.join(ROOT, "metadata")
DEST = os.path.join(ROOT, "metadata_toml")

def dump_toml_val(val):
    if isinstance(val, bool):
        return "true" if val else "false"
    elif isinstance(val, int) or isinstance(val, float):
        return str(val)
    elif isinstance(val, str):
        if "\n" in val:
            # Multiline string
            return '"""\n' + val + '"""'
        else:
            return '"' + val.replace('"', '\\"') + '"'
    elif isinstance(val, list):
        items = [dump_toml_val(x) for x in val]
        return "[" + ", ".join(items) + "]"
    else:
        return '"' + str(val) + '"'

def convert_package(group, pkg, pkg_dir):
    meta_dir = os.path.join(pkg_dir, "metadata")
    if not os.path.exists(meta_dir):
        return

    # Read YAMLs
    try:
        with open(os.path.join(meta_dir, "identity.yaml"), "r") as f:
            identity = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Skipping {group}/{pkg}: No identity.yaml")
        return

    builder = {}
    try:
        with open(os.path.join(meta_dir, "builder.yaml"), "r") as f:
            builder = yaml.safe_load(f) or {}
    except FileNotFoundError:
        pass

    installer = {}
    try:
        with open(os.path.join(meta_dir, "installer.yaml"), "r") as f:
            installer = yaml.safe_load(f) or {}
    except FileNotFoundError:
        pass

    policy = {}
    try:
        with open(os.path.join(meta_dir, "policy.yaml"), "r") as f:
            policy = yaml.safe_load(f) or {}
    except FileNotFoundError:
        pass
    
    # Generate TOML Content
    lines = []
    
    # [identity]
    lines.append("[identity]")
    for k, v in identity.items():
        if k == "source" or k == "depends": continue # Handle separately?
        lines.append(f'{k} = {dump_toml_val(v)}')
    lines.append("")

    # [source] (from identity['source'])
    if 'source' in identity:
        lines.append("[source]")
        for k, v in identity['source'].items():
            lines.append(f'{k} = {dump_toml_val(v)}')
        lines.append("")

    # [dependencies] (from identity['depends'])
    if 'depends' in identity:
        lines.append("[dependencies]")
        for k, v in identity['depends'].items():
             # k is 'build', 'runtime', etc.
             # v is list
             lines.append(f'{k} = {dump_toml_val(v)}')
        lines.append("")
        
    # [build] (from builder)
    if builder:
        lines.append("[build]")
        for k, v in builder.items():
            lines.append(f'{k} = {dump_toml_val(v)}')
        lines.append("")
        
    # [installer] (from installer)
    # verify goes to [installer.verify] or just verify key?
    # cogmanII expects [installer.verify] table?
    # Let's check installer keys.
    installer_steps = installer.get('steps', [])
    installer_verify = installer.get('verify', [])

    lines.append("[installer]")
    if installer_steps:
        lines.append(f'steps = {dump_toml_val(installer_steps)}')
    lines.append("")
    
    if installer_verify:
        lines.append("[installer.verify]")
        lines.append(f'paths = {dump_toml_val(installer_verify)}')
        lines.append("")

    # [policy]
    if policy:
        lines.append("[policy]")
        # Policy structure is nested (filesystem -> read -> list).
        # Simple recursion? Or manual flatten?
        # My dumper handles basic types, but dicts?
        # Recursively dump tables?
        # Since policy is nested, I should use [policy.filesystem] etc?
        # Simple approach: just ignore for now, or print as strings if needed?
        # cogmanII policy support is minimal. I'll comment out for now or try basics.
        pass # Skip policy for now to avoid complexity in MVP script

    # Write
    dest_dir = os.path.join(DEST, group, pkg)
    os.makedirs(dest_dir, exist_ok=True)
    dest_file = os.path.join(dest_dir, f"{pkg}.toml")
    
    with open(dest_file, "w") as f:
        f.write("\n".join(lines))
    print(f"Converted {group}/{pkg} -> {dest_file}")

def main():
    if not os.path.exists(SRC):
        print(f"Source metadata dir not found: {SRC}")
        sys.exit(1)
        
    for group in os.listdir(SRC):
        group_dir = os.path.join(SRC, group)
        if not os.path.isdir(group_dir): continue
        
        for pkg in os.listdir(group_dir):
            pkg_dir = os.path.join(group_dir, pkg)
            if not os.path.isdir(pkg_dir): continue
            
            # Check if it has metadata folder
            if os.path.exists(os.path.join(pkg_dir, "metadata", "identity.yaml")):
                convert_package(group, pkg, pkg_dir)

if __name__ == "__main__":
    main()
