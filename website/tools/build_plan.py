#!/usr/bin/env python3
import os
import shutil
import cogman_utils as butler

SRC_DIR = "website/src"
OUT_DIR = "website/public"

def ensure_dirs():
    if not os.path.exists(SRC_DIR):
        butler.log_error(f"Source directory {SRC_DIR} missing!")
        return False
    
    # Clean and Recreate Public
    if os.path.exists(OUT_DIR):
        shutil.rmtree(OUT_DIR)
    os.makedirs(OUT_DIR)
    
    # Copy Assets
    butler.log_info("Migrating assets to public domain...")
    shutil.copytree(f"{SRC_DIR}/assets", f"{OUT_DIR}/assets")
    return True

def load_partial(name):
    path = f"{SRC_DIR}/partials/{name}.html"
    if os.path.exists(path):
        with open(path, "r") as f:
            return f.read()
    return ""

def build_page(filename):
    butler.log_check(f"Compiling {filename}")
    
    with open(f"{SRC_DIR}/pages/{filename}", "r") as f:
        content = f.read()
    
    # Basic Front-Matter-ish extraction for title (custom naive parser)
    title = "Home"
    # If the page has specific title logic, we can add it here.
    # For now, we just inject the content into a layout if we had a master layout.
    # But our partials are meant to be injected INTO the page content in this simple design,
    # OR we wrap the page content.
    
    # Strategy: The pages currently contain full HTML.
    # We need to STRIP the static parts and replace them with partial tags if we were converting.
    # But since we moved full HTML files to pages/, we first need to convert them to templates.
    # Let's assume the conversion happened or we do it on the fly.
    
    # ACTUAL STRATEGY:
    # 1. Read the page (which is currently full HTML)
    # 2. Naively regex replace common blocks with partials? NO, that's flaky.
    # 3. We should have rewritten the pages as templates first. 
    #    Since I blindly moved them, I will write a "migrator" logic here for the first run,
    #    or just treat them as templates that NEED partials.
    
    # Let's rewrite the pages to utilize the partials properly.
    # I will write the "Template" version of index.html first.
    pass

def main():
    if not ensure_dirs(): return
    butler.log_success("Build system initialized. Proceeding to compilation phase.")
    # Implementation pending migration of pages
    
if __name__ == "__main__":
    main()
