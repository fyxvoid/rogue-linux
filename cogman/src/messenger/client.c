/*
 * cogman/src/messenger/client.c - IPC Client Library
 *
 * This file provides the lightweight client interface for system tools
 * to transmit tactical notifications to the Cogman Messenger broker.
 *
 * Why: To allow decoupled components to report status without 
 * direct dependency on the broker implementation.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <errno.h>

#include "messenger.h"

int messenger_send(ipc_msg_type_t type, const void *payload, uint32_t len) {
    int sock_fd;
    struct sockaddr_un addr;
    struct ipc_header hdr;

    if ((sock_fd = socket(AF_UNIX, SOCK_STREAM, 0)) == -1) {
        return -1;
    }

    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, COGMAN_IPC_SOCK, sizeof(addr.sun_path) - 1);

    if (connect(sock_fd, (struct sockaddr *)&addr, sizeof(addr)) == -1) {
        close(sock_fd);
        return -1;
    }

    hdr.magic = IPC_MAGIC;
    hdr.version = 1;
    hdr.type = (uint16_t)type;
    hdr.payload_len = len;
    hdr.source_id = (uint32_t)getpid();

    if (send(sock_fd, &hdr, sizeof(hdr), 0) != sizeof(hdr)) {
        close(sock_fd);
        return -1;
    }

    if (len > 0 && payload != NULL) {
        if (send(sock_fd, payload, len, 0) != len) {
            close(sock_fd);
            return -1;
        }
    }

    close(sock_fd);
    return 0;
}

int messenger_hud_notify(const char *msg) {
    return messenger_send(MSG_HUD_ALERT, msg, strlen(msg));
}
