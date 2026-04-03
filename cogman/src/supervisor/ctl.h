/*
 * cogman/src/supervisor/ctl.h - Control Socket Interface
 *
 * Declares the Unix-domain socket control interface used by cogman-ctl
 * to query and manipulate running services.
 *
 * Why: Separating the IPC layer from service logic keeps both sides
 * independently comprehensible and testable.
 */

#ifndef COGMAN_CTL_H
#define COGMAN_CTL_H

/* Path of the Unix-domain socket (can be overridden at compile time) */
#ifndef CTL_SOCK_PATH
#define CTL_SOCK_PATH "/run/cogman-supervisor.sock"
#endif

/* Maximum length of one control command line (including '\n') */
#define CTL_CMD_MAX 256

/*
 * ctl_init – create, bind, and listen on CTL_SOCK_PATH.
 * Sets the socket to non-blocking mode.
 * Returns the listening fd on success, -1 on failure.
 */
int ctl_init(void);

/*
 * ctl_accept – accept one pending connection on server_fd (non-blocking).
 * Reads one command line, dispatches it, writes the response, closes the
 * connection.  Returns immediately if no connection is pending.
 */
void ctl_accept(int server_fd);

#endif /* COGMAN_CTL_H */
