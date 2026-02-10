/*
 * cogmanII executor — verify/verify.h
 *
 * This header exists because verification (artifact checks before
 * installation) is the safety gate between build and install.
 * It must be a separate concern from general filesystem operations.
 */

#ifndef COGMAN2_VERIFY_H
#define COGMAN2_VERIFY_H

/* Check that a path exists. Returns 0 if it does, -1 if not. */
int verify_path(const char *path);

/* Verify a step command (path check or sha256 hash check). */
int verify_step(const char *cmd);

#endif /* COGMAN2_VERIFY_H */
