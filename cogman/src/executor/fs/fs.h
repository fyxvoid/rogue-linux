/*
 * cogman/src/executor/fs/fs.h - Filesystem Operation Definitions
 *
 * This header defines the POSIX-based filesystem interface used by
 * the Cogman Executor for deterministic deployment.
 *
 * Why: To provide a safe, high-speed abstraction for directory
 * management and artifact copying.
 */

#ifndef COGMAN_FS_H
#define COGMAN_FS_H

/* Create directory tree recursively (like mkdir -p). */
int mkdir_p(const char *path);

/* Recursively copy src directory contents into dst. */
int copy_recursive(const char *src, const char *dst);

/* Recursively remove a directory tree (like rm -rf). */
int rm_rf(const char *path);

#endif /* COGMAN_FS_H */
