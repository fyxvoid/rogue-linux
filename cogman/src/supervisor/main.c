/*
 * cogman/src/supervisor/main.c - cogman-supervisor Entry Point
 *
 * PID-1-capable init/supervisor for Rogue Linux.
 * Architecture: kernel → cogman-supervisor (init) → wm → apps
 *
 * Signal handling strategy:
 *   SIGCHLD is caught; the handler writes the dead child's pid_t into a
 *   self-pipe.  The main loop reads from the read-end of that pipe and
 *   calls sup_handle_dead() — all complex work happens in non-signal
 *   context, preserving async-signal-safety.
 *
 * Why: A self-pipe makes SIGCHLD composable with the select/poll/sleep
 * main-loop model without requiring signalfd (which is Linux-specific
 * and non-portable to a future musl-only environment).
 */

#define _POSIX_C_SOURCE 200809L

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <signal.h>
#include <fcntl.h>
#include <time.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <sys/select.h>
#include <sys/stat.h>
#include <sys/time.h>

#include "service.h"
#include "supervisor.h"
#include "ctl.h"

/* ── Global supervisor instance ─────────────────────────────────────── */

struct supervisor g_sup;

/* ── Self-pipe for SIGCHLD ───────────────────────────────────────────── */

/*
 * g_sigchld_pipe[0] = read end (main loop)
 * g_sigchld_pipe[1] = write end (signal handler)
 */
static int g_sigchld_pipe[2] = { -1, -1 };

/*
 * SIGCHLD handler — async-signal-safe.
 * Writes a single byte to g_sigchld_pipe[1] to wake the main loop.
 * We do NOT call waitpid() here; that happens in drain_sigchld_pipe().
 */
static void
sigchld_handler(int sig)
{
    (void)sig;
    /* write() is async-signal-safe; ignore errors (pipe full = already notified) */
    char byte = 1;
    write(g_sigchld_pipe[1], &byte, 1);
}

/*
 * SIGTERM / SIGINT handler — async-signal-safe.
 */
static void
sigterm_handler(int sig)
{
    (void)sig;
    g_sup.running = 0;
}

/* ── SIGCHLD pipe drainer ────────────────────────────────────────────── */

/*
 * Called from the main loop when the pipe has data.
 * Drains all pending bytes from the read end, then reaps all dead
 * children via waitpid(WNOHANG).
 */
static void
drain_sigchld_pipe(void)
{
    /* Drain the pipe (may have multiple bytes for multiple children) */
    char buf[64];
    while (read(g_sigchld_pipe[0], buf, sizeof(buf)) > 0)
        ; /* intentionally empty */

    /* Reap every dead child */
    for (;;) {
        int status;
        pid_t pid = waitpid(-1, &status, WNOHANG);
        if (pid <= 0)
            break;
        sup_handle_dead(pid, status);
    }
}

/* ── Supervisor body functions ───────────────────────────────────────── */

/*
 * sup_handle_dead — update the owning service's state after a child exits.
 */
void
sup_handle_dead(pid_t pid, int status)
{
    struct service *svc = NULL;
    for (int i = 0; i < g_sup.count; i++) {
        if (g_sup.table[i].pid == pid) {
            svc = &g_sup.table[i];
            break;
        }
    }

    if (!svc) {
        /* Orphan reap — common for zombie cleanup as PID 1 */
        fprintf(stderr, "sup: reaped orphan pid=%d\n", pid);
        return;
    }

    int exit_code = 0;
    if (WIFEXITED(status))
        exit_code = WEXITSTATUS(status);
    else if (WIFSIGNALED(status))
        exit_code = -WTERMSIG(status);

    svc->exit_code = exit_code;
    svc->pid       = -1;

    fprintf(stderr, "sup: service '%s' pid=%d exited, code=%d\n",
            svc->name, (int)pid, exit_code);

    /* Oneshot completion */
    if (svc->type == SVC_TYPE_ONESHOT) {
        svc->state = (exit_code == 0) ? SVC_DONE : SVC_FAILED;
        return;
    }

    /* Forking: parent exits intentionally — treat as DONE */
    if (svc->type == SVC_TYPE_FORKING) {
        svc->state = SVC_DONE;
        return;
    }

    /* If the service was explicitly stopped, honour that — no restart. */
    if (svc->state == SVC_STOPPED) {
        fprintf(stderr, "sup: '%s' was stopped explicitly, not restarting\n",
                svc->name);
        return;
    }

    /* type == PROCESS: apply restart policy */
    int should_restart = 0;
    switch (svc->restart) {
    case SVC_RESTART_ALWAYS:
        should_restart = 1;
        break;
    case SVC_RESTART_ON_FAILURE:
        should_restart = (exit_code != 0);
        break;
    case SVC_RESTART_NEVER:
    default:
        should_restart = 0;
        break;
    }

    if (should_restart) {
        svc->state      = SVC_RESTARTING;
        svc->restart_at = time(NULL) + svc->restart_delay;
        fprintf(stderr, "sup: will restart '%s' in %ds\n",
                svc->name, svc->restart_delay);
    } else {
        svc->state = (exit_code == 0) ? SVC_STOPPED : SVC_FAILED;
    }
}

