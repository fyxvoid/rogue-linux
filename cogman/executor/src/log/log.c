/*
 * cogman executor — log/log.c
 *
 * Logging implementation (ANSI support).
 * that must be decoupled from business logic. Every module includes
 * log.h but never calls fprintf(stderr, ...) directly.
 *
 * Cogman butler personality preserved: all messages end with ", sir."
 * All output goes to stderr so stdout remains available for data.
 */

#include <stdio.h>
#include <stdarg.h>

/* ANSI escape codes */
#define RST   "\033[0m"
#define BOLD  "\033[1m"
#define BLUE  "\033[94m"
#define WHITE "\033[97m"
#define GREEN "\033[92m"
#define YELLO "\033[93m"
#define RED   "\033[91m"

#define PREFIX BLUE BOLD "▐ COGMAN II ▌" RST " "

void
log_info(const char *fmt, ...)
{
    va_list ap;
    fprintf(stderr, PREFIX WHITE);
    va_start(ap, fmt);
    vfprintf(stderr, fmt, ap);
    va_end(ap);
    fprintf(stderr, ", sir." RST "\n");
}

void
log_ok(const char *fmt, ...)
{
    va_list ap;
    fprintf(stderr, PREFIX GREEN);
    va_start(ap, fmt);
    vfprintf(stderr, fmt, ap);
    va_end(ap);
    fprintf(stderr, ". Quite satisfactory, sir." RST "\n");
}

void
log_warn(const char *fmt, ...)
{
    va_list ap;
    fprintf(stderr, PREFIX YELLO);
    va_start(ap, fmt);
    vfprintf(stderr, fmt, ap);
    va_end(ap);
    fprintf(stderr, ". One raises an eyebrow, sir." RST "\n");
}

void
log_err(const char *fmt, ...)
{
    va_list ap;
    fprintf(stderr, PREFIX RED);
    va_start(ap, fmt);
    vfprintf(stderr, fmt, ap);
    va_end(ap);
    fprintf(stderr, ". Deeply unfortunate, sir." RST "\n");
}
