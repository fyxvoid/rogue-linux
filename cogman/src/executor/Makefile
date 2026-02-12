# cogman executor — Makefile
# dwm-style: minimal, explicit, fast.
# Now modularized.

CC       = gcc
CFLAGS   = -Wall -Wextra -Wpedantic -O2 -std=c11 -D_POSIX_C_SOURCE=200809L
LDFLAGS  = -lpthread
INCLUDES = -Isrc -I../messenger

# Optional debug logging: make CFLAGS+=-DCOGMAN_DEBUG
# CFLAGS += -DCOGMAN_DEBUG

SRC      = main.c \
           plan/plan.c \
           log/log.c \
           exec/proc.c \
           fs/fs.c \
           verify/verify.c \
           ../messenger/messenger.c \
           ../messenger/client.c

OBJ      = $(SRC:.c=.o)
TARGET   = cogman-exec

TEST_SRC = ../messenger/test_messenger.c ../messenger/messenger.c ../messenger/client.c log/log.c
TEST_OBJ = $(TEST_SRC:.c=.o)
TEST_TARGET = messenger_test

.PHONY: all clean messenger_test

all: $(TARGET)

$(TARGET): $(OBJ)
	$(CC) $(LDFLAGS) -o $@ $(OBJ)

messenger_test: $(TEST_OBJ)
	$(CC) $(LDFLAGS) -o $@ $(TEST_OBJ)

%.o: %.c
	$(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@

clean:
	rm -f $(OBJ) $(TARGET) $(TEST_TARGET) ../messenger/*.o
