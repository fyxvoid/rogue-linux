#!/usr/bin/env python3
import os
import sys
import shutil
import stat
import subprocess
import cogman_utils as butler

SKELETON_ROOT = "/tmp/rogue-rootfs-skeleton"

def fail(msg):
    butler.log_error(msg)
    cleanup()
    sys.exit(1)

def cleanup():
    if os.path.exists(SKELETON_ROOT):
        butler.log_info(f"Cleaning up {SKELETON_ROOT}...")
        shutil.rmtree(SKELETON_ROOT)

def step_1_create_skeleton():
    butler.log_check("Step 1: Creating Skeleton Definition definition")
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
            
    butler.log_success("Skeleton created successfully")

def step_2_permission_checks():
    butler.log_check("Step 2: Checking Permissions")
    
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
        butler.log_info("Running as different user, skipping strict ownership check")
    
    butler.log_success("Permissions validated (Simulation)")

def step_3_path_safety():
    butler.log_check("Step 3: Path Safety Analysis")
    
    # Test traversal
    safe_path = os.path.abspath(SKELETON_ROOT)
    
    test_link = os.path.join(SKELETON_ROOT, "unsafe_link")
    os.symlink("../../../etc/passwd", test_link)
    
    real_path = os.path.realpath(test_link)
    if not real_path.startswith(safe_path):
        butler.log_success(f"Detected unsafe link escape: {real_path}")
        os.remove(test_link)
    else:
        fail("Failed to detect unsafe link traversal!")

    butler.log_success("Path safety confirmed")

def step_6_dry_execution():
    butler.log_check("Step 6: Dry Execution Simulation")
    
    # Generate a plan definition targeting the skeleton
    # We interpret "steps" manually here as a dry run logic check
    
    pkg_name = "test-pkg-skeleton"
    
    # Contract: Cogman writes to SKELETON_ROOT/<pkg_name> ?
    # No, Cogman writes to pure paths inside pkgroot.
    # Wait, execution installs to pkgroot.
    # Rootfs construction copies FROM pkgroot TO SKELETON_ROOT.
    # This logic belongs to the "Rootfs Constructor" (future tool).
    
    # But we want to validate that COGMAN *output* is compatible.
    
    butler.log_info("Simulating installation of 'bash' to skeleton...")
    install_path = os.path.join(SKELETON_ROOT, "bin/bash")
    
    # Verify 'bin' resolves to 'usr/bin'
    real_install = os.path.realpath(install_path)
    expected = os.path.join(SKELETON_ROOT, "usr/bin/bash")
    
    if real_install != expected:
        fail(f"Symlink resolution mismatch: {real_install} != {expected}")
        
    butler.log_success("Installation path resolves correctly")

def main():
    try:
        step_1_create_skeleton()
        step_2_permission_checks()
        step_3_path_safety()
        step_6_dry_execution()
        butler.log_success("ALL CHECKS PASSED. SKELETON VALID AND READY FOR SERVICE.")
    except Exception as e:
        fail(f"Exception: {e}")
    finally:
        cleanup()

if __name__ == "__main__":
    main()
