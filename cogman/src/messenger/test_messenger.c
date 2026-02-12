/*
 * cogman/src/messenger/test_messenger.c - IPC Pipeline Validation
 *
 * This file implements synthetic tests for the Cogman IPC system,
 * including broker initialization and message dispatch.
 *
 * Why: To ensure that the tactical communication layer remains 
 * functional across architectural changes.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <pthread.h>
#include <assert.h>

#include "messenger.h"

void *broker_thread(void *arg) {
    int server_fd = messenger_broker_init();
    if (server_fd == -1) return NULL;

    printf("[TEST] Broker thread started.\n");
    
    /* Process one message and exit for the test */
    int client_fd;
    struct ipc_header hdr;
    char payload[256];

    client_fd = accept(server_fd, NULL, NULL);
    if (client_fd == -1) return NULL;

    if (recv(client_fd, &hdr, sizeof(hdr), 0) == sizeof(hdr)) {
        printf("[TEST] Received header: Type=%d, Len=%d, PID=%d\n", 
               hdr.type, hdr.payload_len, hdr.source_id);
        
        if (hdr.payload_len > 0) {
            recv(client_fd, payload, hdr.payload_len, 0);
            payload[hdr.payload_len] = '\0';
            printf("[TEST] Received payload: %s\n", payload);
        }
    }

    close(client_fd);
    close(server_fd);
    unlink(COGMAN_IPC_SOCK);
    return NULL;
}

int main() {
    pthread_t tid;

    if (pthread_create(&tid, NULL, broker_thread, NULL) != 0) {
        perror("pthread_create");
        return 1;
    }

    /* Wait for broker to start */
    sleep(1);

    printf("[TEST] Sending HUD notification...\n");
    if (messenger_hud_notify("SYSTEM_THAW_INITIATED") != 0) {
        fprintf(stderr, "[TEST] Failed to send notification\n");
        return 1;
    }

    pthread_join(tid, NULL);
    printf("[TEST] IPC Validation SUCCESSFUL.\n");

    return 0;
}
