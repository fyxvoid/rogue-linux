/*
 * cogmanII executor — log/log.h
 *
 * This header exists because every C file needs logging,
 * and the COGMAN_DEBUG compile flag controls whether trace-level
 * output is included. When COGMAN_DEBUG is not defined, log_debug
 * compiles to nothing — zero runtime cost.
 */

#ifndef COGMAN2_LOG_H
#define COGMAN2_LOG_H

void log_info(const char *fmt, ...);
void log_ok(const char *fmt, ...);
void log_warn(const char *fmt, ...);
void log_err(const char *fmt, ...);

/* Debug logging — compile-time only.
 * Build with: make CFLAGS+=-DCOGMAN_DEBUG */
#ifdef COGMAN_DEBUG
#include <stdio.h>
#define log_debug(fmt, ...) \
    fprintf(stderr, "\033[90m[DEBUG] " fmt "\033[0m\n", ##__VA_ARGS__)
#else
#define log_debug(fmt, ...) ((void)0)
#endif

#endif /* COGMAN2_LOG_H */
