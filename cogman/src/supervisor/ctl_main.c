/*
 * cogman/src/supervisor/ctl_main.c - cogman-ctl Client Binary
 *
 * Connects to /run/cogman-supervisor.sock, sends a single command
 * constructed from argv[], prints the response to stdout, and exits
 * with 0 on "OK" or 1 on "ERR".
 *
 * Usage:
 *   cogman-ctl list
 *   cogman-ctl status <name>
 *   cogman-ctl start  <name>
 *   cogman-ctl stop   <name>
 *   cogman-ctl restart <name>
 *
 * Why: A thin client binary lets shell scripts and users inspect and
 * control the supervisor without linking against any supervisor library.
 */

#define _POSIX_C_SOURCE 200809L

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/un.h>

#include "ctl.h"   /* CTL_SOCK_PATH */

static void
usage(const char *prog)
{
    fprintf(stderr,
            "Usage: %s <command> [args...]\n"
            "Commands:\n"
            "  list               list all services\n"
            "  status <name>      show status of a service\n"
            "  start  <name>      start a stopped service\n"
            "  stop   <name>      stop a running service\n"
            "  restart <name>     restart a service\n",
            prog);
}

int
main(int argc, char **argv)
{
    if (argc < 2) {
        usage(argv[0]);
        return 1;
    }

    /* ── Build the command string from argv[1..] ─────────────────────── */
    char cmd[512];
    int pos = 0;
    for (int i = 1; i < argc; i++) {
        int written = snprintf(cmd + pos, sizeof(cmd) - (size_t)pos - 2,
                               "%s%s", (i > 1 ? " " : ""), argv[i]);
        if (written < 0 || pos + written >= (int)sizeof(cmd) - 2) {
            fprintf(stderr, "cogman-ctl: command too long\n");
            return 1;
        }
        pos += written;
    }
    /* Append newline as the protocol delimiter */
    cmd[pos++] = '\n';
    cmd[pos]   = '\0';

    /* ── Connect to the supervisor socket ───────────────────────────── */
    int fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (fd < 0) {
        perror("cogman-ctl: socket");
        return 1;
    }

    const char *sock_path = getenv("COGMAN_SUPERVISOR_SOCK");
    if (!sock_path || sock_path[0] == '\0')
        sock_path = CTL_SOCK_PATH;

    struct sockaddr_un addr;
    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, sock_path, sizeof(addr.sun_path) - 1);

    if (connect(fd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        fprintf(stderr, "cogman-ctl: cannot connect to %s: %s\n"
                        "  (is cogman-supervisor running?)\n",
                sock_path, strerror(errno));
        close(fd);
        return 1;
    }

    /* ── Send command ────────────────────────────────────────────────── */
    size_t cmdlen = strlen(cmd);
    size_t sent   = 0;
    while (sent < cmdlen) {
        ssize_t r = write(fd, cmd + sent, cmdlen - sent);
        if (r < 0) {
            if (errno == EINTR) continue;
            perror("cogman-ctl: write");
            close(fd);
            return 1;
        }
        sent += (size_t)r;
    }

    /* ── Read and print response ─────────────────────────────────────── */
    int exit_code = 0;
    char buf[4096];
    ssize_t n;
    /* Accumulate complete lines; check the last line for OK/ERR */
    char last_line[256] = "";

    while ((n = read(fd, buf, sizeof(buf) - 1)) > 0) {
        buf[n] = '\0';
        fwrite(buf, 1, (size_t)n, stdout);

        /* Track the last complete line we saw */
        char *p = buf + n - 1;
        /* Walk backward to find the start of the last complete line */
        while (p > buf && *p != '\n') p--;
        if (*p == '\n') {
            /* Find start of that line */
            char *line_start = p - 1;
            while (line_start > buf && *line_start != '\n') line_start--;
            if (*line_start == '\n') line_start++;
            size_t ll = (size_t)(p - line_start);
            if (ll >= sizeof(last_line)) ll = sizeof(last_line) - 1;
            strncpy(last_line, line_start, ll);
            last_line[ll] = '\0';
        }
    }
    fflush(stdout);

    /* Determine exit code from last response line */
    if (strncmp(last_line, "ERR", 3) == 0)
        exit_code = 1;

    close(fd);
    return exit_code;
}
