/*
 * cogmanII executor — main.c
 *
 * This is the executor entry point. It does exactly four things:
 *   1. mmap() the plan file (plan/plan.c)
 *   2. Validate the plan header (plan/plan.c)
 *   3. Iterate through step records (plan/plan.h)
 *   4. Dispatch steps to handlers (exec/, fs/, verify/)
 *
 * It contains NO business logic for how steps are implemented.
 * It is a pure timeline of execution.
 */

#define _POSIX_C_SOURCE 200809L

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>

#include "plan/plan.h"
#include "log/log.h"
#include "exec/proc.h"
#include "fs/fs.h"
#include "verify/verify.h"

/*
 * Execute a single step record.
 * Returns 0 on success, -1 on failure.
 */
static int
execute_step(const void *base, const struct plan_header *hdr,
             const struct step_record *step, uint32_t index)
{
    const char *cmd  = plan_str(base, hdr->strtab_offset, step->cmd_offset);
    const char *wdir = plan_str(base, hdr->strtab_offset, step->wdir_offset);
    const char *env  = NULL;
    int rc = 0;

    if (step->env_len > 0)
        env = plan_str(base, hdr->strtab_offset, step->env_offset);

    const char *op_name = plan_op_name(step->op);
    log_info("Step %u/%u [%s]: %.60s%s",
             index + 1, hdr->step_count,
             op_name,
             cmd, (strlen(cmd) > 60 ? "..." : ""));

    log_debug("Step detail: op=%u policy=%u wdir='%s' env_len=%u",
              step->op, step->fail_policy, wdir, step->env_len);

    switch (step->op) {
    case OP_EXEC:
        rc = exec_command(cmd, wdir, env, step->env_len);
        break;

    case OP_MKDIR:
        rc = mkdir_p(cmd);
        break;

    case OP_COPY: {
        /* Command format: "src|dst" */
        char *buf = strdup(cmd);
        if (!buf) {
            rc = -1;
            break;
        }
        char *sep = strchr(buf, '|');
        if (!sep) {
            log_err("COPY step missing '|' separator: %s", cmd);
            free(buf);
            rc = -1;
            break;
        }
        *sep = '\0';
        rc = copy_recursive(buf, sep + 1);
        free(buf);
        break;
    }

    case OP_VERIFY:
        rc = verify_step(cmd);
        break;

    case OP_CLEANUP:
        rc = rm_rf(cmd);
        break;

    default:
        log_err("Unknown step opcode: %u", step->op);
        rc = -1;
        break;
    }

    if (rc != 0) {
        if (step->fail_policy == FAIL_ABORT) {
            log_err("Step %u FAILED (abort)", index + 1);
            return -1;
        } else {
            log_warn("Step %u failed (continuing)", index + 1);
            return 0;
        }
    }

    return 0;
}

int
main(int argc, char **argv)
{
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <plan-file>\n", argv[0]);
        return 1;
    }

    const char *plan_path = argv[1];
    size_t file_size;
    void *base = plan_open(plan_path, &file_size);

    if (!base)
        return 1;

    if (plan_validate(base, file_size) != 0) {
        munmap(base, file_size);
        return 1;
    }

    const struct plan_header *hdr = (const struct plan_header *)base;
    const char *variant = (hdr->variant == VARIANT_BINARY) ? "binary" : "native";

    log_info("Executing %s plan with %u step(s)", variant, hdr->step_count);

    int failed = 0;
    for (uint32_t i = 0; i < hdr->step_count; i++) {
        const struct step_record *step = plan_step(base, i);
        if (execute_step(base, hdr, step, i) != 0) {
            failed = 1;
            break;
        }
    }

    munmap(base, file_size);

    if (failed) {
        log_err("Execution aborted due to step failure");
        return 1;
    }

    log_ok("All %u steps executed successfully", hdr->step_count);
    return 0;
}
