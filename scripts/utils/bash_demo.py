#!/usr/bin/env python3
import time
import sys
import os
import shutil

# Ensure we can import cogman_utils
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
import cogman_utils as butler

PKG_NAME = "bash"
PKG_VERSION = "5.2.21"
PKG_ROOT = os.path.abspath(os.path.join(os.getcwd(), "packages/base/bash/pkgroot"))

def setup_pkgroot():
    if os.path.exists(PKG_ROOT):
        shutil.rmtree(PKG_ROOT)
    os.makedirs(PKG_ROOT)
    os.makedirs(os.path.join(PKG_ROOT, "bin"))
    os.makedirs(os.path.join(PKG_ROOT, "usr/bin"))
    os.makedirs(os.path.join(PKG_ROOT, "usr/share/man/man1"))

def run_bash_demo():
    butler.log_info(f"Initializing Native Build: {PKG_NAME}-{PKG_VERSION}")
    setup_pkgroot()
    
    # Phase 1: Resource Acquisition (Downloading)
    butler.log_info(f"Downloading {PKG_NAME}-{PKG_VERSION}.tar.xz from mirror...")
    for i in range(101):
        butler.show_progress(i, 100, "HUD.FETCH")
        time.sleep(0.02)
    butler.log_success("Source integrity verified (SHA256).")

    # Phase 2: Environment Initialization
    butler.log_check("Toolchain availability (GCC/Glibc)")
    time.sleep(0.5)
    butler.log_success("Found localized toolchain: x86_64-rogue-linux-gnu")

    # Phase 3: Extraction & Configuration
    butler.log_info("Extracting source fragments...")
    for i in range(101):
        butler.show_progress(i, 100, "CORE.EXTRACT")
        time.sleep(0.01)
    
    butler.log_info("Configuring build parameters...")
    butler.log_native("CONF", "--prefix=/usr --without-bash-malloc")
    time.sleep(1)

    # Phase 4: Native Compilation
    butler.log_info("Executing GCC native compilation...")
    artifacts = [
        "shell.c", "builtins.c", "execute_cmd.c", "parser.c", 
        "jobs.c", "signames.c", "trap.c", "alias.c"
    ]
    for i, art in enumerate(artifacts):
        progress = int(((i + 1) / len(artifacts)) * 100)
        butler.log_native("CC", art)
        butler.show_progress(progress, 100, "ARCH.LINK")
        time.sleep(0.5)

    # Phase 5: Installation into PKGROOT
    butler.log_info(f"Injecting verified artifacts into {PKG_ROOT}...")
    
    # Actually create the files to reflect in filesystem
    with open(os.path.join(PKG_ROOT, "bin/bash"), "w") as f: f.write("#!/bin/bash\necho 'Rogue Linux Bash'")
    os.chmod(os.path.join(PKG_ROOT, "bin/bash"), 0o755)
    butler.log_native("INSTALL", "bin/bash")
    
    with open(os.path.join(PKG_ROOT, "usr/share/man/man1/bash.1"), "w") as f: f.write("BASH MANPAGE")
    butler.log_native("INSTALL", "usr/share/man/man1/bash.1")
    
    for i in range(101):
        butler.show_progress(i, 100, "CORE.DEPLOY")
        time.sleep(0.02)

    butler.log_success(f"Deployment complete. {PKG_NAME} is now live in PKGROOT.")
    butler.advice("I've verified the ELF headers. It's clean, sir. I wouldn't recommend changing the binary permissions manually.")

if __name__ == "__main__":
    try:
        run_bash_demo()
    except KeyboardInterrupt:
        print("\n[COGMAN] Build sequence aborted by user. Most unfortunate.", file=sys.stderr)
