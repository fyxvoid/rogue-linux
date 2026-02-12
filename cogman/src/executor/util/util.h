/*
 * cogman/src/executor/util/util.h - Shared Inline Utilities
 *
 * This header contains minimalist, side-effect-free inline helpers
 * used across the Cogman Executor.
 *
 * Why: To centralize common logic (e.g., safe string length) while
 * maintaining a zero-dependency footprint.
 */

#ifndef COGMAN_UTIL_H
#define COGMAN_UTIL_H

#include <string.h>

/* Safe string length with upper bound */
static inline size_t
safe_strlen(const char *s, size_t max)
{
    size_t i = 0;
    while (i < max && s[i] != '\0')
        i++;
    return i;
}

#endif /* COGMAN_UTIL_H */
