/*
 * cogman/src/supervisor/service.h - Service Definition Structures
 *
 * Defines the service table entry, enums for state/type/restart policy,
 * and all service lifecycle function prototypes.
 *
 * Why: A clean, self-contained data model for the supervisor's process
 * table allows the main loop, signal handling, and control socket to
 * operate without sharing mutable global state carelessly.
 */

#ifndef COGMAN_SERVICE_H
#define COGMAN_SERVICE_H

#include <sys/types.h>
#include <time.h>

/* ── Compile-time limits ─────────────────────────────────────────────── */
#define MAX_SERVICES    64
#define MAX_NAME        64
#define MAX_CMD         512
#define MAX_DEPS        8
#define MAX_ENV         32
#define MAX_ENV_ENTRY   512   /* length of one "KEY=VALUE" string */

/* ── Enumerations ────────────────────────────────────────────────────── */

/* How the process model works once launched */
typedef enum {
    SVC_TYPE_PROCESS  = 0,   /* long-running; supervisor tracks this PID  */
    SVC_TYPE_ONESHOT  = 1,   /* run once; never restarted                  */
    SVC_TYPE_FORKING  = 2    /* parent exits, child becomes the daemon     */
} svc_type_t;

/* When to restart after a crash / exit */
typedef enum {
    SVC_RESTART_NEVER      = 0,
    SVC_RESTART_ON_FAILURE = 1,
    SVC_RESTART_ALWAYS     = 2
} svc_restart_t;

/* Observable lifecycle state */
typedef enum {
    SVC_STOPPED    = 0,   /* initial / cleanly stopped         */
    SVC_STARTING   = 1,   /* fork called, exec pending         */
    SVC_RUNNING    = 2,   /* exec confirmed (pid is live)      */
    SVC_RESTARTING = 3,   /* waiting for restart_at to elapse  */
    SVC_FAILED     = 4,   /* died, restart policy = never      */
    SVC_DONE       = 5    /* oneshot completed successfully     */
} svc_state_t;

/* ── Service record ──────────────────────────────────────────────────── */

struct service {
    /* ── Static (parsed from .service file) ─────────────────────────── */
    char          name[MAX_NAME];
    char          command[MAX_CMD];
    svc_type_t    type;
    svc_restart_t restart;
    int           restart_delay;   /* seconds; default 1 */

    char          deps[MAX_DEPS][MAX_NAME];
    int           ndeps;

    char          env[MAX_ENV][MAX_ENV_ENTRY];   /* "KEY=VALUE" strings */
    int           nenv;

    /* ── Runtime ─────────────────────────────────────────────────────── */
    svc_state_t   state;
    pid_t         pid;
    time_t        started_at;
    time_t        restart_at;   /* epoch; restart after this time */
    int           exit_code;
    int           restart_count;
};

/* ── Function prototypes ─────────────────────────────────────────────── */

/*
 * svc_load_dir – scan dir for *.service files, parse each into table[].
 * Returns number of services loaded, or -1 on hard error.
 */
int svc_load_dir(struct service *table, int max, const char *dir);

/*
 * svc_parse_file – parse a single .service file into *svc.
 * Returns 0 on success, -1 on error.
 */
int svc_parse_file(struct service *svc, const char *path);

/* svc_state_str – human-readable state label */
const char *svc_state_str(svc_state_t s);

/*
 * svc_spawn – fork/exec svc->command in svc->env environment.
 * Sets svc->pid, svc->state = SVC_RUNNING, svc->started_at.
 * Returns 0 on success, -1 on failure.
 */
int svc_spawn(struct service *svc);

/*
 * svc_stop – send SIGTERM; if still alive after 3 s, send SIGKILL.
 * Sets svc->state = SVC_STOPPED.
 * Returns 0, or -1 if the service was not running.
 */
int svc_stop(struct service *svc);

/*
 * svc_deps_satisfied – returns 1 if every dep in svc->deps[] is
 * SVC_RUNNING or SVC_DONE in table[0..n-1], else 0.
 */
int svc_deps_satisfied(struct service *svc,
                       struct service *table, int n);

#endif /* COGMAN_SERVICE_H */
