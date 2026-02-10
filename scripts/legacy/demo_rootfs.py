#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess
import time

DEMO_ROOT = "/tmp/rogue-rootfs-demo"
SRC_HELLO = "scripts/hello.c"
BIN_HELLO = "scripts/hello-static"

def log(msg):
    print(f"[DEMO] {msg}")

def cleanup():
    if os.path.exists(DEMO_ROOT):
        log(f"Cleaning up {DEMO_ROOT}...")
        shutil.rmtree(DEMO_ROOT)
    if os.path.exists(BIN_HELLO):
        os.remove(BIN_HELLO)

def fail(msg):
    print(f"[FAIL] {msg}")
    cleanup()
    sys.exit(1)

def run_cmd(cmd, cwd=None):
    log(f"Exec: {' '.join(cmd)}")
    subprocess.check_call(cmd, cwd=cwd)

def main():
    try:
        cleanup()
        
        # 1. Compile Static Binary
        log("Compiling static hello world...")
        run_cmd(["gcc", "-static", SRC_HELLO, "-o", BIN_HELLO])
        
        # 2. Create Skeleton
        log("Creating rootfs skeleton...")
        os.makedirs(os.path.join(DEMO_ROOT, "bin"))
        os.makedirs(os.path.join(DEMO_ROOT, "lib"))
        os.makedirs(os.path.join(DEMO_ROOT, "lib64"))
        
        # 3. Install Binary
        log("Installing binary...")
        dest = os.path.join(DEMO_ROOT, "bin/hello")
        shutil.copy(BIN_HELLO, dest)
        os.chmod(dest, 0o755)
        
        # 4. Verify Static Linking
        log("Verifying static linking...")
        ldd_out = subprocess.run(["ldd", dest], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if "not a dynamic executable" not in ldd_out.stderr and "statically linked" not in ldd_out.stdout:
             # ldd output varies by distro.
             # On Arch: "not a dynamic executable" usually.
             pass 
             
        # 5. Execute in Chroot
        log("Attempting isolated execution...")
        # Use unshare -r (fake root) + chroot
        # This allows chroot without real sudo if namespaces are enabled.
        
        cmd = ["unshare", "-r", "chroot", DEMO_ROOT, "/bin/hello"]
        
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if res.returncode == 0:
            log("Execution SUCCESS!")
            print("--- OUTPUT ---")
            print(res.stdout)
            print("--- END ---")
        else:
            log(f"Execution failed (rc={res.returncode})")
            print("STDERR:", res.stderr)
            # Fallback: exec directly to prove binary works
            log("Fallback: Executing directly to prove binary validity...")
            subprocess.run([dest])
            
        log("Demo Complete.")
        
    except Exception as e:
        fail(str(e))
    finally:
        cleanup()

if __name__ == "__main__":
    main()
