/*
 * cogman/src/supervisor/service.c - Service Lifecycle Implementation
 *
 * Parses INI-like .service files, manages fork/exec/stop for each
 * service entry, and checks dependency satisfaction.
 *
 * Why: Isolating all service I/O and process management here keeps the
 * supervisor's main loop free of parsing clutter and makes each concern
 * independently testable.
 */

#define _POSIX_C_SOURCE 200809L

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <errno.h>
#include <unistd.h>
#include <signal.h>
#include <time.h>
#include <dirent.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <sys/stat.h>
#include <fcntl.h>

#include "service.h"

/* ── Internal helpers ────────────────────────────────────────────────── */

/* Trim leading and trailing whitespace in-place; returns pointer to result */
static char *
trim(char *s)
{
    while (*s == ' ' || *s == '\t' || *s == '\r') s++;
    char *end = s + strlen(s);
    while (end > s && (end[-1] == ' ' || end[-1] == '\t' ||
                       end[-1] == '\r' || end[-1] == '\n'))
        end--;
    *end = '\0';
    return s;
}

/* Parse a comma-separated list of dep names into svc->deps[] */
static void
parse_deps(struct service *svc, const char *val)
{
    char buf[MAX_NAME * MAX_DEPS];
    strncpy(buf, val, sizeof(buf) - 1);
    buf[sizeof(buf) - 1] = '\0';

    svc->ndeps = 0;
    char *tok = strtok(buf, ",");
    while (tok && svc->ndeps < MAX_DEPS) {
        char *t = trim(tok);
        if (*t) {
            strncpy(svc->deps[svc->ndeps], t, MAX_NAME - 1);
            svc->deps[svc->ndeps][MAX_NAME - 1] = '\0';
            svc->ndeps++;
        }
        tok = strtok(NULL, ",");
    }
}

/* ── svc_parse_file ──────────────────────────────────────────────────── */

int
svc_parse_file(struct service *svc, const char *path)
{
    FILE *f = fopen(path, "r");
    if (!f) {
        fprintf(stderr, "svc_parse_file: cannot open %s: %s\n",
                path, strerror(errno));
        return -1;
    }

    /* Zero-initialise; set defaults */
    memset(svc, 0, sizeof(*svc));
    svc->type          = SVC_TYPE_PROCESS;
    svc->restart       = SVC_RESTART_NEVER;
    svc->restart_delay = 1;
    svc->state         = SVC_STOPPED;
    svc->pid           = -1;

    /* Track which INI section we are currently in */
    enum { SEC_NONE, SEC_SERVICE, SEC_ENV } section = SEC_NONE;

    char line[1024];
    while (fgets(line, sizeof(line), f)) {
        char *l = trim(line);

        /* Skip blank lines and comments */
        if (*l == '\0' || *l == '#' || *l == ';')
            continue;

        /* Section header */
        if (*l == '[') {
            char *close = strchr(l, ']');
            if (close) *close = '\0';
            char *sec = trim(l + 1);
            if (strcasecmp(sec, "service") == 0)
                section = SEC_SERVICE;
            else if (strcasecmp(sec, "env") == 0)
                section = SEC_ENV;
            else
                section = SEC_NONE;
            continue;
        }

        /* Key = value */
        char *eq = strchr(l, '=');
        if (!eq)
            continue;
        *eq = '\0';
        char *key = trim(l);
        char *val = trim(eq + 1);

        if (section == SEC_SERVICE) {
            if (strcasecmp(key, "name") == 0) {
                strncpy(svc->name, val, MAX_NAME - 1);

            } else if (strcasecmp(key, "command") == 0) {
                strncpy(svc->command, val, MAX_CMD - 1);

            } else if (strcasecmp(key, "type") == 0) {
                if (strcasecmp(val, "oneshot") == 0)
                    svc->type = SVC_TYPE_ONESHOT;
                else if (strcasecmp(val, "forking") == 0)
                    svc->type = SVC_TYPE_FORKING;
                else
                    svc->type = SVC_TYPE_PROCESS;

            } else if (strcasecmp(key, "restart") == 0) {
                if (strcasecmp(val, "always") == 0)
                    svc->restart = SVC_RESTART_ALWAYS;
                else if (strcasecmp(val, "on-failure") == 0)
                    svc->restart = SVC_RESTART_ON_FAILURE;
                else
                    svc->restart = SVC_RESTART_NEVER;

            } else if (strcasecmp(key, "restart_delay") == 0) {
                svc->restart_delay = atoi(val);
                if (svc->restart_delay < 0)
                    svc->restart_delay = 1;

            } else if (strcasecmp(key, "depends") == 0) {
                parse_deps(svc, val);
            }

        } else if (section == SEC_ENV) {
            if (svc->nenv < MAX_ENV) {
                /* Store as "KEY=VALUE" */
                char entry[MAX_ENV_ENTRY];
                snprintf(entry, sizeof(entry), "%s=%s", key, val);
                snprintf(svc->env[svc->nenv], MAX_ENV_ENTRY, "%s", entry);
                svc->nenv++;
            }
        }
    }

    fclose(f);

    /* A service file must at least have a name and a command */
    if (svc->name[0] == '\0' || svc->command[0] == '\0') {
        fprintf(stderr, "svc_parse_file: %s: missing name or command\n", path);
        return -1;
    }

    return 0;
}

