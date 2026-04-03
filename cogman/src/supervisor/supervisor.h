/*
 * cogman/src/supervisor/supervisor.h - Global Supervisor State
 *
 * Declares the top-level supervisor struct and the three entry-points
 * called from the main loop and the SIGCHLD path.
 *
 * Why: Keeping all mutable supervisor state in one struct avoids hidden
 * globals and makes the coupling between modules explicit.
 */

#ifndef COGMAN_SUPERVISOR_H
#define COGMAN_SUPERVISOR_H

#include <sys/types.h>
#include "service.h"

/* ── Supervisor state ────────────────────────────────────────────────── */

struct supervisor {
    struct service  table[MAX_SERVICES];
    int             count;        /* number of valid entries in table[] */
    int             ctl_fd;       /* listening Unix-socket fd, or -1     */
    volatile int    running;      /* set to 0 to request shutdown        */
};

/* ── Global instance ─────────────────────────────────────────────────── */

extern struct supervisor g_sup;

/*
 * sup_handle_dead – process one dead child.
 * Called from the main loop after a SIGCHLD notification arrives on the
 * self-pipe.  pid is the result of waitpid(); status is the raw status
 * word from waitpid().
 *
 * Finds the service owning pid, updates its state, and schedules a
 * restart if the restart policy calls for one.
 */
void sup_handle_dead(pid_t pid, int status);

/*
 * sup_tick – called every main-loop iteration.
 * Scans the process table for services in SVC_RESTARTING state whose
 * restart_at deadline has passed and re-spawns them.
 */
void sup_tick(void);

/*
 * sup_start_ready – called every main-loop iteration.
 * Starts any service that is SVC_STOPPED and whose dependencies are all
 * SVC_RUNNING or SVC_DONE.
 */
void sup_start_ready(void);

#endif /* COGMAN_SUPERVISOR_H */
