import os
import re

files = [
    "packages/toolchain/mpc/mpc.toml",
    "packages/toolchain/bison/bison.toml",
    "packages/toolchain/mpfr/mpfr.toml",
    "packages/toolchain/gmp/gmp.toml",
    "packages/toolchain/m4/m4.toml",
    "packages/toolchain/make/make.toml",
    "packages/toolchain/flex/flex.toml",
    "packages/toolchain/libstdc++/libstdc++.toml",
    "packages/toolchain/libtool/libtool.toml",
    "packages/toolchain/cmake/cmake.toml",
    "packages/toolchain/gettext/gettext.toml",
    "packages/toolchain/bc/bc.toml",
    "packages/toolchain/texinfo/texinfo.toml",
    "packages/toolchain/patch/patch.toml",
    "packages/toolchain/pkg-config/pkg-config.toml",
    "packages/toolchain/ninja/ninja.toml",
    "packages/toolchain/perl/perl.toml"
]

def fix_file(path):
    if not os.path.exists(path):
        return
    with open(path, 'r') as f:
        content = f.read()
    
    # Use regex to find the identity.depends section and its build list
    # We want to remove "toolchain/gcc" from that list.
    
    # Pattern to match: build = [ ... "toolchain/gcc" ... ]
    # We'll use a more robust approach: find the build = [...] line and remove the element.
    
    pattern = r'(build\s*=\s*\[)(.*?)(\])'
    
    def remove_gcc(match):
        prefix = match.group(1)
        elements_str = match.group(2)
        suffix = match.group(3)
        
        # Split elements, strip, remove gcc, rejoin
        elements = [e.strip() for e in elements_str.split(',') if e.strip()]
        new_elements = [e for e in elements if "toolchain/gcc" not in e]
        
        return f"{prefix}{', '.join(new_elements)}{suffix}"

    new_content = re.sub(pattern, remove_gcc, content)
    
    if new_content != content:
        with open(path, 'w') as f:
            f.write(new_content)
        print(f"Fixed {path}: removed toolchain/gcc")
    else:
        print(f"No changes for {path}")

for f in files:
    fix_file(f)
