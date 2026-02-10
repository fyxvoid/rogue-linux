# cogman executor — Makefile
# dwm-style: minimal, explicit, fast.
# Now modularized.

CC       = gcc
CFLAGS   = -Wall -Wextra -Wpedantic -O2 -std=c11 -D_POSIX_C_SOURCE=200809L
LDFLAGS  =
INCLUDES = -Isrc

# Optional debug logging: make CFLAGS+=-DCOGMAN_DEBUG
# CFLAGS += -DCOGMAN_DEBUG

SRC      = src/main.c \
           src/plan/plan.c \
           src/log/log.c \
           src/exec/proc.c \
           src/fs/fs.c \
           src/verify/verify.c

OBJ      = $(SRC:.c=.o)
TARGET   = cogman-exec

.PHONY: all clean

all: $(TARGET)

$(TARGET): $(OBJ)
	$(CC) $(LDFLAGS) -o $@ $(OBJ)

%.o: %.c
	$(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@

clean:
	rm -f $(OBJ) $(TARGET)
