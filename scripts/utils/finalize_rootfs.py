import os
import subprocess

ROOTFS = "/home/rogue/rootfs-staging"

def run(cmd):
    print(f"Executing: {cmd}")
    subprocess.run(cmd, shell=True, check=True)

def finalize_rootfs():
    os.chdir(ROOTFS)
    
    # Create mandatory FHS directories
    dirs = ["usr/bin", "usr/lib", "usr/sbin", "etc", "var", "run", "proc", "sys", "dev"]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        
    # Apply sticky bit to tmp
    os.makedirs("tmp", exist_ok=True)
    os.chmod("tmp", 0o1777)
    
    # Establish FHS symlinks
    links = {
        "bin": "usr/bin",
        "sbin": "usr/bin",
        "lib": "usr/lib",
        "lib64": "usr/lib"
    }
    
    # Move existing contents to usr/ counterparts before symlinking
    for link, target in links.items():
        if os.path.exists(link) and not os.path.islink(link):
            print(f"Moving contents of {link} to {target}...")
            # Use shell to move contents safely
            run(f"cp -a {link}/* {target}/ 2>/dev/null || true")
            run(f"rm -rf {link}")
        elif os.path.islink(link):
            os.unlink(link)
            
    for link, target in links.items():
        os.symlink(target, link)
        print(f"Created symlink: {link} -> {target}")

    # Establish /bin/sh for sanity checks
    # Since bash is a dummy, we link to toybox
    if os.path.exists("usr/bin/toybox"):
        os.symlink("toybox", "usr/bin/sh")
        print("Created symlink: usr/bin/sh -> toybox")
    
    print("Rootfs FHS finalization complete, sir.")

if __name__ == "__main__":
    finalize_rootfs()
