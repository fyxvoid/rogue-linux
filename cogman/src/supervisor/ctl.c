/*
 * cogman/src/supervisor/ctl.c - Control Socket Implementation
 *
 * Implements a non-blocking Unix-domain socket listener that accepts
 * one-shot client connections, reads a single command, dispatches it
 * to the supervisor process table, and returns a text response.
 *
 * Protocol (newline-terminated text):
 *   Request:   "<verb> [<name>]\n"
 *   Response:  zero or more info lines, terminated by "OK\n" or "ERR <msg>\n"
 *
 * Why: A Unix socket gives cogman-ctl a simple, process-agnostic IPC
 * channel without pulling in D-Bus or any other framework.
 */

#define _POSIX_C_SOURCE 200809L

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/un.h>
#include <sys/types.h>

#include "ctl.h"
#include "supervisor.h"
#include "service.h"

/* ── Helpers ─────────────────────────────────────────────────────────── */

static int set_nonblocking(int fd)
{
    int flags = fcntl(fd, F_GETFL, 0);
    if (flags < 0) return -1;
    return fcntl(fd, F_SETFL, flags | O_NONBLOCK);
}


/* Write an entire buffer; retry on EINTR */
static void write_all(int fd, const char *buf, size_t len)
{
    size_t written = 0;
    while (written < len) {
        ssize_t r = write(fd, buf + written, len - written);
        if (r < 0) {
            if (errno == EINTR) continue;
            break;
        }
        written += (size_t)r;
    }
}



static void
send_str(int fd, const char *s)
{
    write_all(fd, s, strlen(s));
}



/* ── Command handlers ────────────────────────────────────────────────── */

/* Find a service by name; returns NULL if not found */
static struct service *
find_svc(const char *name)
{
    for (int i = 0; i < g_sup.count; i++)
        if (strcmp(g_sup.table[i].name, name) == 0)
            return &g_sup.table[i];
    return NULL;
}

static void
cmd_list(int fd)
{
    char line[256];
    for (int i = 0; i < g_sup.count; i++) {
        struct service *s = &g_sup.table[i];
        snprintf(line, sizeof(line), "%-24s  %-12s  pid=%-7d  restarts=%d\n",
                 s->name,
                 svc_state_str(s->state),
                 (int)s->pid,
                 s->restart_count);
        send_str(fd, line);
    }
    send_str(fd, "OK\n");
}

static void
cmd_status(int fd, const char *name)
{
    struct service *s = find_svc(name);
    if (!s) {
        char buf[128];
        snprintf(buf, sizeof(buf), "ERR unknown service '%s'\n", name);
        send_str(fd, buf);
        return;
    }
    char buf[512];
    snprintf(buf, sizeof(buf),
             "name:      %s\n"
             "state:     %s\n"
             "pid:       %d\n"
             "type:      %s\n"
             "restart:   %s\n"
             "restarts:  %d\n"
             "exit_code: %d\n",
             s->name,
             svc_state_str(s->state),
             (int)s->pid,
             (s->type == SVC_TYPE_ONESHOT  ? "oneshot"  :
              s->type == SVC_TYPE_FORKING  ? "forking"  : "process"),
             (s->restart == SVC_RESTART_ALWAYS     ? "always"     :
              s->restart == SVC_RESTART_ON_FAILURE ? "on-failure" : "never"),
             s->restart_count,
             s->exit_code);
    send_str(fd, buf);
    send_str(fd, "OK\n");
}

static void
cmd_start(int fd, const char *name)
{
    struct service *s = find_svc(name);
    if (!s) {
        char buf[128];
        snprintf(buf, sizeof(buf), "ERR unknown service '%s'\n", name);
        send_str(fd, buf);
        return;
    }
    if (s->state == SVC_RUNNING || s->state == SVC_STARTING) {
        send_str(fd, "ERR service already running\n");
        return;
    }
    if (!svc_deps_satisfied(s, g_sup.table, g_sup.count)) {
        send_str(fd, "ERR dependencies not yet satisfied\n");
        return;
    }
    if (svc_spawn(s) < 0) {
        send_str(fd, "ERR spawn failed\n");
        return;
    }
    send_str(fd, "OK\n");
}

static void
cmd_stop(int fd, const char *name)
{
    struct service *s = find_svc(name);
    if (!s) {
        char buf[128];
        snprintf(buf, sizeof(buf), "ERR unknown service '%s'\n", name);
        send_str(fd, buf);
        return;
    }
    if (s->state != SVC_RUNNING && s->state != SVC_STARTING &&
        s->state != SVC_RESTARTING) {
        send_str(fd, "ERR service is not running\n");
        return;
    }
    /* Temporarily set NEVER so SIGCHLD doesn't auto-restart during svc_stop.
     * The SVC_STOPPED state + started_at>0 guard in sup_start_ready() keeps
     * the service stopped after we restore the original policy. */
    svc_restart_t saved = s->restart;
    s->restart = SVC_RESTART_NEVER;
    int rc = svc_stop(s);
    s->restart = saved;           /* always restore original policy */
    if (rc < 0) {
        send_str(fd, "ERR stop failed\n");
        return;
    }
    send_str(fd, "OK\n");
}

static void
cmd_stop_all(int fd)
{
    int stopped = 0;
    for (int i = g_sup.count - 1; i >= 0; i--) {
        struct service *s = &g_sup.table[i];
        if (s->state == SVC_RUNNING || s->state == SVC_STARTING ||
            s->state == SVC_RESTARTING) {
            svc_restart_t saved = s->restart;
            s->restart = SVC_RESTART_NEVER;
            svc_stop(s);
            s->restart = saved;
            stopped++;
        }
    }
    char buf[64];
    snprintf(buf, sizeof(buf), "stopped %d service(s)\nOK\n", stopped);
    send_str(fd, buf);
}

