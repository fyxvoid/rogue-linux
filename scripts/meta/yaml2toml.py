#!/usr/bin/env python3
import os
import sys
import yaml

# CONFIGURATION
ROOT = "/home/rogue/workspace/rogue-linux"
SRC = os.path.join(ROOT, "metadata")
DEST = os.path.join(ROOT, "packages") # Final canonical location
REMOVE_YAML = True

def dump_val(val, indent=0):
    padding = "  " * indent
    if isinstance(val, bool):
        return "true" if val else "false"
    elif isinstance(val, (int, float)):
        return str(val)
    elif isinstance(val, str):
        if "\n" in val:
            return '"""\n' + val + '"""'
        return '"' + val.replace('"', '\\"') + '"'
    elif isinstance(val, list):
        items = [dump_val(x) for x in val]
        return "[" + ", ".join(items) + "]"
    elif isinstance(val, dict):
        # We don't really want inline dicts in TOML for this schema
        # but if we had them, we'd handle them here.
        return "{ " + ", ".join(f'{k} = {dump_val(v)}' for k, v in val.items()) + " }"
    return '"' + str(val) + '"'

def convert_package(group, pkg, pkg_dir):
    meta_dir = os.path.join(pkg_dir, "metadata")
    if not os.path.exists(meta_dir):
        return

    # Files to load
    files = {
        "identity": os.path.join(meta_dir, "identity.yaml"),
        "builder": os.path.join(meta_dir, "builder.yaml"),
        "installer": os.path.join(meta_dir, "installer.yaml"),
        "policy": os.path.join(meta_dir, "policy.yaml")
    }

    data = {}
    for key, path in files.items():
        if os.path.exists(path):
            with open(path, "r") as f:
                data[key] = yaml.safe_load(f) or {}

    if "identity" not in data:
        print(f"Skipping {group}/{pkg}: No identity data")
        return

    lines = []
    
    # 1. [identity]
    lines.append("[identity]")
    identity = data["identity"]
    for k in ["name", "version", "category", "summary"]:
        if k in identity:
            lines.append(f'{k} = {dump_val(identity[k])}')
    
    # [source]
    if "source" in identity:
        lines.append("")
        lines.append("[identity.source]")
        for k, v in identity["source"].items():
            lines.append(f'{k} = {dump_val(v)}')

    # [depends]
    if "depends" in identity:
        lines.append("")
        lines.append("[identity.depends]")
        for k, v in identity["depends"].items():
            lines.append(f'{k} = {dump_val(v)}')
    lines.append("")

    # 2. [build] (was builder)
    builder = data.get("builder", {})
    if builder:
        lines.append("[build]")
        for k, v in builder.items():
            if k == "configure": continue # Handle nested
            lines.append(f'{k} = {dump_val(v)}')
        
        if "configure" in builder:
            lines.append("")
            lines.append("[build.configure]")
            for k, v in builder["configure"].items():
                lines.append(f'{k} = {dump_val(v)}')
        lines.append("")

    # 3. [installer]
    installer = data.get("installer", {})
    if installer:
        lines.append("[installer]")
        if "steps" in installer:
            lines.append(f'steps = {dump_val(installer["steps"])}')
        
        if "verify" in installer:
            lines.append("")
            lines.append("[installer.verify]")
            v = installer["verify"]
            if isinstance(v, list): # Legacy format
                lines.append(f'expected_files = {dump_val(v)}')
            elif isinstance(v, dict):
                for vk, vv in v.items():
                    lines.append(f'{vk} = {dump_val(vv)}')
        lines.append("")

    # 4. [policy]
    policy = data.get("policy", {})
    if policy:
        lines.append("[policy]")
        for k, v in policy.items():
            if isinstance(v, dict):
                lines.append("")
                lines.append(f"[policy.{k}]")
                for subk, subv in v.items():
                    lines.append(f'{subk} = {dump_val(subv)}')
            else:
                lines.append(f'{k} = {dump_val(v)}')
        lines.append("")

    # Write TOML
    dest_dir = os.path.join(DEST, group, pkg)
    os.makedirs(dest_dir, exist_ok=True)
    dest_file = os.path.join(dest_dir, f"{pkg}.toml")
    
    with open(dest_file, "w") as f:
        f.write("\n".join(lines))
    
    print(f"Migrated {group}/{pkg} -> {dest_file}")

    # Cleanup YAMLs
    if REMOVE_YAML:
        for path in files.values():
            if os.path.exists(path):
                os.remove(path)
        # Try to remove the metadata dir if empty
        try:
            os.rmdir(meta_dir)
            # Try to remove pkg dir if empty
            # os.rmdir(pkg_dir) # Maybe too aggressive?
        except OSError:
            pass

def main():
    if not os.path.exists(SRC):
        print(f"Source metadata dir not found: {SRC}")
        return
        
    for group in os.listdir(SRC):
        group_dir = os.path.join(SRC, group)
        if not os.path.isdir(group_dir): continue
        
        for pkg in os.listdir(group_dir):
            pkg_dir = os.path.join(group_dir, pkg)
            if not os.path.isdir(pkg_dir): continue
            
            convert_package(group, pkg, pkg_dir)

if __name__ == "__main__":
    main()
