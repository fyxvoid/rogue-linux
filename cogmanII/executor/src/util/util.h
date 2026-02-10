/*
 * cogmanII executor — util/util.h
 *
 * This header exists for small inline helpers that don't belong
 * in any specific syscall domain. Keep this minimal — if a helper
 * grows beyond a few lines, it deserves its own module.
 */

#ifndef COGMAN2_UTIL_H
#define COGMAN2_UTIL_H

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

#endif /* COGMAN2_UTIL_H */