static void
cmd_restart(int fd, const char *name)
{
    struct service *s = find_svc(name);
    if (!s) {
        char buf[128];
        snprintf(buf, sizeof(buf), "ERR unknown service '%s'\n", name);
        send_str(fd, buf);
        return;
    }

    /* Stop if running */
    if (s->state == SVC_RUNNING || s->state == SVC_STARTING ||
        s->state == SVC_RESTARTING) {
        svc_restart_t saved = s->restart;
        s->restart = SVC_RESTART_NEVER;
        svc_stop(s);
        s->restart = saved;
    }

    /* Spawn fresh */
    if (!svc_deps_satisfied(s, g_sup.table, g_sup.count)) {
        send_str(fd, "ERR dependencies not yet satisfied\n");
        return;
    }
    if (svc_spawn(s) < 0) {
        send_str(fd, "ERR spawn failed\n");
        return;
    }
    s->restart_count++;
    send_str(fd, "OK\n");
}

/* ── Dispatcher ──────────────────────────────────────────────────────── */

static void
dispatch(int fd, char *line)
{
    /* Strip trailing newline / carriage-return */
    size_t len = strlen(line);
    while (len > 0 && (line[len-1] == '\n' || line[len-1] == '\r'))
        line[--len] = '\0';

    if (len == 0) {
        send_str(fd, "ERR empty command\n");
        return;
    }

    /* Split into verb and optional argument */
    char *verb = line;
    char *arg  = NULL;
    char *sp   = strchr(line, ' ');
    if (sp) {
        *sp = '\0';
        arg = sp + 1;
        while (*arg == ' ') arg++; /* skip extra spaces */
    }

    if (strcmp(verb, "list") == 0) {
        cmd_list(fd);
    } else if (strcmp(verb, "status") == 0) {
        if (!arg || !*arg) { send_str(fd, "ERR usage: status <name>\n"); return; }
        cmd_status(fd, arg);
    } else if (strcmp(verb, "start") == 0) {
        if (!arg || !*arg) { send_str(fd, "ERR usage: start <name>\n"); return; }
        cmd_start(fd, arg);
    } else if (strcmp(verb, "stop") == 0) {
        if (!arg || !*arg) { send_str(fd, "ERR usage: stop <name>\n"); return; }
        cmd_stop(fd, arg);
    } else if (strcmp(verb, "restart") == 0) {
        if (!arg || !*arg) { send_str(fd, "ERR usage: restart <name>\n"); return; }
        cmd_restart(fd, arg);
    } else if (strcmp(verb, "stop-all") == 0) {
        cmd_stop_all(fd);
    } else {
        char buf[128];
        snprintf(buf, sizeof(buf), "ERR unknown command '%s'\n", verb);
        send_str(fd, buf);
    }
}

/* ── Public API ──────────────────────────────────────────────────────── */

int
ctl_init(void)
{
    /* Allow runtime override via environment variable */
    const char *sock_path = getenv("COGMAN_SUPERVISOR_SOCK");
    if (!sock_path || sock_path[0] == '\0')
        sock_path = CTL_SOCK_PATH;

    /* Remove any stale socket file */
    unlink(sock_path);

    int fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (fd < 0) {
        fprintf(stderr, "ctl_init: socket() failed: %s\n", strerror(errno));
        return -1;
    }

    struct sockaddr_un addr;
    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, sock_path, sizeof(addr.sun_path) - 1);

    if (bind(fd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        fprintf(stderr, "ctl_init: bind(%s) failed: %s\n",
                sock_path, strerror(errno));
        close(fd);
        return -1;
    }

    /* Let all users interact with the socket (init runs as root) */
    chmod(sock_path, 0666);

    if (listen(fd, 8) < 0) {
        fprintf(stderr, "ctl_init: listen() failed: %s\n", strerror(errno));
        close(fd);
        return -1;
    }

    if (set_nonblocking(fd) < 0) {
        fprintf(stderr, "ctl_init: fcntl(O_NONBLOCK) failed: %s\n",
                strerror(errno));
        close(fd);
        return -1;
    }

    fprintf(stderr, "ctl_init: listening on %s\n", sock_path);
    return fd;
}

void
ctl_accept(int server_fd)
{
    if (server_fd < 0)
        return;

    /* Accept (non-blocking; returns EAGAIN if nothing is pending) */
    int cfd = accept(server_fd, NULL, NULL);
    if (cfd < 0) {
        if (errno == EAGAIN || errno == EWOULDBLOCK)
            return;   /* nothing pending — normal */
        fprintf(stderr, "ctl_accept: accept() error: %s\n", strerror(errno));
        return;
    }

    /* Set a brief read timeout via SO_RCVTIMEO so we never block forever */
    struct timeval tv = { .tv_sec = 2, .tv_usec = 0 };
    setsockopt(cfd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));

    /* Read one line (up to CTL_CMD_MAX bytes) */
    char buf[CTL_CMD_MAX];
    ssize_t n = recv(cfd, buf, sizeof(buf) - 1, 0);
    if (n > 0) {
        buf[n] = '\0';
        dispatch(cfd, buf);
    } else {
        send_str(cfd, "ERR read error\n");
    }

    close(cfd);
}
