/*
 * cogman/src/messenger/messenger.c - IPC Broker Implementation
 *
 * This file implements the Unix Domain Socket server that routes
 * tactical signals between system components.
 *
 * Why: To decouple the execution engine from the visual interface
 * while maintaining near-zero latency.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <errno.h>

#include "messenger.h"
#include "../executor/log/log.h"

int messenger_broker_init() {
    int server_fd;
    struct sockaddr_un addr;

    if ((server_fd = socket(AF_UNIX, SOCK_STREAM, 0)) == -1) {
        log_err("Messenger: Failed to create socket: %s", strerror(errno));
        return -1;
    }

    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, COGMAN_IPC_SOCK, sizeof(addr.sun_path) - 1);

    unlink(COGMAN_IPC_SOCK);

    if (bind(server_fd, (struct sockaddr *)&addr, sizeof(addr)) == -1) {
        log_err("Messenger: Failed to bind socket: %s", strerror(errno));
        close(server_fd);
        return -1;
    }

    if (listen(server_fd, 5) == -1) {
        log_err("Messenger: Failed to listen: %s", strerror(errno));
        close(server_fd);
        return -1;
    }

    log_ok("Messenger: Broker initialized at %s", COGMAN_IPC_SOCK);
    return server_fd;
}

int messenger_listen_and_process(int server_fd) {
    int client_fd;
    struct ipc_header hdr;

    log_info("Messenger: Broker listening for events...");

    while (1) {
        if ((client_fd = accept(server_fd, NULL, NULL)) == -1) {
            log_err("Messenger: Accept error: %s", strerror(errno));
            continue;
        }

        if (recv(client_fd, &hdr, sizeof(hdr), 0) != sizeof(hdr)) {
            log_warn("Messenger: Dropped malformed header from PID %d", hdr.source_id);
            close(client_fd);
            continue;
        }

        if (hdr.magic != IPC_MAGIC) {
            log_err("Messenger: Protocol mismatch (Magic: 0x%08X)", hdr.magic);
            close(client_fd);
            continue;
        }

        switch (hdr.type) {
            case MSG_HUD_ALERT:
                log_info("\033[34m[HUD ALERT]\033[0m from tool %d: (payload_len: %d)", 
                         hdr.source_id, hdr.payload_len);
                break;
            case MSG_HEARTBEAT:
                log_debug("Messenger: Heartbeat from PID %d", hdr.source_id);
                break;
            default:
                log_warn("Messenger: Unhandled message type %d", hdr.type);
        }

        close(client_fd);
    }

    return 0;
}
