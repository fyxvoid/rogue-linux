#!/usr/bin/env python3
import os
import sys
import shutil
import stat
import subprocess

SKELETON_ROOT = "/tmp/rogue-rootfs-skeleton"

def log(msg, status="INFO"):
    print(f"[{status}] {msg}")

def fail(msg):
    log(msg, "FAIL")
    cleanup()
    sys.exit(1)

def cleanup():
    if os.path.exists(SKELETON_ROOT):
        log(f"Cleaning up {SKELETON_ROOT}...", "CLEAN")
        shutil.rmtree(SKELETON_ROOT)

def step_1_create_skeleton():
    log("Step 1: Creating Skeleton Definition...", "STEP")
    if os.path.exists(SKELETON_ROOT):
        shutil.rmtree(SKELETON_ROOT)
    os.makedirs(SKELETON_ROOT)
    
    # Standard FHS Layout
    dirs = [
        "etc", "var", "tmp", "run",
        "usr/bin", "usr/lib", "usr/share",
        "boot", "dev", "proc", "sys", "home", "root"
    ]
    
    for d in dirs:
        path = os.path.join(SKELETON_ROOT, d)
        os.makedirs(path, exist_ok=True)
        
    # Symlinks
    links = {
        "bin": "usr/bin",
        "sbin": "usr/bin", # Arch style
        "lib": "usr/lib",
        "lib64": "usr/lib"
    }
    
    for link, target in links.items():
        link_path = os.path.join(SKELETON_ROOT, link)
        if not os.path.exists(link_path):
            os.symlink(target, link_path)
            
    log("Skeleton created successfully.")

def step_2_permission_checks():
    log("Step 2: Checking Permissions...", "STEP")
    
    # Verify /tmp is sticky
    tmp_path = os.path.join(SKELETON_ROOT, "tmp")
    os.chmod(tmp_path, 0o1777)
    
    st = os.stat(tmp_path)
    if not (st.st_mode & stat.S_ISVTX):
        fail("/tmp missing sticky bit")
        
    # Verify root ownership (simulated: python running as user)
    # We can't chown to root if we are not root.
    # We just check we own it.
    uid = os.getuid()
    if st.st_uid != uid:
        log("Running as different user, skipping strict ownership check.", "WARN")
    
    log("Permissions validated (Simulation).")

def step_3_path_safety():
    log("Step 3: Path Safety Analysis...", "STEP")
    
    # Test traversal
    safe_path = os.path.abspath(SKELETON_ROOT)
    
    test_link = os.path.join(SKELETON_ROOT, "unsafe_link")
    os.symlink("../../../etc/passwd", test_link)
    
    real_path = os.path.realpath(test_link)
    if not real_path.startswith(safe_path):
        log(f"Detected unsafe link escape: {real_path}", "PASS")
        os.remove(test_link)
    else:
        fail("Failed to detect unsafe link traversal!")

    log("Path safety confirmed.")

def step_6_dry_execution():
    log("Step 6: Dry Execution Simulation...", "STEP")
    
    # Generate a plan definition targeting the skeleton
    # We interpret "steps" manually here as a dry run logic check
    
    pkg_name = "test-pkg-skeleton"
    
    # Contract: Cogman writes to SKELETON_ROOT/<pkg_name> ?
    # No, Cogman writes to pure paths inside pkgroot.
    # Wait, execution installs to pkgroot.
    # Rootfs construction copies FROM pkgroot TO SKELETON_ROOT.
    # This logic belongs to the "Rootfs Constructor" (future tool).
    
    # But we want to validate that COGMAN *output* is compatible.
    
    log("Simulating installation of 'bash' to skeleton...")
    install_path = os.path.join(SKELETON_ROOT, "bin/bash")
    
    # Verify 'bin' resolves to 'usr/bin'
    real_install = os.path.realpath(install_path)
    expected = os.path.join(SKELETON_ROOT, "usr/bin/bash")
    
    if real_install != expected:
        fail(f"Symlink resolution mismatch: {real_install} != {expected}")
        
    log("Installation path resolves correctly.")

def main():
    try:
        step_1_create_skeleton()
        step_2_permission_checks()
        step_3_path_safety()
        step_6_dry_execution()
        log("ALL CHECKS PASSED. SKELETON VALID.", "SUCCESS")
    except Exception as e:
        fail(f"Exception: {e}")
    finally:
        cleanup()

if __name__ == "__main__":
    main()