/* ── Cycle detection ─────────────────────────────────────────────────── */

/* DFS visitor — returns -1 if a cycle is found */
static int
dfs_visit(const struct service *table, int n, int i,
          unsigned char *color)
{
    color[i] = 1; /* gray — currently on DFS stack */
    for (int d = 0; d < table[i].ndeps; d++) {
        const char *dep_name = table[i].deps[d];
        int j = -1;
        for (int k = 0; k < n; k++) {
            if (strcmp(table[k].name, dep_name) == 0) { j = k; break; }
        }
        if (j < 0) continue; /* unknown dep — deps_satisfied will catch it */
        if (color[j] == 1) {
            fprintf(stderr,
                    "cogman: dependency cycle detected: '%s' -> '%s'\n",
                    table[i].name, table[j].name);
            return -1;
        }
        if (color[j] == 0 && dfs_visit(table, n, j, color) < 0)
            return -1;
    }
    color[i] = 2; /* black — fully visited */
    return 0;
}

/*
 * svc_check_cycles — scan the service table for dependency cycles.
 * Returns 0 if no cycles are found, -1 if any cycle is detected.
 * Logs the offending edge on stderr.
 */
int
svc_check_cycles(const struct service *table, int n)
{
    unsigned char color[MAX_SERVICES];
    memset(color, 0, sizeof(color));
    for (int i = 0; i < n; i++) {
        if (color[i] == 0 && dfs_visit(table, n, i, color) < 0)
            return -1;
    }
    return 0;
}

/* ── svc_load_dir ────────────────────────────────────────────────────── */

int
svc_load_dir(struct service *table, int max, const char *dir)
{
    DIR *d = opendir(dir);
    if (!d) {
        fprintf(stderr, "svc_load_dir: cannot open %s: %s\n",
                dir, strerror(errno));
        return -1;
    }

    int count = 0;
    struct dirent *ent;
    while ((ent = readdir(d)) != NULL) {
        if (ent->d_type != DT_REG && ent->d_type != DT_UNKNOWN)
            continue;

        /* Only process *.service files */
        const char *name = ent->d_name;
        size_t nlen = strlen(name);
        if (nlen < 8 || strcmp(name + nlen - 8, ".service") != 0)
            continue;

        if (count >= max) {
            fprintf(stderr, "svc_load_dir: service table full (max %d)\n", max);
            break;
        }

        /* Build full path */
        char path[512];
        snprintf(path, sizeof(path), "%s/%s", dir, name);

        if (svc_parse_file(&table[count], path) == 0) {
            fprintf(stderr, "svc_load_dir: loaded service '%s' from %s\n",
                    table[count].name, path);
            count++;
        }
    }

    closedir(d);
    return count;
}

