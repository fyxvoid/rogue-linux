/*
 * cogman/src/executor/main.c - The Heart of the Execution Engine
 *
 * This file serves as the core entry point for the Cogman Executor.
 * It handles logic for mapping binary plans into memory and
 * initiating the procedural execution loop.
 *
 * Why: To provide a minimalist, zero-parsing C runtime for
 * high-speed system deployment.
 */

#define _POSIX_C_SOURCE 200809L

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <signal.h>
#include <sys/wait.h>
#include <unistd.h>
#include <errno.h>

#include "plan/plan.h"
#include "log/log.h"
#include "exec/proc.h"
#include "fs/fs.h"
#include "verify/verify.h"
#include "messenger.h"

static volatile sig_atomic_t keep_running = 1;

/*
 * SIGCHLD handler: The Supervisor's "Ear to the Ground"
 */
static void
sigchld_handler(int sig)
{
    (void)sig;
    int status;
    pid_t pid;

    /* Reap all zombies */
    while ((pid = waitpid(-1, &status, WNOHANG)) > 0) {
        if (WIFEXITED(status)) {
            log_info("Process %d exited with status %d", pid, WEXITSTATUS(status));
        } else if (WIFSIGNALED(status)) {
            log_warn("Process %d killed by signal %d", pid, WTERMSIG(status));
        }
    }
}

static void
sigint_handler(int sig)
{
    (void)sig;
    log_warn("Termination signal received. Shutting down Supervisor.");
    keep_running = 0;
}

/*
 * Execute a single step record.
 * Returns 0 on success, -1 on failure.
 */
/*
 * Returns 1 if any path component is ".." (traversal attempt).
 * Walks each segment between slashes to detect bare ".." entries.
 */
static int
path_has_traversal(const char *path)
{
    const char *p = path;
    while (*p) {
        while (*p == '/') p++;          /* skip leading/repeated slashes */
        if (p[0] == '.' && p[1] == '.' &&
            (p[2] == '/' || p[2] == '\0'))
            return 1;
        while (*p && *p != '/') p++;    /* skip this component */
    }
    return 0;
}

static int
execute_step(const void *base, const struct plan_header *hdr,
             const struct step_record *step, uint32_t index)
{
    const char *cmd  = plan_str(base, hdr->strtab_offset, step->cmd_offset);
    const char *wdir = plan_str(base, hdr->strtab_offset, step->wdir_offset);
    const char *env  = NULL;
    uint32_t flags = step->flags;
    int rc = 0;

    if (step->env_len > 0)
        env = plan_str(base, hdr->strtab_offset, step->env_offset);

    const char *op_name = plan_op_name(step->op);
    log_info("Step %u/%u [%s]: %.60s%s",
             index + 1, hdr->step_count,
             op_name,
             cmd, (strlen(cmd) > 60 ? "..." : ""));

    log_debug("Step detail: op=%u policy=%u wdir='%s' env_len=%u",
              step->op, step->fail_policy, wdir, step->env_len);

    switch (step->op) {
    case OP_EXEC:
        rc = exec_command(cmd, wdir, env, step->env_len, flags);
        break;

    case OP_MKDIR:
        rc = mkdir_p(cmd);
        break;

    case OP_COPY: {
        /* Command format: "src|dst" */
        char *buf = strdup(cmd);
        if (!buf) {
            rc = -1;
            break;
        }
        char *sep = strchr(buf, '|');
        if (!sep) {
            log_err("COPY step missing '|' separator: %s", cmd);
            free(buf);
            rc = -1;
            break;
        }
        *sep = '\0';
        const char *src_path = buf;
        const char *dst_path = sep + 1;
        if (path_has_traversal(src_path) || path_has_traversal(dst_path)) {
            log_err("COPY step rejected: path traversal detected (src='%s' dst='%s')",
                    src_path, dst_path);
            free(buf);
            rc = -1;
            break;
        }
        rc = copy_recursive(src_path, dst_path);
        free(buf);
        break;
    }

    case OP_VERIFY:
        rc = verify_step(cmd);
        break;

    case OP_CLEANUP:
        rc = rm_rf(cmd);
        break;

    default:
        log_err("Unknown step opcode: %u", step->op);
        rc = -1;
        break;
    }

    if (rc != 0) {
        if (step->fail_policy == FAIL_ABORT) {
            log_err("Step %u FAILED (abort)", index + 1);
            return -1;
        } else {
            log_warn("Step %u failed (continuing)", index + 1);
            return 0;
        }
    }

    return 0;
}

int
main(int argc, char **argv)
{
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <plan-file>\n", argv[0]);
        return 1;
    }

    const char *plan_path = argv[1];
    size_t file_size;
    void *base = plan_open(plan_path, &file_size);

    if (!base)
        return 1;

    if (plan_validate(base, file_size) != 0) {
        munmap(base, file_size);
        return 1;
    }

    const struct plan_header *hdr = (const struct plan_header *)base;
    const char *variant = (hdr->variant == VARIANT_BINARY) ? "binary" : "native";

    /* 
     * In Binary mode (Rogue Core), we act as the Init/Supervisor.
     * Initialize the IPC broker and enter the persistent lifecycle loop.
     */
    if (hdr->variant == VARIANT_BINARY) {
        struct sigaction sa;
        memset(&sa, 0, sizeof(sa));
        sa.sa_handler = sigchld_handler;
        sigaction(SIGCHLD, &sa, NULL);

        sa.sa_handler = sigint_handler;
        sigaction(SIGINT, &sa, NULL);

        int ipc_fd = messenger_broker_init();
        (void)ipc_fd;

        log_ok("Supervisor mode active. Monitoring heartbeat.");
    }

    log_info("Executing %s plan with %u step(s)", variant, hdr->step_count);

    int failed = 0;
    for (uint32_t i = 0; i < hdr->step_count; i++) {
        const struct step_record *step = plan_step(base, i);
        if (execute_step(base, hdr, step, i) != 0) {
            failed = 1;
            break;
        }
    }

    if (hdr->variant == VARIANT_BINARY && !failed) {
        log_info("Startup phase complete. Entering Supervisor Idle.");
        while (keep_running) {
            pause(); /* Wait for signals (SIGCHLD, etc) */
        }
    }

    uint32_t step_count = hdr->step_count; // Store before unmap

    munmap(base, file_size);

    if (failed) {
        log_err("Execution aborted due to step failure");
        return 1;
    }

    log_ok("All %u steps executed successfully", step_count);
    return 0;
}
