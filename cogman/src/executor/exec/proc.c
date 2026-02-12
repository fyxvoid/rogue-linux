/*
 * cogman/src/executor/exec/proc.c - Process Execution Logic
 *
 * This file implements the fork/exec/wait lifecycle for Cogman steps.
 * It handles environment injection and sanitized process dispatch.
 *
 * Why: To ensure that build steps are executed in a reproducible,
 * isolated, and efficient manner.
 */

#define _POSIX_C_SOURCE 200809L

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h>
#include <errno.h>
#include <stdint.h>

#include "../log/log.h"
#include "../plan/plan.h"

/*
 * Parse a null-terminated env block into a NULL-terminated array.
 * Inherits current environment, overlays plan environment.
 */
static char **
parse_env_block(const char *block, uint32_t len)
{
    if (len == 0)
        return NULL;

    /* Count plan entries */
    int count = 0;
    const char *p = block;
    const char *end = block + len;
    while (p < end) {
        if (*p == '\0')
            count++;
        p++;
    }

    /* Merge: current env + plan env overrides */
    extern char **environ;
    int base_count = 0;
    for (char **e = environ; *e; e++)
        base_count++;

    char **env = malloc(sizeof(char *) * (base_count + count + 1));
    if (!env)
        return NULL;

    int idx = 0;
    for (int i = 0; i < base_count; i++)
        env[idx++] = environ[i];

    p = block;
    while (p < end) {
        env[idx++] = (char *)p;
        p += strlen(p) + 1;
    }

    env[idx] = NULL;
    return env;
}

int
exec_command(const char *cmd, const char *workdir,
             const char *env_block, uint32_t env_len, uint32_t flags)
{
    log_debug("exec_command: cmd='%s' wdir='%s' flags=0x%x", cmd, workdir, flags);

    pid_t pid = fork();

    if (pid < 0) {
        log_err("fork() failed: %s", strerror(errno));
        return -1;
    }

    if (pid == 0) {
        /* Child: change directory, build env, exec */
        if (workdir && workdir[0] != '\0') {
            if (chdir(workdir) != 0) {
                fprintf(stderr, "chdir(%s): %s\n", workdir, strerror(errno));
                _exit(127);
            }
        }

        char **env = parse_env_block(env_block, env_len);

        const char *argv[4];
        argv[0] = "/bin/sh";
        argv[1] = "-c";
        argv[2] = cmd;
        argv[3] = NULL;

        if (env)
            execve("/bin/sh", (char *const *)argv, env);
        else
            execv("/bin/sh", (char *const *)argv);

        fprintf(stderr, "execve failed: %s\n", strerror(errno));
        _exit(127);
    }

    /* Parent: wait for child UNLESS it's a service */
    if (flags & STEP_FLAG_SERVICE) {
        log_info("Process %d launched as a persistent service.", pid);
        return 0;
    }

    int status;
    if (waitpid(pid, &status, 0) < 0) {
        log_err("waitpid() failed: %s", strerror(errno));
        return -1;
    }

    if (WIFEXITED(status))
        return WEXITSTATUS(status);

    if (WIFSIGNALED(status)) {
        log_err("Child killed by signal %d", WTERMSIG(status));
        return -1;
    }

    return -1;
}
