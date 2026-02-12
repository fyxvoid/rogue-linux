/*
 * cogman/src/executor/log/log.h - Logging System Interface
 *
 * This header defines the Cogman logging macros and levels, including
 * the zero-cost debug logging compiled out in production.
 *
 * Why: To ensure consistent, tactical, and personality-driven output
 * throughout the entire C codebase.
 */

#ifndef COGMAN_LOG_H
#define COGMAN_LOG_H

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

#ifdef COGMAN_DEBUG
#define COGMAN_LOG_DEBUG(fmt, ...) log_debug(fmt, ##__VA_ARGS__)
#else
#define COGMAN_LOG_DEBUG(fmt, ...) ((void)0)
#endif

#define COGMAN_LOG_INFO(fmt, ...) log_info(fmt, ##__VA_ARGS__)
#define COGMAN_LOG_OK(fmt, ...)   log_ok(fmt, ##__VA_ARGS__)
#define COGMAN_LOG_WARN(fmt, ...) log_warn(fmt, ##__VA_ARGS__)
#define COGMAN_LOG_ERR(fmt, ...)  log_err(fmt, ##__VA_ARGS__)

#endif /* COGMAN_LOG_H */
