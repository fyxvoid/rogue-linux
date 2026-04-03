/*
 * cogman/src/executor/verify/verify.c - Artifact Verification Engine
 *
 * This file implements the post-build verification logic, ensuring
 * that produced artifacts meet the defined safety and checksum criteria.
 *
 * Why: To prevent the installation of corrupted or incomplete
 * packages into the Rogue Linux rootfs.
 */

#define _POSIX_C_SOURCE 200809L

#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <limits.h>
#include <errno.h>

#include "../log/log.h"

int
verify_path(const char *path)
{
    struct stat st;
    if (stat(path, &st) == 0) {
        log_debug("verify_path: %s exists", path);
        return 0;
    }
    log_err("verify_path: %s not found: %s", path, strerror(errno));
    return -1;
}

/*
 * Compute the SHA-256 hash of a file by invoking sha256sum(1) via
 * fork/execve (no shell injection possible — filepath is passed as a
 * direct argv element, not interpolated into a shell string).
 *
 * Writes the 64-character hex digest into out_hex[65] on success.
 * Returns 0 on success, -1 on error.
 */
static int
compute_sha256(const char *filepath, char out_hex[65])
{
    int pipefd[2];
    if (pipe(pipefd) < 0) {
        log_err("pipe() failed: %s", strerror(errno));
        return -1;
    }

    pid_t pid = fork();
    if (pid < 0) {
        log_err("fork() failed: %s", strerror(errno));
        close(pipefd[0]);
        close(pipefd[1]);
        return -1;
    }

    if (pid == 0) {
        /* Child: redirect stdout → pipe write end, exec sha256sum */
        close(pipefd[0]);
        if (dup2(pipefd[1], STDOUT_FILENO) < 0)
            _exit(127);
        close(pipefd[1]);

        /* Try standard locations for sha256sum */
        const char *sha256sum_path = "/usr/bin/sha256sum";
        if (access(sha256sum_path, X_OK) != 0)
            sha256sum_path = "/bin/sha256sum";

        execlp(sha256sum_path, "sha256sum", "--", filepath, NULL);
        /* fallback: try PATH lookup */
        execlp("sha256sum", "sha256sum", "--", filepath, NULL);
        _exit(127);
    }

    /* Parent: read hash from pipe */
    close(pipefd[1]);

    char buf[256] = {0};
    ssize_t n = read(pipefd[0], buf, sizeof(buf) - 1);
    close(pipefd[0]);

    int status;
    waitpid(pid, &status, 0);

    if (!WIFEXITED(status) || WEXITSTATUS(status) != 0) {
        log_err("sha256sum failed for %s", filepath);
        return -1;
    }

    if (n < 64) {
        log_err("sha256sum produced insufficient output for %s", filepath);
        return -1;
    }

    /* sha256sum output format: "<64-hex-chars>  <filename>\n" */
    for (int i = 0; i < 64; i++) {
        char c = buf[i];
        if (!((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f') || (c >= 'A' && c <= 'F'))) {
            log_err("sha256sum output has unexpected char at pos %d: '%c'", i, c);
            return -1;
        }
        out_hex[i] = c;
    }
    out_hex[64] = '\0';
    return 0;
}

/*
 * Verify a file's SHA-256 hash against an expected hex digest.
 * expected_hash must be exactly 64 lowercase hex characters.
 */
static int
verify_sha256(const char *expected_hash, const char *filepath)
{
    if (strlen(expected_hash) != 64) {
        log_err("Expected SHA-256 hash must be 64 hex chars, got %zu", strlen(expected_hash));
        return -1;
    }

    if (verify_path(filepath) != 0)
        return -1;

    char actual_hex[65];
    if (compute_sha256(filepath, actual_hex) != 0)
        return -1;

    /* Case-insensitive compare: allow uppercase in expected_hash */
    char expected_lower[65];
    for (int i = 0; i < 64; i++) {
        char c = expected_hash[i];
        expected_lower[i] = (c >= 'A' && c <= 'F') ? (c + 32) : c;
    }
    expected_lower[64] = '\0';

    if (strcmp(actual_hex, expected_lower) != 0) {
        log_err("SHA-256 mismatch for %s", filepath);
        log_err("  expected: %s", expected_lower);
        log_err("  actual:   %s", actual_hex);
        return -1;
    }

    log_ok("SHA-256 verified: %s", filepath);
    return 0;
}

int
verify_step(const char *cmd)
{
    if (strncmp(cmd, "sha256:", 7) == 0) {
        /*
         * Format: sha256:<64-hex-hash>:<filepath>
         * Example: sha256:abc123...def:<path>
         */
        const char *hash_start = cmd + 7;
        const char *colon = strchr(hash_start, ':');
        if (!colon) {
            log_err("VERIFY sha256: missing ':' between hash and path in '%s'", cmd);
            return -1;
        }

        size_t hash_len = (size_t)(colon - hash_start);
        if (hash_len != 64) {
            log_err("VERIFY sha256: hash must be 64 hex chars, got %zu", hash_len);
            return -1;
        }

        char expected_hash[65];
        memcpy(expected_hash, hash_start, 64);
        expected_hash[64] = '\0';

        const char *filepath = colon + 1;
        if (*filepath == '\0') {
            log_err("VERIFY sha256: empty filepath");
            return -1;
        }

        return verify_sha256(expected_hash, filepath);
    }

    /* Plain path existence verification */
    if (verify_path(cmd) != 0) {
        log_err("VERIFY path not found: %s", cmd);
        return -1;
    }
    log_ok("VERIFY path exists: %s", cmd);
    return 0;
}
