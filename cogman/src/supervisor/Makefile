# cogman/src/supervisor/Makefile
# Builds cogman-supervisor (init/supervisor daemon) and cogman-ctl (client).
#
# Targets:
#   all              build both binaries
#   cogman-supervisor
#   cogman-ctl
#   clean            remove generated files

CC      = gcc
CFLAGS  = -Wall -Wextra -O2 -std=c11 -D_POSIX_C_SOURCE=200809L -D_DEFAULT_SOURCE
LDFLAGS =

# ── Supervisor daemon ─────────────────────────────────────────────────
TARGET = cogman-supervisor
SRCS   = main.c service.c ctl.c
OBJS   = $(SRCS:.c=.o)

# ── Control client ────────────────────────────────────────────────────
CTL_TARGET = cogman-ctl
CTL_SRCS   = ctl_main.c
CTL_OBJS   = $(CTL_SRCS:.c=.o)

# ── Default target ────────────────────────────────────────────────────
.PHONY: all clean

all: $(TARGET) $(CTL_TARGET)

# ── Supervisor binary ─────────────────────────────────────────────────
$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $^

# ── Control client binary ─────────────────────────────────────────────
# ctl_main.c needs ctl.h (for CTL_SOCK_PATH) but does NOT link ctl.c —
# it has no supervisor state and only uses the path constant.
$(CTL_TARGET): $(CTL_OBJS)
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $^

# ── Compilation rules ─────────────────────────────────────────────────
main.o:     main.c service.h supervisor.h ctl.h
service.o:  service.c service.h
ctl.o:      ctl.c ctl.h supervisor.h service.h
ctl_main.o: ctl_main.c ctl.h

%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

# ── Clean ─────────────────────────────────────────────────────────────
clean:
	rm -f $(OBJS) $(CTL_OBJS) $(TARGET) $(CTL_TARGET)
