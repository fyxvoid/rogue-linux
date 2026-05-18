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
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
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

static void
record_installed(const char *name, const char *version)
{
    if (!name || !version)
        return;

    /* Ensure the directory exists */
    mkdir("/var/lib/cogman", 0755);

    /* Read existing entries, replacing any with the same name */
    char tmp_path[] = "/var/lib/cogman/installed.db.XXXXXX";
    int tmpfd = mkstemp(tmp_path);
    if (tmpfd < 0) {
        /* fallback: just append */
        FILE *f = fopen("/var/lib/cogman/installed.db", "a");
        if (f) { fprintf(f, "%s\t%s\n", name, version); fclose(f); }
        return;
    }
    FILE *tmp = fdopen(tmpfd, "w");
    if (!tmp) { close(tmpfd); unlink(tmp_path); return; }

    FILE *existing = fopen("/var/lib/cogman/installed.db", "r");
    int replaced = 0;
    if (existing) {
        char line[512];
        while (fgets(line, sizeof(line), existing)) {
            char *tab = strchr(line, '\t');
            if (tab && strncmp(line, name, (size_t)(tab - line)) == 0 &&
                (size_t)(tab - line) == strlen(name)) {
                fprintf(tmp, "%s\t%s\n", name, version);
                replaced = 1;
            } else {
                fputs(line, tmp);
            }
        }
        fclose(existing);
    }
    if (!replaced) fprintf(tmp, "%s\t%s\n", name, version);
    fclose(tmp);
    rename(tmp_path, "/var/lib/cogman/installed.db");
    log_info("Recorded package '%s' version '%s' in installed.db", name, version);
}

/*
 * Verify a .plan file against a minisig signature using the minisign CLI.
 * pubkey_file: path to the minisign public key (e.g. /etc/cogman/cogman.pub)
 * plan_path:   path to the .plan file
 * sig_path:    path to the .plan.minisig file (auto-derived if NULL)
 * Returns 0 on success, -1 on failure.
 */
static int
verify_plan_signature(const char *pubkey_file, const char *plan_path, const char *sig_path)
{
    char auto_sig[4096];
    if (!sig_path) {
        snprintf(auto_sig, sizeof(auto_sig), "%s.minisig", plan_path);
        sig_path = auto_sig;
    }

    /* Check both files exist before forking */
    if (access(pubkey_file, R_OK) != 0) {
        log_err("minisign pubkey not found: %s", pubkey_file);
        return -1;
    }
    if (access(sig_path, R_OK) != 0) {
        log_err("plan signature not found: %s (expected alongside plan file)", sig_path);
        return -1;
    }

    pid_t pid = fork();
    if (pid < 0) {
        log_err("fork() failed for minisign: %s", strerror(errno));
        return -1;
    }
    if (pid == 0) {
        /* Redirect stdout/stderr to /dev/null — minisign is verbose on success */
        int null_fd = open("/dev/null", O_WRONLY);
        if (null_fd >= 0) {
            dup2(null_fd, STDOUT_FILENO);
            dup2(null_fd, STDERR_FILENO);
            close(null_fd);
        }
        execlp("minisign", "minisign",
               "-V",
               "-p", pubkey_file,
               "-m", plan_path,
               "-x", sig_path,
               NULL);
        _exit(127);
    }

    int status;
    waitpid(pid, &status, 0);

    if (!WIFEXITED(status) || WEXITSTATUS(status) != 0) {
        log_err("minisign verification FAILED for %s", plan_path);
        log_err("  pubkey: %s", pubkey_file);
        log_err("  sigfile: %s", sig_path);
        return -1;
    }

    log_ok("Plan signature verified: %s", plan_path);
    return 0;
}

int
main(int argc, char **argv)
{
    if (argc < 2) {
        fprintf(stderr,
            "Usage: %s <plan-file> [--pkg-name <name>] [--pkg-version <ver>]\n"
            "                     [--pubkey <path>] [--sig <path>]\n",
            argv[0]);
        return 1;
    }

    const char *plan_path   = argv[1];
    const char *pkg_name    = NULL;
    const char *pkg_version = NULL;
    const char *pubkey_path = NULL;
    const char *sig_path    = NULL;

    for (int i = 2; i < argc - 1; i++) {
        if (strcmp(argv[i], "--pkg-name") == 0)
            pkg_name = argv[++i];
        else if (strcmp(argv[i], "--pkg-version") == 0)
            pkg_version = argv[++i];
        else if (strcmp(argv[i], "--pubkey") == 0)
            pubkey_path = argv[++i];
        else if (strcmp(argv[i], "--sig") == 0)
            sig_path = argv[++i];
    }

    /* Verify signature before executing anything */
    if (pubkey_path) {
        if (verify_plan_signature(pubkey_path, plan_path, sig_path) != 0) {
            log_err("Refusing to execute unsigned or tampered plan.");
            return 1;
        }
    } else {
        /* Check if default pubkey exists — warn but don't block (transition period) */
        const char *default_pubkey = "/etc/cogman/cogman.pub";
        if (access(default_pubkey, R_OK) == 0) {
            log_warn("Default pubkey found at %s but --pubkey not passed. "
                     "Pass --pubkey to enforce signature verification.", default_pubkey);
        }
    }
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

    /* Supervisor idle loop intentionally removed: cogman-supervisor owns that
     * role. The executor exits after all plan steps complete. */

    uint32_t step_count = hdr->step_count; // Store before unmap

    munmap(base, file_size);

    if (failed) {
        log_err("Execution aborted due to step failure");
        return 1;
    }

    log_ok("All %u steps executed successfully", step_count);
    record_installed(pkg_name, pkg_version);
    return 0;
}
