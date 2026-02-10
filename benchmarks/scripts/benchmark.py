#!/usr/bin/env python3
import os
import sys
import time
import subprocess
import shutil
import csv
from pathlib import Path

# Configuration
TEST_PACKAGES = ["toybox", "zlib", "bash"]
ITERATIONS = 3
TMP_ROOT = "/tmp/cogman-test"
RESULTS_FILE = "benchmark_results.csv"

# Paths
# Paths
WORKSPACE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COGMAN_LEGACY = os.path.join(WORKSPACE, "archived/cogman-python")
COGMAN_ROOT = os.path.join(WORKSPACE, "cogman")
COGMAN_PLANNER = os.path.join(COGMAN_ROOT, "planner/target/debug/cogman-planner")
COGMAN_EXECUTOR = os.path.join(COGMAN_ROOT, "executor/cogman-exec")

def run_cmd(cmd, cwd=None, env=None, shell=False):
    """Run command and return (returncode, stdout, stderr, time_taken, peak_mem)"""
    start_time = time.time()
    
    # Just run the command directly
    full_cmd = (cmd if isinstance(cmd, list) else cmd.split())
    
    try:
        p = subprocess.run(
            full_cmd,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=shell
        )
        end_time = time.time()
        
        # We can't easily get peak mem without /usr/bin/time or complex wrapping
        peak_mem_kb = 0
        
        return p.returncode, p.stdout, p.stderr, end_time - start_time, peak_mem_kb
    except Exception as e:
        return -1, "", str(e), 0, 0

def setup_env():
    if os.path.exists(TMP_ROOT):
        # Handle permission issues with sudo if needed, but try simple rm first
        try:
            shutil.rmtree(TMP_ROOT)
        except:
            subprocess.run(["rm", "-rf", TMP_ROOT])
    os.makedirs(TMP_ROOT)
    
    with open(RESULTS_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["System", "Package", "Variant", "Iteration", "PlannerTime", "ExecTime", "TotalTime", "PeakMemKB", "Status"])

def benchmark_cogman(pkg, iteration, writer):
    # System 1: Cogman (Python) - Build only
    print(f"Benchmarking cogman [build] {pkg} iter {iteration}...")
    
    pkg_dir = os.path.join(TMP_ROOT, "cogman", pkg)
    os.makedirs(pkg_dir, exist_ok=True)
    
    env = os.environ.copy()
    env["PKGROOT"] = os.path.join(pkg_dir, "root")
    # cogmen.py expects packages dir relative to CWD
    
    cmd = ["python3", "cogmen.py", "build", pkg]
    
    # Run from root of workspace where 'cogman' folder is?
    # No, run from cogman dir so it finds 'packages'
    # Run from archived dir
    rc, _, err, duration, mem = run_cmd(cmd, cwd=COGMAN_LEGACY, env=env)
    
    status = "SUCCESS" if rc == 0 else "FAIL"
    writer.writerow(["cogman-legacy", pkg, "build", iteration, 0, duration, duration, mem, status])
    if rc != 0: print(f"FAILED: {err[:200]}")

def benchmark_cogman_current(pkg, variant, iteration, writer):
    # System 2: Cogman (Rust/C)
    print(f"Benchmarking cogman [{variant}] {pkg} iter {iteration}...")
    
    plan_file = os.path.join(TMP_ROOT, f"{pkg}-{variant}.plan")
    
    # PLAN
    # Search in categories
    toml_path = None
    for cat in ["base", "system", "toolchain"]:
        candidate = os.path.join(WORKSPACE, f"packages/{cat}/{pkg}/{pkg}.toml")
        if os.path.exists(candidate):
            toml_path = candidate
            break
    
    if not toml_path:
        # Fallback to absolute if it was already one, or just fail
        toml_path = os.path.join(WORKSPACE, f"packages/base/{pkg}/{pkg}.toml")
    
    # Needs to output to a temp rootfs to avoid /mnt/rogue issues
    rootfs = os.path.join(TMP_ROOT, "cogman")
    
    args = ["build", toml_path, "-o", plan_file, "--rootfs", rootfs]
    if variant == "build":
        args.append("--build")
    elif variant == "native":
        args += ["--build", "--native"]

        
    cmd_plan = [COGMAN_PLANNER] + args
    rc_p, _, err_p, time_p, mem_p = run_cmd(cmd_plan)
    
    if rc_p != 0:
        print(f"Plan FAILED: {err_p[:200]}")
        writer.writerow(["cogman", pkg, variant, iteration, time_p, 0, time_p, mem_p, "PLAN_FAIL"])
        return

    # EXEC
    # Ensure C executor can run (needs to find headers/libs? No, it's static-ish)
    cmd_exec = [COGMAN_EXECUTOR, plan_file]
    rc_e, _, err_e, time_e, mem_e = run_cmd(cmd_exec)
    
    status = "SUCCESS" if rc_e == 0 else "EXEC_FAIL"
    writer.writerow(["cogman", pkg, variant, iteration, time_p, time_e, time_p + time_e, max(mem_p, mem_e), status])
    if rc_e != 0: print(f"Exec FAILED: {err_e}")

def benchmark_arch(pkg, iteration, writer):
    # System 3: Arch (Pacman) - Binary reference
    print(f"Benchmarking arch [binary] {pkg} iter {iteration}...")
    
    tmp_root = os.path.join(TMP_ROOT, "arch", pkg)
    tmp_db = os.path.join(tmp_root, "var/lib/pacman")
    os.makedirs(tmp_db, exist_ok=True)
    
    # Pacman usually needs root. Check if we can run without.
    # If not, skip or mock.
    # Attempt: pacman -Sdf --root <tmp> --dbpath <tmp_db> --noconfirm <pkg>
    # Note: 'S' operation might require sync. 'U' requires file.
    # We'll skip actual pacman run if we aren't root, to avoid permissions errors cluttering results.
    if os.geteuid() != 0:
        # Just log a placeholder or skipped
        writer.writerow(["arch", pkg, "binary", iteration, 0, 0, 0, 0, "SKIPPED_NON_ROOT"])
        return

    cmd = ["pacman", "-S", "--root", tmp_root, "--dbpath", tmp_db, "--noconfirm", "--cachedir", "/tmp", pkg]
    rc, _, _, duration, mem = run_cmd(cmd)
    
    status = "SUCCESS" if rc == 0 else "FAIL"
    writer.writerow(["arch", pkg, "binary", iteration, 0, duration, duration, mem, status])

def main():
    setup_env()
    
    with open(RESULTS_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        
        for iteration in range(1, ITERATIONS + 1):
            for pkg in TEST_PACKAGES:
                benchmark_cogman(pkg, iteration, writer)
                benchmark_cogman_current(pkg, "build", iteration, writer)
                benchmark_cogman_current(pkg, "native", iteration, writer)
                benchmark_arch(pkg, iteration, writer)

if __name__ == "__main__":
    main()
