# Executor: The Tactical Execution Engine

The Executor (`cogman-exec`) is the low-level "Muscle" of Cogman. It is written in **C11** to achieve maximum performance and minimum dependency overhead.

## ⚡ High-Speed Execution (mmap)

Traditional build systems parse scripts (Bash, Python) at runtime, leading to interpreter overhead and string manipulation latency. Cogman eliminates this entirely.

1.  **Zero-Parsing Header**: The executor maps the `.plan` file directly into its address space.
2.  **Struct Casting**: It treats the mapped memory as an array of `struct PlanStep`. There is no loop through a parser—just a loop through memory addresses.
3.  **Kernel-Level Efficiency**: Since the file is mapped, the kernel handles page loading and caching. If the same plan is run multiple times, it never touches the disk after the first page-in.

## 🛡️ Process Lifecycle & Isolation

For every step in the plan, the Executor follows a strict fork-join model:

```c
// Simplified Execution Loop
for (uint32_t i = 0; i < plan->step_count; i++) {
    const struct PlanStep *step = &plan->steps[i];
    
    pid_t pid = fork();
    if (pid == 0) { // Child
        configure_environment(step->env_offset);
        chdir(get_string(step->workdir_offset));
        execvp(get_string(step->cmd_offset), get_args(step->args_offset));
        exit(127); // Fail if exec failed
    }
    
    int status;
    waitpid(pid, &status, 0);
    if (WEXITSTATUS(status) != 0) {
        handle_failure(step, i); // Triggers Advisor and aborts
    }
}
```

## 🏗️ Performance & Rationale

| Feature | Implementation | Benefit |
| :--- | :--- | :--- |
| **Memory Allocation** | Zero (Static buffer/mmap) | No heap fragmentation, predictable performance. |
| **Logic Core** | `switch(step->opcode)` | Single-branch performance, minimal CPU cache misses. |
| **Binary Footprint** | ~50KB (Dynamic) / ~300KB (Static) | Fits in any rootfs, including minimal initramfs. |

## 🛠️ Contributor Onboarding: Hacking the Executor

The Executor is kept "dumb" by design. If you find yourself writing complex logic or string manipulation in the C code, **stop**. That logic belongs in the Rust Planner. The Executor should only know how to call syscalls based on integers.

**Key Files**:
- `executor/main.c`: Entry point and `mmap` setup.
- `executor/exec.c`: The core `switch(op)` loop.
- `executor/log/log.c`: The Butler personality implementation.
