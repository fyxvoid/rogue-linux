#!/usr/bin/env python3
import os
import sys
import subprocess
import time
import cogman_utils as butler

# CONFIGURATION
# Best general mirrors for standardized names
MIRRORS = [
    "http://anduin.linuxfromscratch.org/LFS/{file}",
    "https://distfiles.gentoo.org/distfiles/{file}",
    "https://ftp.gnu.org/gnu/{name}/{file}",
    "https://sources.buildroot.net/{name}/{file}",
    "https://www.kernel.org/pub/linux/utils/{name}/{file}",
    "https://www.kernel.org/pub/linux/kernel/v6.x/{file}",
    "https://www.kernel.org/pub/linux/kernel/v5.x/{file}",
    "https://www.kernel.org/pub/linux/libs/pam/library/{file}",
    "https://github.com/{name}/{name}/releases/download/v{version}/{file}",
    "https://github.com/{name}/{name}/archive/refs/tags/v{version}.tar.gz",
]

GITHUB_MAPPING = {
    "fd": "sharkdp/fd",
    "ripgrep": "BurntSushi/ripgrep",
    "bat": "sharkdp/bat",
    "exa": "ogham/exa",
    "hyperfine": "sharkdp/hyperfine",
    "zoxide": "ajeetdsouza/zoxide",
    "bottom": "ClementTsang/bottom",
    "procs": "dalance/procs",
    "tokei": "XAMPPRocky/tokei",
    "ncdu": "rofl0r/ncdu",
    "dust": "bootandy/dust",
    "starship": "starship/starship",
    "lsd": "Peltoche/lsd",
    "zellij": "zellij-org/zellij",
    "mawk": "invisible-island.net/mawk", # Special case, not github but often missed
    "neovim": "neovim/neovim",
    "helix": "helix-editor/helix",
    "kakoune": "mawww/kakoune",
    "micro": "zyedidia/micro",
}

URL_OVERRIDES = {
    "zip": "https://downloads.sourceforge.net/infozip/zip30.tar.gz",
    "unzip": "https://downloads.sourceforge.net/infozip/unzip60.tar.gz",
    "docbook-xml": "https://www.docbook.org/xml/4.5/docbook-xml-4.5.zip",
    "mpfr": "https://www.mpfr.org/mpfr-{version}/{file}",
    "gmp": "https://gmplib.org/download/gmp/{file}",
    "expat": "https://github.com/libexpat/libexpat/releases/download/R_{version_underscore}/{file}",
    "openrc": "https://github.com/OpenRC/openrc/archive/0.54.tar.gz",
    "libelf": "https://sourceware.org/elfutils/ftp/0.191/elfutils-0.191.tar.bz2",
    "man-pages": "https://www.kernel.org/pub/linux/docs/man-pages/man-pages-6.06.tar.xz",
    "psmisc": "https://sourceforge.net/projects/psmisc/files/psmisc/psmisc-23.7.tar.xz",
    "man-db": "http://download.savannah.nongnu.org/releases/man-db/man-db-2.12.0.tar.xz",
    "kmod": "https://www.kernel.org/pub/linux/utils/kernel/kmod/kmod-32.tar.xz",
    "toilet": "http://caca.zoy.org/files/toilet/toilet-0.3.tar.gz",
    "sysvinit": "https://github.com/sysvinit/sysvinit/releases/download/3.08/sysvinit-3.08.tar.xz",
}

MANIFEST = "pkg_manifest.txt"
LOG = "download_results.log"

