# Cogman Daemon Reference

`cogman` is the unified Rust binary that serves as init process, service supervisor, and package manager for Rogue Linux.

Source: `cogman/src/cogman/`  
Binary: `bin/cogman`

---

## Modes

```
cogman daemon [--services DIR] [--sock PATH]
cogman svc    <verb> [args]    [--sock PATH]
cogman pkg    <verb> [args]
```

The `--sock` flag (or `$COGMAN_SOCK` env var) sets the Unix socket path for daemon communication. Default: `/run/cogman.sock`.

---

## Daemon Mode

```sh
cogman daemon
cogman daemon --services /etc/cogman/services
cogman daemon --services /etc/cogman/services --sock /run/cogman.sock
```

When started as PID 1 (via kernel `init=` parameter or inittab), the daemon:

1. Reads all `*.service` files from the services directory (sorted alphabetically)
2. Starts services with `auto_start = true` after resolving dependencies
3. Runs the supervision loop:
   - Reaps dead children (`SIGCHLD` + `waitpid`)
   - Restarts according to policy with backoff
   - Runs health probes on configured intervals
   - Listens on the control socket for commands
4. Never exits (PID 1 must not exit)

### Service startup order

Services are started in dependency order. A service waits until all its `depends` entries are in `Running` state before it is spawned.

---

## Service Control

```sh
cogman svc list
cogman svc status <name>
cogman svc start  <name>
cogman svc stop   <name>
cogman svc restart <name>
cogman svc ping
```

All `svc` subcommands connect to the daemon's Unix socket and send a text command. The daemon responds with `OK\n<payload>` or `ERR <message>\n`.

### `svc list`
Prints all registered services with their current state.

```
syslogd    running    pid=123    restarts=0
dbus       running    pid=124    restarts=0
xorg       running    pid=130    restarts=1
wm         running    pid=145    restarts=0
```

### `svc status <name>`
Shows detailed status for one service.

### `svc start <name>`
Starts a service that is stopped or failed. No-op if already running.

### `svc stop <name>`
Sends SIGTERM to the service process, marks it as `Stopped` so it will not be restarted.

### `svc restart <name>`
Stops the service (SIGTERM) then starts it again with a 200 ms delay.

### `svc ping`
Checks that the daemon is alive. Returns `PONG`.

---

## Package Management

```sh
cogman pkg install <path/to/package.toml> [--root /] [--packages-dir /var/cache/cogman/packages]
cogman pkg remove  <name>
cogman pkg upgrade <path/to/package.toml>
cogman pkg list
```

### `pkg install`
1. Invokes `cogman-planner` to generate a `.plan` file
2. Invokes `cogman-executor` to build and install the package
3. Reads the `.manifest` file (list of installed paths)
4. Records the installation in the package database (`/var/lib/cogman/packages.db`)

### `pkg remove`
1. Looks up the package's file manifest in the database
2. Deletes every listed file
3. Removes empty directories
4. Purges the database record

### `pkg upgrade`
Equivalent to `remove` followed by `install`. If the package is not currently installed, behaves like `install`.

### `pkg list`
Lists all installed packages with their name, version, and category.

---

## Package Database

The database is stored at `/var/lib/cogman/packages.db` (overridable via the `$COGMAN_DB` env var).

Binary flat-file format:

```
Header (32 bytes):
  magic:   [u8; 8]  = b"CGMDB001"
  count:   u32      number of package entries
  version: u32
  _pad:    [u8; 16]

Entry (512 bytes each):
  name:         [u8; 64]
  version:      [u8; 32]
  category:     [u8; 32]
  install_root: [u8; 128]
  installed_at: u64       Unix timestamp
  file_count:   u32
  heap_offset:  u32       offset into string heap
  heap_len:     u32
  _pad:         [u8; 240]

String heap (variable):
  Per-entry file list: NUL-separated paths, total length = heap_len
```

---

## Health Checks

Service files can declare health probes beyond "PID is alive". The daemon runs probes on a configurable interval and restarts the service if enough consecutive probes fail.

```ini
[health]
type     = tcp         # tcp | http | exec
port     = 3000        # for tcp and http
path     = /healthz    # for http (optional, default /)
command  = /usr/bin/check-service.sh   # for exec
interval = 10          # seconds between checks
timeout  = 5           # seconds before probe is considered failed
retries  = 3           # consecutive failures before restart
```

| Probe type | Success condition |
|------------|------------------|
| `tcp` | TCP connection to `localhost:port` completes within `timeout` |
| `http` | HTTP GET to `localhost:port/path` returns status < 400 |
| `exec` | Command exits with code 0 |

---

## Landlock Isolation

When `[policy]` sections are present in a `.service` file, the daemon applies Landlock filesystem restrictions to the service process before exec (Linux ≥ 5.13, `CONFIG_SECURITY_LANDLOCK=y`).

```ini
[policy]
allow_read  = /usr, /lib, /etc
allow_write = /var/run/myservice, /tmp
```

If Landlock is unavailable on the running kernel, the restriction is silently skipped (logged as a warning) and the service starts unrestricted.

---

## Control Socket Protocol

Text-based, newline-terminated. Useful for scripting or custom control clients.

```
Request:  "<VERB> [arg]\n"
Response: "OK\n<payload>"  or  "ERR <message>\n"
```

| Verb | Arg | Description |
|------|-----|-------------|
| `PING` | — | Liveness check; returns `PONG` |
| `LIST` | — | Returns all services, one per line |
| `STATUS` | `<name>` | Returns status of named service |
| `START` | `<name>` | Start service |
| `STOP` | `<name>` | Stop service |
| `RESTART` | `<name>` | Restart service |

Example with `socat`:
```sh
echo "LIST" | socat - UNIX-CONNECT:/run/cogman.sock
echo "STATUS syslogd" | socat - UNIX-CONNECT:/run/cogman.sock
```

---

## Service States

| State | Meaning |
|-------|---------|
| `Pending` | Registered but not yet started (waiting for deps) |
| `Starting` | Spawn has been issued; waiting for PID to be confirmed |
| `Running` | Process is alive and (if health configured) passing probes |
| `Stopping` | SIGTERM sent; waiting for exit |
| `Stopped` | Exited cleanly or manually stopped; will not restart |
| `Restarting` | Scheduled for restart after backoff delay |
| `Failed` | Exited unexpectedly; restart policy prevents further attempts |
| `Done` | One-shot service completed successfully |

---

## Restart Policies

| Policy | When to restart |
|--------|----------------|
| `never` | Never (one-shot, manually managed services) |
| `on-failure` | Only when exit code is non-zero |
| `always` | Always, regardless of exit code |

---

## Supervisor Loop Timing

| Parameter | Default | Description |
|-----------|---------|-------------|
| Loop interval | 200 ms | Time between supervisor iterations |
| Health check interval | per-service | Configured in `[health]` section |
| Restart backoff | 1 s (default) | `restart_delay` in service file |
