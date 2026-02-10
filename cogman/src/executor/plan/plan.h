/*
 * cogman executor — plan/plan.h
 *
 * This header exists because the binary plan format is a contract
 * between the Rust planner and the C executor. Every constant and
 * struct here MUST match planner/src/plan/layout.rs exactly.
 *
 * Plan file layout:
 *   [PlanHeader]                 — 64 bytes
 *   [StepRecord × step_count]    — 128 bytes each
 *   [String table]               — variable, null-terminated strings
 */

#ifndef COGMAN2_PLAN_H
#define COGMAN2_PLAN_H

#include <stdint.h>
#include <stddef.h>

/* Plan file magic: "CGM2PLAN" */
#define PLAN_MAGIC      "CGM2PLAN"
#define PLAN_MAGIC_LEN  8
#define PLAN_VERSION    1
#define HEADER_SIZE     64
#define STEP_SIZE       128

/* Install variant */
#define VARIANT_BINARY  0
#define VARIANT_NATIVE  1

/* Step operation codes — one per syscall domain */
#define OP_EXEC     0   /* fork/exec a shell command */
#define OP_MKDIR    1   /* create directory tree */
#define OP_COPY     2   /* recursive copy (src|dst format) */
#define OP_VERIFY   3   /* check file existence or checksum */
#define OP_CLEANUP  4   /* rm -rf a directory */

/* Failure policy */
#define FAIL_ABORT  0   /* halt the entire plan */
#define FAIL_WARN   1   /* log and continue */

/* Plan header — 64 bytes, packed */
struct __attribute__((packed)) plan_header {
    char     magic[8];
    uint32_t version;
    uint32_t variant;
    uint32_t step_count;
    uint32_t strtab_offset;
    char     _reserved[40];
};

/* Step record — 128 bytes, packed */
struct __attribute__((packed)) step_record {
    uint32_t op;
    uint32_t fail_policy;
    uint32_t cmd_offset;
    uint32_t cmd_len;
    uint32_t wdir_offset;
    uint32_t wdir_len;
    uint32_t env_offset;
    uint32_t env_len;
    char     _reserved[96];
};

/* Accessor: get string from string table */
static inline const char *
plan_str(const void *base, uint32_t strtab_offset, uint32_t str_offset)
{
    return (const char *)base + strtab_offset + str_offset;
}

/* Accessor: get step record by index */
static inline const struct step_record *
plan_step(const void *base, uint32_t index)
{
    return (const struct step_record *)
        ((const char *)base + HEADER_SIZE + (index * STEP_SIZE));
}

/*
 * Open, validate, and mmap a plan file.
 * Returns the mmap'd base pointer, or NULL on failure.
 * On success, *out_size is set to the file size.
 */
void *plan_open(const char *path, size_t *out_size);

/* Validate the plan header. Returns 0 on success, -1 on failure. */
int plan_validate(const void *base, size_t file_size);

/* Get the human-readable name for a step op. */
const char *plan_op_name(uint32_t op);

#endif /* COGMAN2_PLAN_H */
