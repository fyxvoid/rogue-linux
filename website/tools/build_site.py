#!/usr/bin/env python3
import os
import shutil
import re
import sys

# Allow importing from scripts/ directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../scripts")))
import cogman_utils as butler

SRC_DIR = "website/src"
OUT_DIR = "website/public"
PAGES_DIR = f"{SRC_DIR}/pages"
PARTIALS_DIR = f"{SRC_DIR}/partials"

def load_partial(name):
    path = f"{PARTIALS_DIR}/{name}.html"
    if os.path.exists(path):
        with open(path, "r") as f:
            return f.read()
    return ""

def build():
    # 1. Setup
    if os.path.exists(OUT_DIR):
        shutil.rmtree(OUT_DIR)
    os.makedirs(OUT_DIR)
    
    # 2. Assets
    butler.log_info("Deploying holographic assets...")
    shutil.copytree(f"{SRC_DIR}/assets", f"{OUT_DIR}/assets")

    # 3. Load Partials
    head_tmpl = load_partial("head")
    nav = load_partial("nav")
    footer = load_partial("footer")

    # 4. Process Pages
    for filename in os.listdir(PAGES_DIR):
        if not filename.endswith(".html"): continue
        
        butler.log_check(f"Compiling fragment: {filename}")
        
        with open(f"{PAGES_DIR}/{filename}", "r") as f:
            content = f.read()
            
        # Metadata Extraction (Simple comment parsing)
        # Format: <!-- title: My Title -->
        title = "Rogue Linux"
        title_match = re.search(r'<!--\s*title:\s*(.*?)\s*-->', content)
        if title_match:
            title = f"Rogue Linux | {title_match.group(1)}"
        
        # Inject title into head
        page_head = head_tmpl.replace("{title}", title)
        
        # Assembly
        full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    {page_head}
</head>
<body>
    {nav}
    <main>
        {content}
    </main>
    {footer}
</body>
</html>"""

        with open(f"{OUT_DIR}/{filename}", "w") as f:
            f.write(full_html)

    butler.log_success("Holographic interface compilation complete.")

if __name__ == "__main__":
    build()
