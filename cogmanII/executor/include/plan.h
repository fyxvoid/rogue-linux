/*
 * cogmanII executor — plan.h
 * Shared plan layout definitions.
 * This header MUST match the Rust planner's plan.rs exactly.
 * Any change here requires a matching change in plan.rs.
 *
 * Plan file layout:
 *   [PlanHeader]                 — 64 bytes
 *   [StepRecord × step_count]    — 128 bytes each
 *   [String table]               — variable, null-terminated strings
 */

#ifndef COGMAN2_PLAN_H
#define COGMAN2_PLAN_H

#include <stdint.h>

/* Plan file magic: "CGM2PLAN" */
#define PLAN_MAGIC      "CGM2PLAN"
#define PLAN_MAGIC_LEN  8
#define PLAN_VERSION    1
#define HEADER_SIZE     64
#define STEP_SIZE       128

/* Install variant */
#define VARIANT_BINARY  0
#define VARIANT_NATIVE  1

/* Step operation codes */
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
    char     magic[8];       /*  8 bytes */
    uint32_t version;        /*  4 bytes */
    uint32_t variant;        /*  4 bytes */
    uint32_t step_count;     /*  4 bytes */
    uint32_t strtab_offset;  /*  4 bytes — byte offset to string table */
    char     _reserved[40];  /* 40 bytes — pad to 64 */
};

/* Step record — 128 bytes, packed */
struct __attribute__((packed)) step_record {
    uint32_t op;             /*   4 bytes */
    uint32_t fail_policy;    /*   4 bytes */
    uint32_t cmd_offset;     /*   4 bytes — into string table */
    uint32_t cmd_len;        /*   4 bytes */
    uint32_t wdir_offset;    /*   4 bytes — into string table */
    uint32_t wdir_len;       /*   4 bytes */
    uint32_t env_offset;     /*   4 bytes — into string table */
    uint32_t env_len;        /*   4 bytes */
    char     _reserved[96];  /*  96 bytes — pad to 128 */
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

#endif /* COGMAN2_PLAN_H */
