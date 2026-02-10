/*
 * cogmanII executor — proc.c
 * Process execution: fork + execve + waitpid.
 * Environment injection from plan step records.
 * Uses /bin/sh -c for command strings (plan encodes shell commands).
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h>
#include <errno.h>
#include <stdint.h>

/* Forward declarations from log.c */
extern void log_info(const char *fmt, ...);
extern void log_err(const char *fmt, ...);

/*
 * Parse a null-terminated env block "KEY=VAL\0KEY=VAL\0" into
 * a NULL-terminated array of strings for execve().
 * Caller must free the returned array (but not individual strings —
 * they point into the original block).
 */
static char **
parse_env_block(const char *block, uint32_t len)
{
    if (len == 0)
        return NULL;

    /* Count entries */
    int count = 0;
    const char *p = block;
    const char *end = block + len;
    while (p < end) {
        if (*p == '\0')
            count++;
        p++;
    }

    /* Build array: inherit current environment + plan env */
    extern char **environ;
    int base_count = 0;
    for (char **e = environ; *e; e++)
        base_count++;

    char **env = malloc(sizeof(char *) * (base_count + count + 1));
    if (!env)
        return NULL;

    int idx = 0;

    /* Copy base environment */
    for (int i = 0; i < base_count; i++)
        env[idx++] = environ[i];

    /* Append plan environment (overrides) */
    p = block;
    while (p < end) {
        env[idx++] = (char *)p;
        p += strlen(p) + 1;
    }

    env[idx] = NULL;
    return env;
}

/*
 * exec_command — fork and exec a shell command.
 * `cmd`: shell command string
 * `workdir`: chdir before exec
 * `env_block`: null-separated env pairs (may be NULL)
 * `env_len`: length of env block
 *
 * Returns: child exit status (0 = success), or -1 on fork/exec failure.
 */
int
exec_command(const char *cmd, const char *workdir,
             const char *env_block, uint32_t env_len)
{
    pid_t pid = fork();

    if (pid < 0) {
        log_err("fork() failed: %s", strerror(errno));
        return -1;
    }

    if (pid == 0) {
        /* Child process */

        /* Change working directory */
        if (workdir && workdir[0] != '\0') {
            if (chdir(workdir) != 0) {
                fprintf(stderr, "chdir(%s): %s\n", workdir, strerror(errno));
                _exit(127);
            }
        }

        /* Build environment */
        char **env = parse_env_block(env_block, env_len);

        /* Exec through /bin/sh -c */
        const char *argv[4];
        argv[0] = "/bin/sh";
        argv[1] = "-c";
        argv[2] = cmd;
        argv[3] = NULL;

        if (env) {
            execve("/bin/sh", (char *const *)argv, env);
        } else {
            execv("/bin/sh", (char *const *)argv);
        }

        /* execve failed */
        fprintf(stderr, "execve failed: %s\n", strerror(errno));
        _exit(127);
    }

    /* Parent: wait for child */
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
