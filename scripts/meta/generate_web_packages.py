#!/usr/bin/env python3
import os
import cogman_utils as butler

MANIFEST = "pkg_manifest.txt"
MANFIEST = "pkg_manifest.txt"
# Fragment Template
TEMPLATE = """<!-- title: Packages -->

<div class="hero main-hero" style="min-height: 40vh;">
    <h1 class="glitch" data-text="ARSENAL">ARSENAL</h1>
    <p>Curated tools for digital warfare.</p>
</div>

<section style="padding: 2rem 10%; max-width: 1400px; margin: 0 auto;">
    <input type="text" class="search-bar" placeholder="SEARCH PACKAGE DATABASE..." onkeyup="filterPkgs()">
    
    <ul class="pkg-list" id="pkgList">
        {pkg_list}
    </ul>
</section>

<script>
    function filterPkgs() {{
        let input = document.querySelector('.search-bar');
        let filter = input.value.toUpperCase();
        let ul = document.getElementById("pkgList");
        let li = ul.getElementsByTagName("li");
        for (let i = 0; i < li.length; i++) {{
            let name = li[i].getElementsByClassName("pkg-name")[0];
            if (name.innerHTML.toUpperCase().indexOf(filter) > -1) {{
                li[i].style.display = "";
            }} else {{
                li[i].style.display = "none";
            }}
        }}
    }}
</script>
"""

def generate():
    if not os.path.exists(MANIFEST):
        butler.log_error(f"Manifest not found at {MANIFEST}")
        return

    butler.log_info(f"Generating package catalog fragment from {MANIFEST}...")
    
    with open(MANIFEST, "r") as f:
        lines = f.readlines()

    pkg_items = ""
    count = 0
    for line in lines:
        line = line.strip()
        if not line: continue
        parts = line.split("|")
        if len(parts) >= 2:
            name = parts[0]
            ver = parts[1]
            pkg_items += f'<li class="pkg-item"><span class="pkg-name">{name}</span><span class="pkg-ver">v{ver}</span></li>\n'
            count += 1

    html = TEMPLATE.format(pkg_list=pkg_items)
    
    out_path = "website/src/pages/packages.html"
    with open(out_path, "w") as f:
        f.write(html)
        
    butler.log_success(f"Generated {out_path} with {count} packages.")

if __name__ == "__main__":
    generate()