def download_pkg(name, version, filename, pkg_path):
    dest_dir = os.path.join(pkg_path, "tar")
    dest_file = os.path.join(dest_dir, filename)

    if os.path.exists(dest_file):
        butler.log_info(f"It appears {name} already possesses {filename}")
        return True

    os.makedirs(dest_dir, exist_ok=True)
    
    butler.log_info(f"Attempting to procure {filename} for the {name} package")
    
    # Extensions to try if the main one fails
    # We will try to download these, and if successful, RENAME them to 'filename'
    # This allows the rest of the build system (which expects 'filename') to work
    # assuming 'tar' can auto-detect the format.
    extensions_to_try = []
    
    base_name = filename
    for ext in [".tar.xz", ".tar.gz", ".tgz", ".tar.bz2", ".zip"]:
        if filename.endswith(ext):
            base_name = filename[:-len(ext)]
            break
            
    extensions_to_try.append(filename)
    
    # Add fallbacks
    variations = [".tar.gz", ".tgz", ".tar.bz2", ".zip", ".tar.xz"]
    for ext in variations:
        new_name = base_name + ext
        if new_name != filename:
            extensions_to_try.append(new_name)

    # Check for direct URL override
    if name in URL_OVERRIDES:
        url = URL_OVERRIDES[name]
        # Handle version underscore for expat
        version_underscore = version.replace(".", "_")
        url = url.format(name=name, version=version, version_underscore=version_underscore, file=filename)
        
        # If url ends with a specific extension, we should probably respect it for the download
        # but the logic below iterates extensions.
        # Let's just try the override URL directly first.
        butler.log_check(f"override URL {url}")
        cmd = ["curl", "-L", "-f", "--connect-timeout", "10", "-o", dest_file, url]
        rc = subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if rc == 0:
            butler.log_success(f"Successfully acquired {filename} via override")
            return True

    for try_filename in extensions_to_try:
        # Check mirrors for this filename
        for mirror in MIRRORS:
            # Check if we have a special mapping for this package on GitHub
            safe_name = name
            current_url = ""
            
            if "github.com" in mirror and name in GITHUB_MAPPING:
                # If the mirror is the generic github one:
                if "{name}/{name}" in mirror:
                     user_repo = GITHUB_MAPPING[name] # e.g. sharkdp/fd
                     current_url = mirror.replace("{name}/{name}", user_repo).format(version=version, file=try_filename)
                else:
                     current_url = mirror.format(name=name, version=version, file=try_filename)
            elif "sourceforge" in mirror:
                 # SF needs special handling often, but let's try standard layout
                 current_url = mirror.format(name=name, version=version, file=try_filename)
            else:
                current_url = mirror.format(name=name, version=version, file=try_filename)
            
            butler.log_check(f"mirror: {current_url}")
            
            # Download to a temp file first to avoid partials matching "dest_file" if we rename later
            temp_dest = dest_file + ".tmp"
            
            cmd = ["curl", "-L", "-f", "--connect-timeout", "10", "-o", temp_dest, current_url]
            rc = subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            if rc == 0:
                butler.log_success(f"Successfully acquired {try_filename} from {current_url}")
                # Rename to dest_file (the expected filename)
                os.rename(temp_dest, dest_file)
                return True
            
            if os.path.exists(temp_dest):
                os.remove(temp_dest)

    butler.log_error(f"I regret to inform you that {filename} (and its variations) could not be located on any known mirror")
    return False

def main():
    if not os.path.exists(MANIFEST):
        butler.log_error(f"I cannot seem to locate the manifest at {MANIFEST}")
        return

    with open(MANIFEST, "r") as f:
        lines = f.readlines()

    success_count = 0
    fail_count = 0
    failures = []

    for line in lines:
        line = line.strip()
        if not line: continue
        
        # Format: name|version|file|path
        parts = line.split("|")
        if len(parts) != 4: continue
        
        name, version, filename, pkg_path = parts
        
        if download_pkg(name, version, filename, pkg_path):
            success_count += 1
        else:
            fail_count += 1
            failures.append(f"{name}|{filename}")

    # Report
    summary = f"\nDOWNLOAD SUMMARY:\n- Success: {success_count}\n- Failures: {fail_count}\n"
    print(summary)
    
    with open(LOG, "w") as f:
        f.write(summary)
        if failures:
            f.write("\nFAILED PACKAGES:\n")
            for f_pkg in failures:
                f.write(f"- {f_pkg}\n")

if __name__ == "__main__":
    main()
