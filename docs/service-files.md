# Service File Reference

Service definitions live in `/etc/cogman/services/` (or the directory passed to `cogman daemon --services`). Each file has a `.service` extension and uses an INI-like format with named sections.

The daemon reads all `*.service` files at startup, sorted alphabetically. Files are not re-read while the daemon is running; use `cogman svc restart <name>` after editing.

---

## Format

```ini
[service]
name          = myapp
command       = /usr/bin/myapp --flag value
type          = process
restart       = on-failure
restart_delay = 2
depends       = syslogd, dbus

[env]
HOME = /root
PATH = /usr/bin:/bin

[health]
type     = tcp
port     = 8080
interval = 10
timeout  = 3
retries  = 3

[policy]
allow_read  = /usr, /lib, /etc
allow_write = /var/run/myapp, /tmp
```

---

## `[service]` Section

| Key | Values | Default | Description |
|-----|--------|---------|-------------|
| `name` | string | _(filename stem)_ | Service identifier used in `cogman svc` commands |
| `command` | string | — | **Required.** Full shell command to execute |
| `type` | `process` \| `oneshot` \| `forking` | `process` | Process lifecycle model |
| `restart` | `never` \| `on-failure` \| `always` | `never` | When to automatically restart |
| `restart_delay` | integer (seconds) | `1` | How long to wait before restarting |
| `depends` | comma-separated names | — | Services that must be `Running` before this one starts |

### Service types

| Type | Description |
|------|-------------|
| `process` | Long-running daemon. Supervisor tracks it by PID. |
| `oneshot` | Runs once and exits. Restart policy `never` unless explicitly set. |
| `forking` | Process double-forks (legacy daemons). Supervisor tracks the parent PID. |

---

## `[env]` Section

Key-value pairs added to the service's environment. These augment (not replace) the default environment.

```ini
[env]
MY_VAR = some_value
RUST_LOG = warn
```

---

## `[health]` Section

Optional. Enables active health probing beyond PID existence.

| Key | Values | Default | Description |
|-----|--------|---------|-------------|
| `type` | `tcp` \| `http` \| `exec` | — | Probe type |
| `port` | integer | — | Port for `tcp` and `http` probes |
| `path` | string | `/` | HTTP path for `http` probes |
| `command` | string | — | Shell command for `exec` probes |
| `interval` | integer (seconds) | `10` | Seconds between probe attempts |
| `timeout` | integer (seconds) | `5` | Seconds before probe is declared failed |
| `retries` | integer | `3` | Consecutive failures before triggering restart |

### Probe types

**tcp** — Attempts a TCP connection. Service is healthy if the connection succeeds within `timeout`.
```ini
[health]
type     = tcp
port     = 5432
interval = 15
timeout  = 3
retries  = 3
```

**http** — Sends `GET <path> HTTP/1.0` to `localhost:<port>`. Service is healthy if HTTP status < 400.
```ini
[health]
type     = http
port     = 8080
path     = /health
interval = 10
timeout  = 5
retries  = 3
```

**exec** — Runs a shell command. Service is healthy if the command exits 0.
```ini
[health]
type     = exec
command  = /usr/bin/pg_isready -q
interval = 30
timeout  = 10
retries  = 2
```

---

## `[policy]` Section

Optional. Declares Landlock filesystem restrictions applied to the service process.

```ini
[policy]
allow_read  = /usr, /lib, /etc, /proc, /dev/null
allow_write = /var/run/myapp, /var/log/myapp, /tmp
```

- `allow_read` — Comma-separated list of paths the service may read (and execute from).
- `allow_write` — Comma-separated list of paths the service may write.

Paths not listed are inaccessible (Landlock denies access). If the section is omitted entirely, no Landlock restriction is applied.

Landlock requires Linux ≥ 5.13 with `CONFIG_SECURITY_LANDLOCK=y`. On older kernels the restriction is silently skipped.

---

## Examples

### Minimal daemon

```ini
[service]
name    = syslogd
command = /sbin/syslogd -n
type    = process
restart = always

[env]
PATH = /sbin:/usr/sbin:/bin:/usr/bin
```

### Database with health check

```ini
[service]
name          = postgres
command       = /usr/bin/postgres -D /var/lib/postgresql/data
type          = process
restart       = on-failure
restart_delay = 5

[env]
PGDATA = /var/lib/postgresql/data

[health]
type     = exec
command  = /usr/bin/pg_isready -q
interval = 30
timeout  = 10
retries  = 3

[policy]
allow_read  = /usr, /lib, /etc, /var/lib/postgresql
allow_write = /var/lib/postgresql, /var/run/postgresql, /tmp
```

### Window manager with display dependency

```ini
[service]
name    = wm
command = /usr/bin/openbox --startup /etc/openbox/autostart
type    = process
restart = on-failure
depends = dbus, xorg

[env]
DISPLAY = :0
HOME    = /root
```

### One-shot setup script

```ini
[service]
name    = network-setup
command = /etc/init.d/network start
type    = oneshot
restart = never
```

---

## Naming and Load Order

Files are read in alphabetical order. To control startup ordering without explicit `depends`, prefix filenames with numbers:

```
/etc/cogman/services/
  10-syslogd.service
  20-dbus.service
  30-xorg.service
  40-wm.service
```

Services with `depends` always wait for their dependencies regardless of file order.
