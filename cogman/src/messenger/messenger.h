/*
 * cogman/src/messenger/messenger.h - IPC Message Protocol
 *
 * This header defines the TLV-based wire protocol for Cogman's
 * inter-process communication system.
 *
 * Why: To ensure reliable, isolated communication between the
 * Executor and the RMAN client.
 */

#ifndef COGMAN_MESSENGER_H
#define COGMAN_MESSENGER_H

#include <stdint.h>

#define COGMAN_IPC_SOCK "/tmp/cogman.sock"

/* Message Types */
typedef enum {
    MSG_HEARTBEAT = 0,    /* Periodic health check */
    MSG_HUD_ALERT = 1,    /* Push a notification to the HUD */
    MSG_POLICY_REQ = 2,   /* Request a dynamic Landlock/Seccomp change */
    MSG_DATA_XFER = 3,    /* Tool-to-Tool data transfer */
    MSG_LOG_INFO = 4,     /* General tool logging */
} ipc_msg_type_t;

/* Message Header — 16 bytes */
struct __attribute__((packed)) ipc_header {
    uint32_t magic;       /* "COG1" -> 0x434F4731 */
    uint16_t version;     /* Protocol version (1) */
    uint16_t type;        /* ipc_msg_type_t */
    uint32_t payload_len; /* Length of following data */
    uint32_t source_id;   /* PID of the sending process */
};

#define IPC_MAGIC 0x434F4731

/* Standard Success/Failure responses */
#define IPC_ACK 0
#define IPC_NAK -1

/* Function Prototypes */
int messenger_broker_init(void);
int messenger_listen_and_process(int server_fd);
int messenger_send(ipc_msg_type_t type, const void *payload, uint32_t len);
int messenger_hud_notify(const char *msg);

#endif /* COGMAN_MESSENGER_H */