/*
 * sup_tick — respawn services whose restart_at deadline has passed.
 */
void sup_tick(void)
{
    time_t now = time(NULL);
    for (int i = 0; i < g_sup.count; i++) {
        struct service *s = &g_sup.table[i];
        if (s->state != SVC_RESTARTING)
            continue;
        if (now >= s->restart_at) {
            fprintf(stderr, "sup: restarting '%s' (attempt %d)\n",
                    s->name, s->restart_count + 1);
            if (svc_spawn(s) == 0)
                s->restart_count++;
            else
                s->state = SVC_FAILED;
        }
    }
}

/*
 * sup_start_ready — start every service that has never been started
 * (started_at == 0) and whose dependencies are satisfied.
 * Services that were explicitly stopped (started_at > 0, state == SVC_STOPPED)
 * are left alone — they require an explicit `start` command to restart.
 */
void
sup_start_ready(void)
{
    for (int i = 0; i < g_sup.count; i++) {
        struct service *s = &g_sup.table[i];
        if (s->state != SVC_STOPPED)
            continue;
        /* Only auto-start services that haven't been started yet */
        if (s->started_at != 0)
            continue;
        if (!svc_deps_satisfied(s, g_sup.table, g_sup.count))
            continue;
        fprintf(stderr, "sup: starting '%s'\n", s->name);
        if (svc_spawn(s) < 0)
            s->state = SVC_FAILED;
    }
}

/* ── Signal setup ────────────────────────────────────────────────────── */

static int
setup_signals(void)
{
    /* Create self-pipe */
    if (pipe(g_sigchld_pipe) < 0) {
        perror("pipe");
        return -1;
    }

    /* Make both ends non-blocking */
    for (int i = 0; i < 2; i++) {
        int flags = fcntl(g_sigchld_pipe[i], F_GETFL, 0);
        if (flags < 0 || fcntl(g_sigchld_pipe[i], F_SETFL, flags | O_NONBLOCK) < 0) {
            perror("fcntl pipe nonblock");
            return -1;
        }
        /* Set FD_CLOEXEC so child processes don't inherit the pipe */
        if (fcntl(g_sigchld_pipe[i], F_SETFD, FD_CLOEXEC) < 0) {
            perror("fcntl pipe cloexec");
            return -1;
        }
    }

    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sigemptyset(&sa.sa_mask);

    /* SIGCHLD: write to self-pipe */
    sa.sa_handler = sigchld_handler;
    sa.sa_flags   = SA_RESTART | SA_NOCLDSTOP;
    if (sigaction(SIGCHLD, &sa, NULL) < 0) {
        perror("sigaction SIGCHLD");
        return -1;
    }

    /* SIGTERM / SIGINT: set running = 0 */
    sa.sa_handler = sigterm_handler;
    sa.sa_flags   = SA_RESTART;
    if (sigaction(SIGTERM, &sa, NULL) < 0) {
        perror("sigaction SIGTERM");
        return -1;
    }
    if (sigaction(SIGINT, &sa, NULL) < 0) {
        perror("sigaction SIGINT");
        return -1;
    }

    /* Ignore SIGPIPE — broken control socket connections must not crash us */
    sa.sa_handler = SIG_IGN;
    sa.sa_flags   = 0;
    sigaction(SIGPIPE, &sa, NULL);

    return 0;
}

/* ── Usage / argument parsing ────────────────────────────────────────── */

static void
usage(const char *prog)
{
    fprintf(stderr,
            "Usage: %s [options]\n"
            "  --services-dir <path>   directory containing *.service files\n"
            "                          (default: /etc/cogman/services)\n"
            "  --no-ctl                disable control socket\n"
            "  --help                  show this message\n",
            prog);
}

/* ── Main ────────────────────────────────────────────────────────────── */