/* ── svc_state_str ───────────────────────────────────────────────────── */

const char *
svc_state_str(svc_state_t s)
{
    switch (s) {
    case SVC_STOPPED:    return "stopped";
    case SVC_STARTING:   return "starting";
    case SVC_RUNNING:    return "running";
    case SVC_RESTARTING: return "restarting";
    case SVC_FAILED:     return "failed";
    case SVC_DONE:       return "done";
    default:             return "unknown";
    }
}

/* ── svc_spawn ───────────────────────────────────────────────────────── */

/*
 * Build a NULL-terminated envp[] that starts with the current
 * process environment and overlays the service-specific entries.
 * Caller must free() the returned pointer.
 */
static char **
build_envp(struct service *svc)
{
    extern char **environ;

    /* Count inherited vars */
    int base = 0;
    if (environ)
        for (char **e = environ; *e; e++)
            base++;

    int total = base + svc->nenv + 1;
    char **envp = malloc(sizeof(char *) * (size_t)total);
    if (!envp)
        return NULL;

    int idx = 0;
    /* Copy inherited environment, skipping keys overridden by service */
    for (int i = 0; i < base; i++) {
        int overridden = 0;
        for (int j = 0; j < svc->nenv; j++) {
            /* Compare just the key part (up to '=') */
            const char *base_key = environ[i];
            const char *svc_key  = svc->env[j];
            const char *be = strchr(base_key, '=');
            const char *se = strchr(svc_key,  '=');
            if (!be || !se) continue;
            size_t bklen = (size_t)(be - base_key);
            size_t sklen = (size_t)(se - svc_key);
            if (bklen == sklen &&
                strncmp(base_key, svc_key, bklen) == 0) {
                overridden = 1;
                break;
            }
        }
        if (!overridden)
            envp[idx++] = environ[i];
    }

    /* Overlay service-specific vars */
    for (int j = 0; j < svc->nenv; j++)
        envp[idx++] = svc->env[j];

    envp[idx] = NULL;
    return envp;
}

/*
 * Tokenise svc->command into argv[].  Handles up to 63 space-delimited
 * tokens.  Operates on a scratch buffer to avoid modifying svc->command.
 * Returns 0 on success, -1 if command is empty.
 */
static int
build_argv(struct service *svc, char *buf, size_t bufsz,
           char **argv, int max_args)
{
    snprintf(buf, bufsz, "%s", svc->command);

    int argc = 0;
    char *tok = strtok(buf, " \t");
    while (tok && argc < max_args - 1) {
        argv[argc++] = tok;
        tok = strtok(NULL, " \t");
    }
    argv[argc] = NULL;

    return (argc > 0) ? 0 : -1;
}

