/*
 * cogman/src/executor/exec/proc.h - Process Lifecycle Definitions
 *
 * This header defines the interface for process dispatch, isolation,
 * and environment management within the Cogman Executor.
 *
 * Why: To provide a clean boundary between the master execution loop
 * and the low-level fork/exec mechanics.
 */

#ifndef COGMAN_PROC_H
#define COGMAN_PROC_H

#include <stdint.h>

/*
 * Fork and exec a shell command via /bin/sh -c.
 * Returns child exit status (0 = success) or -1 on fork/exec failure.
 */
int exec_command(const char *cmd, const char *workdir,
                 const char *env_block, uint32_t env_len, uint32_t flags);

#endif /* COGMAN_PROC_H */
