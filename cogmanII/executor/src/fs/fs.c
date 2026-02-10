/*
 * cogmanII executor — fs/fs.c
 *
 * This module exists because filesystem operations (mkdir, copy, rm)
 * are a distinct syscall domain. No shell invocations — uses POSIX
 * APIs directly for determinism and speed.
 */

#define _POSIX_C_SOURCE 200809L

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <dirent.h>
#include <fcntl.h>
#include <errno.h>
#include <limits.h>

#include "../log/log.h"

int
mkdir_p(const char *path)
{
    char tmp[PATH_MAX];
    char *p;
    size_t len;

    len = strlen(path);
    if (len == 0 || len >= PATH_MAX)
        return -1;

    memcpy(tmp, path, len + 1);

    if (tmp[len - 1] == '/')
        tmp[len - 1] = '\0';

    for (p = tmp + 1; *p; p++) {
        if (*p == '/') {
            *p = '\0';
            if (mkdir(tmp, 0755) != 0 && errno != EEXIST) {
                log_err("mkdir(%s) failed: %s", tmp, strerror(errno));
                return -1;
            }
            *p = '/';
        }
    }

    if (mkdir(tmp, 0755) != 0 && errno != EEXIST) {
        log_err("mkdir(%s) failed: %s", tmp, strerror(errno));
        return -1;
    }

    log_debug("mkdir_p: %s", path);
    return 0;
}

/* Copy a single file, preserving permissions. */
static int
copy_file(const char *src, const char *dst)
{
    int fd_src, fd_dst;
    struct stat st;
    char buf[8192];
    ssize_t n;

    fd_src = open(src, O_RDONLY);
    if (fd_src < 0)
        return -1;

    if (fstat(fd_src, &st) < 0) {
        close(fd_src);
        return -1;
    }

    fd_dst = open(dst, O_WRONLY | O_CREAT | O_TRUNC, st.st_mode);
    if (fd_dst < 0) {
        close(fd_src);
        return -1;
    }

    while ((n = read(fd_src, buf, sizeof(buf))) > 0) {
        if (write(fd_dst, buf, n) != n) {
            close(fd_src);
            close(fd_dst);
            return -1;
        }
    }

    close(fd_src);
    close(fd_dst);
    return (n < 0) ? -1 : 0;
}

int
copy_recursive(const char *src, const char *dst)
{
    DIR *dir;
    struct dirent *ent;
    struct stat st;
    char src_path[PATH_MAX], dst_path[PATH_MAX];

    dir = opendir(src);
    if (!dir) {
        log_err("Cannot open directory: %s", src);
        return -1;
    }

    if (mkdir_p(dst) != 0) {
        closedir(dir);
        return -1;
    }

    while ((ent = readdir(dir)) != NULL) {
        if (ent->d_name[0] == '.' &&
            (ent->d_name[1] == '\0' ||
             (ent->d_name[1] == '.' && ent->d_name[2] == '\0')))
            continue;

        snprintf(src_path, PATH_MAX, "%s/%s", src, ent->d_name);
        snprintf(dst_path, PATH_MAX, "%s/%s", dst, ent->d_name);

        if (stat(src_path, &st) < 0) {
            log_err("Cannot stat: %s", src_path);
            closedir(dir);
            return -1;
        }

        if (S_ISDIR(st.st_mode)) {
            if (copy_recursive(src_path, dst_path) != 0) {
                closedir(dir);
                return -1;
            }
        } else {
            if (copy_file(src_path, dst_path) != 0) {
                log_err("Cannot copy: %s", src_path);
                closedir(dir);
                return -1;
            }
        }
    }

    closedir(dir);
    log_debug("copy_recursive: %s -> %s", src, dst);
    return 0;
}

int
rm_rf(const char *path)
{
    DIR *dir;
    struct dirent *ent;
    struct stat st;
    char child[PATH_MAX];

    if (lstat(path, &st) < 0)
        return (errno == ENOENT) ? 0 : -1;

    if (!S_ISDIR(st.st_mode))
        return unlink(path);

    dir = opendir(path);
    if (!dir)
        return -1;

    while ((ent = readdir(dir)) != NULL) {
        if (ent->d_name[0] == '.' &&
            (ent->d_name[1] == '\0' ||
             (ent->d_name[1] == '.' && ent->d_name[2] == '\0')))
            continue;

        snprintf(child, PATH_MAX, "%s/%s", path, ent->d_name);
        if (rm_rf(child) != 0) {
            closedir(dir);
            return -1;
        }
    }

    closedir(dir);
    log_debug("rm_rf: %s", path);
    return rmdir(path);
}
