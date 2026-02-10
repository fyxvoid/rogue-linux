/*
 * cogmanII executor — exec/proc.h
 *
 * This header exists because process execution (fork/exec/wait)
 * is a distinct syscall domain from filesystem operations.
 */

#ifndef COGMAN2_PROC_H
#define COGMAN2_PROC_H

#include <stdint.h>

/*
 * Fork and exec a shell command via /bin/sh -c.
 * Returns child exit status (0 = success) or -1 on fork/exec failure.
 */
int exec_command(const char *cmd, const char *workdir,
                 const char *env_block, uint32_t env_len);

#endif /* COGMAN2_PROC_H */
