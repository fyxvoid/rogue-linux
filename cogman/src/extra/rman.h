/*
 * cogman/src/extra/rman.h - Rogue Manager Tactical Identifiers
 *
 * This header defines the ASCII-based communication signals for the
 * RMAN protocol, used to render the Cogman HUD.
 *
 * Why: To provide a high-contrast, low-overhead interface for operators.
 */
#define COGMAN_RMAN_H

/* RMAN v2 Tactical ASCII Identifiers */
#define RMAN_METADATA '!'
#define RMAN_TITLE    '#'
#define RMAN_SECTION  '#' /* Successive # for sub-sections */
#define RMAN_BULLET   '*'
#define RMAN_COMMAND  '>'
#define RMAN_ALERT    '?'

#endif
