/*
 * cogman/src/executor/plan/plan.c - Binary Plan Management
 *
 * This file handles memory-mapping (mmap) and validation of the
 * Cogman binary execution plans.
 *
 * Why: To eliminate runtime parsing overhead and achieve true
 * zero-latency handover from the Planner.
 */

#define _POSIX_C_SOURCE 200809L

#include <stdio.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/stat.h>

#include "plan.h"
#include "../log/log.h"

void *
plan_open(const char *path, size_t *out_size)
{
    int fd = open(path, O_RDONLY);
    if (fd < 0) {
        log_err("Cannot open plan file: %s", path);
        return NULL;
    }

    struct stat st;
    if (fstat(fd, &st) < 0) {
        log_err("Cannot stat plan file");
        close(fd);
        return NULL;
    }

    if ((size_t)st.st_size < HEADER_SIZE) {
        log_err("Plan file too small: %ld bytes", (long)st.st_size);
        close(fd);
        return NULL;
    }

    void *base = mmap(NULL, st.st_size, PROT_READ, MAP_PRIVATE, fd, 0);
    close(fd);

    if (base == MAP_FAILED) {
        log_err("mmap() failed for plan file");
        return NULL;
    }

    *out_size = (size_t)st.st_size;
    return base;
}

int
plan_validate(const void *base, size_t file_size)
{
    const struct plan_header *hdr = (const struct plan_header *)base;

    if (memcmp(hdr->magic, PLAN_MAGIC, PLAN_MAGIC_LEN) != 0) {
        log_err("Invalid plan magic — not a cogman plan file");
        return -1;
    }

    if (hdr->version != PLAN_VERSION) {
        log_err("Unsupported plan version: %u (expected %u)",
                hdr->version, PLAN_VERSION);
        return -1;
    }

    size_t expected_min = HEADER_SIZE + (size_t)(hdr->step_count) * STEP_SIZE;
    if (file_size < expected_min) {
        log_err("Plan file truncated: expected at least %zu bytes, got %zu",
                expected_min, file_size);
        return -1;
    }

    return 0;
}

const char *
plan_op_name(uint32_t op)
{
    switch (op) {
    case OP_EXEC:    return "EXEC";
    case OP_MKDIR:   return "MKDIR";
    case OP_COPY:    return "COPY";
    case OP_VERIFY:  return "VERIFY";
    case OP_CLEANUP: return "CLEANUP";
    default:         return "UNKNOWN";
    }
}
