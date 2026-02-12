/*
 * cogman/src/extra/btm.h - Binary Tool Metadata Definitions
 *
 * This header defines the high-performance BTM structure used by
 * Rogue Linux to achieve O(1) package metadata access.
 *
 * Why: To eliminate database lookup latency in tactical environments.
 */
#define COGMAN_BTM_H

#include <stdint.h>

struct __attribute__((packed)) btm_metadata {
    uint32_t magic;         /* "BTM1" */
    uint32_t pkg_id;        /* Unique identifier */
    uint32_t flags;         /* PERSISTENT, CRITICAL, etc. */
    uint32_t desc_offset;   /* Offset into string table */
    uint32_t rman_offset;   /* Offset to embedded RMAN manual */
};

#define BTM_MAGIC 0x42544D31 /* "BTM1" */

#endif
