/*
 * cogman executor — fs/fs.h
 *
 * This header exists because filesystem operations (mkdir, copy, rm)
 * are a distinct syscall domain from process execution and plan parsing.
 */

#ifndef COGMAN2_FS_H
#define COGMAN2_FS_H

/* Create directory tree recursively (like mkdir -p). */
int mkdir_p(const char *path);

/* Recursively copy src directory contents into dst. */
int copy_recursive(const char *src, const char *dst);

/* Recursively remove a directory tree (like rm -rf). */
int rm_rf(const char *path);

#endif /* COGMAN2_FS_H */
