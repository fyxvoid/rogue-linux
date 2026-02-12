import os
import re

missing_file_path = "/tmp/missing_system.txt"

if not os.path.exists(missing_file_path):
    print("Missing system file list not found.")
    exit(1)

with open(missing_file_path, 'r') as f:
    files = [line.strip() for line in f if line.strip()]

def fix_file(path):
    # Skip false positives
    if ".rustfmt.toml" in path or "pyproject.toml" in path or "alacritty.toml" in path:
        return
    
    if not os.path.exists(path):
        return
        
    with open(path, 'r') as f:
        content = f.read()
    
    if "system =" in content:
        return

    # Determine system type based on content
    system = "autotools"
    if "configure" not in content and "make" in content:
        system = "make"
    if "cmake" in content.lower():
        system = "cmake"
    if "ninja" in content.lower():
        system = "ninja"
    
    new_content = re.sub(r'\[build\]\n', f'[build]\nsystem = "{system}"\n', content)
    
    with open(path, 'w') as f:
        f.write(new_content)
    print(f"Fixed {path} with system={system}")

for f in files:
    fix_file(f)
