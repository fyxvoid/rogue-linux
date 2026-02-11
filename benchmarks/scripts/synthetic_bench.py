#!/usr/bin/env python3
import os
import time
import subprocess
import shutil

# This script measures the "Overhead" of the Cogman system.
# It creates synthetic packages with deep dependencies and many steps
# to measure HOW FAST Cogman can think and act, regardless of the build itself.

WORKSPACE = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
PLANNER = os.path.join(WORKSPACE, "bin/cogman-planner")
EXECUTOR = os.path.join(WORKSPACE, "bin/cogman-executor")
TMP_BASE = "/tmp/cogman-bench"
PKG_ROOT = os.path.join(TMP_BASE, "packages")

def setup():
    if os.path.exists(TMP_BASE):
        shutil.rmtree(TMP_BASE)
    
    os.makedirs(os.path.join(PKG_ROOT, "bench"), exist_ok=True)
    
    # Create 5 synthetic packages with dependencies: pkg5 -> pkg4 -> pkg3 -> pkg2 -> pkg1
    for i in range(1, 6):
        pkg_dir = os.path.join(PKG_ROOT, "bench", f"pkg{i}")
        os.makedirs(pkg_dir, exist_ok=True)
        
        deps = f'build = ["bench/pkg{i-1}"]' if i > 1 else 'build = []'
        
        toml_content = f"""[identity]
name = "pkg{i}"
version = "1.0.0"
category = "bench"
summary = "Synthetic benchmark package {i}"

[identity.source]
kind = "tarball"
file = "dummy.tar.gz"

[identity.depends]
{deps}

[build]
system = "make"
steps = ["true", "echo Step 1", "echo Step 2"]

[installer]
steps = ["true"]
"""
        with open(os.path.join(pkg_dir, f"pkg{i}.toml"), "w") as f:
            f.write(toml_content)

def run_bench():
    print("▐ BENCHMARK ▌ Starting Synthetic Latency Test...")
    target_toml = os.path.join(PKG_ROOT, "bench/pkg5/pkg5.toml")
    plan_out = os.path.join(TMP_BASE, "bench.plan")

    # 1. Measurement: Planning Speed (5-Package Graph)
    # We run it multiple times and take the average
    plan_times = []
    for _ in range(5):
        start_plan = time.time()
        res = subprocess.run(
            [PLANNER, "build", target_toml, "--build", "-o", plan_out],
            capture_output=True, text=True
        )
        plan_times.append((time.time() - start_plan) * 1000)
    
    if res.returncode != 0:
        print(f"Planning Failed: {res.stderr}")
        return

    avg_plan = sum(plan_times) / len(plan_times)

    # 2. Measurement: Execution Dispatch Speed
    exec_times = []
    for _ in range(5):
        start_exec = time.time()
        res_exec = subprocess.run(
            [EXECUTOR, plan_out],
            capture_output=True, text=True
        )
        exec_times.append((time.time() - start_exec) * 1000)

    avg_exec = sum(exec_times) / len(exec_times)
    
    # 5 packages, 4 steps each + resolve overhead? 
    # Let's count steps in the plan.
    # Emitting plan (20 steps) - roughly 4 per package.
    total_steps = 20 

    print(f"\n▐ RESULTS ▌ Cogman Synthetic Performance:")
    print(f"  - Dependency Resolve & Plan (Avg): {avg_plan:.2f}ms")
    print(f"  - Executor Dispatch (20 Steps Avg): {avg_exec:.2f}ms")
    print(f"  - Dispatch Latency per Step: {avg_exec/total_steps:.2f}ms")
    print(f"  - Total System Overhead: {avg_plan + avg_exec:.2f}ms")

if __name__ == "__main__":
    setup()
    run_bench()
