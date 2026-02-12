/*
 * cogman/src/executor/verify/verify.h - Artifact Verification Definitions
 *
 * This header defines the safety-gate interface for verifying produced
 * artifacts against checksums and metadata before deployment.
 *
 * Why: To enforce system integrity and prevent corrupted packages
 * from reaching the target filesystem.
 */

#ifndef COGMAN_VERIFY_H
#define COGMAN_VERIFY_H

/* Check that a path exists. Returns 0 if it does, -1 if not. */
int verify_path(const char *path);

/* Verify a step command (path check or sha256 hash check). */
int verify_step(const char *cmd);

#endif /* COGMAN_VERIFY_H */