int
main(int argc, char **argv)
{
    const char *services_dir = "/etc/cogman/services";
    int no_ctl = 0;

    /* ── Parse arguments ─────────────────────────────────────────────── */
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--services-dir") == 0) {
            if (i + 1 >= argc) {
                fprintf(stderr, "error: --services-dir requires an argument\n");
                return 1;
            }
            services_dir = argv[++i];
        } else if (strcmp(argv[i], "--no-ctl") == 0) {
            no_ctl = 1;
        } else if (strcmp(argv[i], "--help") == 0 ||
                   strcmp(argv[i], "-h") == 0) {
            usage(argv[0]);
            return 0;
        } else {
            fprintf(stderr, "error: unknown argument '%s'\n", argv[i]);
            usage(argv[0]);
            return 1;
        }
    }

    fprintf(stderr, "cogman-supervisor starting (pid=%d)\n", (int)getpid());

    /* ── Initialise global state ─────────────────────────────────────── */
    memset(&g_sup, 0, sizeof(g_sup));
    g_sup.ctl_fd  = -1;
    g_sup.running = 1;

    /* ── Load service definitions ────────────────────────────────────── */
    int n = svc_load_dir(g_sup.table, MAX_SERVICES, services_dir);
    if (n < 0) {
        fprintf(stderr, "warning: could not load services from %s\n",
                services_dir);
        n = 0;
    }
    g_sup.count = n;

    if (svc_check_cycles(g_sup.table, g_sup.count) < 0) {
        fprintf(stderr, "cogman-supervisor: aborting — dependency cycle in service definitions\n");
        return 1;
    }

    fprintf(stderr, "cogman-supervisor: loaded %d service(s)\n", n);

    /* ── Set up signal handlers ──────────────────────────────────────── */
    if (setup_signals() < 0) {
        fprintf(stderr, "fatal: signal setup failed\n");
        return 1;
    }

    /* ── Initialise control socket ───────────────────────────────────── */
    if (!no_ctl) {
        g_sup.ctl_fd = ctl_init();
        if (g_sup.ctl_fd < 0)
            fprintf(stderr, "warning: control socket unavailable\n");
    }

    /* ── Start initial services (those with no dependencies) ─────────── */
    sup_start_ready();

    /* ── Main loop ───────────────────────────────────────────────────── */
    struct timespec sleep_ts = { 0, 100000000L };   /* 100 ms */

    while (g_sup.running) {
        /* 1. Drain SIGCHLD pipe and reap dead children */
        {
            fd_set rfds;
            FD_ZERO(&rfds);
            FD_SET(g_sigchld_pipe[0], &rfds);

            /* Non-blocking poll of the read end */
            struct timeval tv = { 0, 0 };
            if (select(g_sigchld_pipe[0] + 1, &rfds, NULL, NULL, &tv) > 0)
                drain_sigchld_pipe();
        }

        /* 2. Accept and dispatch one control command (non-blocking) */
        ctl_accept(g_sup.ctl_fd);

        /* 3. Respawn services whose restart timer has elapsed */
        sup_tick();

        /* 4. Start any service whose dependencies just became satisfied */
        sup_start_ready();

        /* 4b. Check for pending reload (written by cmd_reload) */
        {
            struct stat st;
            if (stat("/run/cogman/reload-pending", &st) == 0) {
                unlink("/run/cogman/reload-pending");
                fprintf(stderr, "cogman-supervisor: reloading (re-exec)\n");
                /* Close control socket before re-exec */
                if (g_sup.ctl_fd >= 0) {
                    close(g_sup.ctl_fd);
                    unlink(CTL_SOCK_PATH);
                    g_sup.ctl_fd = -1;
                }
                /* Re-exec self — children keep running */
                extern char **environ;
                execve("/proc/self/exe", argv, environ);
                perror("reload: execve failed");
                /* If execve fails, continue normally */
                g_sup.ctl_fd = ctl_init();
            }
        }

        /* 5. As PID 1, reap any orphaned processes (zombie prevention) */
        {
            int status;
            pid_t p;
            while ((p = waitpid(-1, &status, WNOHANG)) > 0)
                sup_handle_dead(p, status);
        }

        /* 6. Sleep 100 ms before next iteration */
        nanosleep(&sleep_ts, NULL);
    }

    /* ── Shutdown: stop all running services ─────────────────────────── */
    fprintf(stderr, "cogman-supervisor: shutting down\n");
    for (int i = 0; i < g_sup.count; i++) {
        struct service *s = &g_sup.table[i];
        if (s->state == SVC_RUNNING || s->state == SVC_STARTING) {
            fprintf(stderr, "  stopping %s\n", s->name);
            svc_restart_t saved = s->restart;
            s->restart = SVC_RESTART_NEVER;
            svc_stop(s);
            s->restart = saved;
        }
    }

    /* Clean up control socket */
    if (g_sup.ctl_fd >= 0) {
        close(g_sup.ctl_fd);
        unlink(CTL_SOCK_PATH);
    }

    fprintf(stderr, "cogman-supervisor: exit\n");
    return 0;
}