int
svc_spawn(struct service *svc)
{
    if (svc->command[0] == '\0') {
        fprintf(stderr, "svc_spawn: %s: empty command\n", svc->name);
        return -1;
    }

    svc->state = SVC_STARTING;

    pid_t pid = fork();
    if (pid < 0) {
        fprintf(stderr, "svc_spawn: fork() for %s failed: %s\n",
                svc->name, strerror(errno));
        svc->state = SVC_FAILED;
        return -1;
    }

    if (pid == 0) {
        /* ── Child ───────────────────────────────────────────── */

        /* Build argv */
        char cmdbuf[MAX_CMD];
        char *argv[64];
        if (build_argv(svc, cmdbuf, sizeof(cmdbuf), argv, 64) < 0) {
            fprintf(stderr, "[%s] empty command\n", svc->name);
            _exit(127);
        }

        /* Build envp */
        char **envp = build_envp(svc);
        if (!envp) {
            fprintf(stderr, "[%s] build_envp OOM\n", svc->name);
            _exit(127);
        }

        /* Reset all signal dispositions to default in the child */
        struct sigaction sa;
        memset(&sa, 0, sizeof(sa));
        sa.sa_handler = SIG_DFL;
        sigemptyset(&sa.sa_mask);
        for (int sig = 1; sig < 32; sig++)
            sigaction(sig, &sa, NULL);

        /* Redirect stdin from /dev/null */
        int null_fd = open("/dev/null", O_RDONLY);
        if (null_fd >= 0) {
            dup2(null_fd, STDIN_FILENO);
            close(null_fd);
        }

        /* Run via sh -c so PATH resolution, shell builtins, and
         * argument splitting all work correctly — same approach as
         * cogman-executor. */
        const char *sh_argv[4];
        sh_argv[0] = "/bin/sh";
        sh_argv[1] = "-c";
        sh_argv[2] = svc->command;
        sh_argv[3] = NULL;
        execve("/bin/sh", (char *const *)sh_argv, envp);
        fprintf(stderr, "[%s] execve(/bin/sh) failed: %s\n",
                svc->name, strerror(errno));
        _exit(127);
    }

    /* ── Parent ──────────────────────────────────────────────── */
    svc->pid        = pid;
    svc->state      = SVC_RUNNING;
    svc->started_at = time(NULL);
    svc->restart_at = 0;

    fprintf(stderr, "svc_spawn: started %s pid=%d\n", svc->name, pid);
    return 0;
}

/* ── svc_stop ────────────────────────────────────────────────────────── */

int
svc_stop(struct service *svc)
{
    if (svc->state != SVC_RUNNING && svc->state != SVC_STARTING &&
        svc->state != SVC_RESTARTING) {
        return -1;
    }

    /* If waiting to restart (no live PID), just cancel the restart */
    if (svc->state == SVC_RESTARTING && svc->pid <= 0) {
        svc->state      = SVC_STOPPED;
        svc->restart_at = 0;
        return 0;
    }

    if (svc->pid <= 0)
        return -1;

    /* Mark STOPPED before sending the signal so sup_handle_dead()
     * (called from the SIGCHLD path) does not restart this service. */
    svc->state = SVC_STOPPED;

    fprintf(stderr, "svc_stop: sending SIGTERM to %s pid=%d\n",
            svc->name, svc->pid);
    kill(svc->pid, SIGTERM);

    /* Poll for up to 3 seconds */
    for (int i = 0; i < 30; i++) {
        struct timespec ts = { 0, 100000000L }; /* 100 ms */
        nanosleep(&ts, NULL);

        int status;
        pid_t r = waitpid(svc->pid, &status, WNOHANG);
        if (r == svc->pid) {
            svc->exit_code = WIFEXITED(status) ? WEXITSTATUS(status) : -1;
            svc->pid   = -1;
            svc->state = SVC_STOPPED;
            return 0;
        }
    }

    /* Still alive: SIGKILL */
    fprintf(stderr, "svc_stop: SIGKILL to %s pid=%d\n", svc->name, svc->pid);
    kill(svc->pid, SIGKILL);

    int status;
    waitpid(svc->pid, &status, 0);
    svc->exit_code = WIFEXITED(status) ? WEXITSTATUS(status) : -1;
    svc->pid   = -1;
    svc->state = SVC_STOPPED;
    return 0;
}

/* ── svc_deps_satisfied ──────────────────────────────────────────────── */

int
svc_deps_satisfied(struct service *svc, struct service *table, int n)
{
    for (int i = 0; i < svc->ndeps; i++) {
        const char *dep = svc->deps[i];
        int found = 0;
        for (int j = 0; j < n; j++) {
            if (strcmp(table[j].name, dep) == 0) {
                found = 1;
                /* Oneshot deps must complete before dependents start */
                if (table[j].type == SVC_TYPE_ONESHOT) {
                    if (table[j].state != SVC_DONE)
                        return 0;
                } else {
                    if (table[j].state != SVC_RUNNING &&
                        table[j].state != SVC_DONE)
                        return 0;
                }
                break;
            }
        }
        /* If a dep is not in the table at all, treat as unsatisfied */
        if (!found)
            return 0;
    }
    return 1;
}
