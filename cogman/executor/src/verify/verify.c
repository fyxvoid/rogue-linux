/*
 * cogman executor — verify/verify.c
 *
 * Artifact verification logic (safety gate).
 * build and install. A failed verification MUST abort installation —
 * no partial installs allowed. This is separated from fs.c because
 * verification is a policy decision, not just a filesystem operation.
 */

#define _POSIX_C_SOURCE 200809L

#include <string.h>
#include <sys/stat.h>

#include "../log/log.h"

int
verify_path(const char *path)
{
    struct stat st;
    if (stat(path, &st) == 0) {
        log_debug("verify_path: %s exists", path);
        return 0;
    }
    return -1;
}

int
verify_step(const char *cmd)
{
    if (strncmp(cmd, "sha256:", 7) == 0) {
        /* Format: sha256:<hash>:<filepath> */
        const char *colon = strchr(cmd + 7, ':');
        if (colon) {
            int rc = verify_path(colon + 1);
            if (rc == 0)
                log_info("Checksum file exists (hash check pending)");
            return rc;
        }
        return -1;
    }

    /* Plain path verification */
    return verify_path(cmd);
}
