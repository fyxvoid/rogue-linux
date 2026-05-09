# Rogue Linux — Daily Driver Roadmap

Current state: boots with cogman as PID 1, persistent disk image, UEFI GRUB, pivot_root, multi-TTY, DHCP, SSH, syslogd, ntpd, void user, 5 packages verified.
Everything below is what stands between now and a usable daily driver.

---

## P0 — Blockers ✓ DONE

### Persistent Storage ✓
- `build/build-disk.sh` creates a 1 GB GPT image (64 MB EFI + ext4 root)
- Copies rootfs, writes `/etc/fstab` with real UUIDs
- Two boot paths: `boot-disk.sh` (UEFI GRUB) and `boot-disk-direct.sh` (QEMU fast)
- cogman packages installed via `cogman-exec` survive reboot

### Bootloader ✓
- `build-disk.sh` installs GRUB2 x86_64-efi (removable, no-nvram)
- `grub.cfg` generated with UUID-based root, `init=/init`, `--services-dir` args
- If `build/rogue-linux.cpio.gz` exists, it is copied to `/boot/initramfs.cpio.gz`
  and an `initrd` line added — enabling the full initramfs → pivot path under GRUB

### initramfs → pivot_root ✓
- `rootfs/init` is now a proper shell script (was: symlink to cogman-supervisor)
- **Branch A (initramfs)**: parses `root=UUID=` from cmdline, waits for the block
  device, mounts it, pre-mounts `/run` as tmpfs on the new root, then `switch_root`
- **Branch B (direct disk)**: detects ext4/btrfs root in `/proc/mounts`, mounts
  `/run` as tmpfs, execs cogman-supervisor — no pivot needed
- RAM-only dev boot (no `root=` in cmdline): stays in ramfs, cogman starts directly
- `rcS` updated: `/run` is pre-mounted by `/init`; rcS only ensures subdirs exist

---

## P1 — Core System

### Device Management ✓
- `mdev.service` in both `services/` and `services-minimal/`
- Runs `mdev -s` at boot (oneshot) + registers `/sbin/mdev` as the kernel hotplug handler
- Remaining: eudev for persistent device naming and complex udev rules

### Multi-TTY Consoles ✓
- `tty1.service` through `tty6.service` in both `services/` and `services-minimal/`
- Each runs `getty -L ttyN 0 linux`, restarts on failure, depends on `rcs`

### User Management (partial)
- ✓ `void` user added (uid 1000, gid 1000, home `/home/void`, shell `/bin/sh`)
- ✓ `void` added to `wheel` and `users` supplementary groups
- ✓ `/etc/passwd`, `/etc/shadow`, `/etc/group` updated
- ✓ `/etc/doas.conf` created: `permit persist :wheel` and `permit nopass root`
- Still needed: `doas` binary compiled and placed in rootfs
- Still needed: remove getty `-l /bin/sh` bypass once PAM login is tested

### PAM Authentication ✓
- `/etc/pam.d/login`, `su`, `sudo`, `other` all configured with `pam_unix.so`
- `other` uses `pam_deny.so` as safe fallback for unconfigured services
- Remaining: getty still uses `-l /bin/sh` bypass — remove when PAM login tested

### Locale & Timezone ✓
- `/etc/locale.conf` created: `LANG=C.UTF-8`, `LC_ALL=C.UTF-8`
- `/etc/timezone` set to `UTC`; `/etc/localtime` populated with UTC TZif binary
- `/etc/profile` exports `TERM=xterm-256color`, `LANG=C.UTF-8`, `EDITOR=vi`, `PAGER=less`
- `/etc/profile` sources `/root/.bashrc` for root sessions

### System Logging ✓
- `syslogd.service`: busybox syslogd → `/var/log/syslog` (1 MB max, 3 rotations)
- `klogd.service`: kernel log daemon, depends on `syslogd`
- Remaining: logrotate for long-running installs

### Time Sync ✓
- `ntpd.service`: busybox ntpd against `pool.ntp.org`, restarts on failure

---

## P2 — Networking

### WiFi
- No wireless stack at all
- Need: `iwd` (or `wpa_supplicant`) + kernel WiFi drivers compiled in
- `iwd` integrates well as a cogman service

### DHCP Client ✓
- `eth0-dhcp.service`: runs `udhcpc -i eth0` with `/etc/udhcpc/default.script`
- Hook script writes `ip addr`, `ip route`, and `/etc/resolv.conf` on lease events

### DNS Resolution ✓
- udhcpc hook writes nameservers to `/etc/resolv.conf` on `bound`/`renew` events
- Static fallback in `/etc/resolv.conf` still useful before DHCP completes

### Firewall ✓
- `firewall.service` loads `/etc/cogman/firewall.nft` at boot (oneshot, depends=rcs)
- Ruleset: drop by default, accept loopback + established + ICMP + SSH(22) + dashboard(7070)
- Remaining: `nft` binary not yet in rootfs — needs native build or binary package

---

## P3 — cogman Package System

### Package Database ✓
- `cogman-exec` accepts `--pkg-name <n> --pkg-version <v>` and appends to `/var/lib/cogman/installed.db` on success
- `cogman-ctl list-pkgs` reads and prints the database
- Remaining: `cogman-planner` should pass `--pkg-name/--pkg-version` when invoking `cogman-exec`

### Package Removal ✓ (partial)
- `[uninstaller]` stanza added to TOML schema (`Uninstaller { steps: Vec<String> }`)
- `plan_uninstall()` in `binary.rs` emits uninstaller steps from the stanza
- Remaining: wire `plan_uninstall` into a `cogman-planner uninstall` subcommand; file manifest still needed

### Package Upgrade
- No diff between installed version and new plan
- Need: version comparison in `cogman-planner`, upgrade path in `cogman-exec`

### Online Repository
- All plans are local TOML files — no remote fetch
- Need: a package index (JSON/TOML) hosted on the website
- `cogman-planner fetch <name>` pulls the plan, verifies signature, installs

### Binary Package Cache ✓ (partial)
- `/var/cache/cogman/` directory exists and survives reboot (on disk)
- Still needed: `cogman-exec` writes compiled `.plan` files there and reuses them

---

## P4 — Display (for GUI use)

### Kernel DRM / KMS
- Kernel config needs `CONFIG_DRM`, `CONFIG_DRM_VIRTIO_GPU` for QEMU
- Real hardware needs Mesa + the right GPU driver (i915, amdgpu, nouveau)
- Without KMS, X11 falls back to VESA/fbdev — slow and limited

### Font Rendering
- No `fontconfig` or `freetype` → applications that need fonts fail silently
- Need: `fontconfig`, a base font set (DejaVu or Noto), `fc-cache` run at install

### ncurses / TERM ✓ (partial)
- `/etc/profile` now exports `TERM=xterm-256color` for interactive sessions
- Remaining: proper `terminfo` database and `ncurses` linked against running libc

### X11 / Wayland
- `Xorg` and `i3` binaries exist in rootfs but untested on real hardware
- Need: `xorg.conf.d` snippets for input/output, `startx` wrapper, `.xinitrc`
- Wayland alternative: `sway` (lighter, no X dependency)

---

## P5 — Audio

- No ALSA, no PipeWire, no kernel sound modules
- Need: `alsa-utils`, kernel `CONFIG_SND_*` for target hardware
- PipeWire as cogman service (replaces PulseAudio + JACK in one)
- `wireplumber` as session manager

---

## P6 — Security

### Full Disk Encryption
- No LUKS on the root partition
- Need: `cryptsetup` in initramfs, kernel `CONFIG_DM_CRYPT`
- Boot flow: GRUB → initramfs → `cryptsetup open` → pivot_root → cogman

### SSH Server ✓
- `dropbear` daemon binary present at `/usr/sbin/dropbear`
- `dropbear-keygen.service`: generates RSA + ECDSA host keys on first boot (oneshot)
- `dropbear.service`: runs dropbear on port 22, depends on `dropbear-keygen`
- Keys stored in `/etc/dropbear/` (persists on disk across reboots)

### Sudo / Privilege Escalation ✓
- No `sudo` or `doas` binary
- `/etc/doas.conf` created: `permit persist :wheel` + `permit nopass root`
- Remaining: `doas` binary needs compilation and installation

---

## P7 — Developer Toolchain

These are needed to build cogman packages from source inside the distro:

| Tool | Why |
|---|---|
| `gcc` / `musl-gcc` | compile C packages |
| `make` / `cmake` | build systems |
| `python3` | scripting, cogman planner deps |
| `git` | source fetching |
| `pkg-config` | library discovery |
| `patch` | apply source patches |

---

## P8 — Daily Use Applications

- tmux, htop, less, neofetch, alsa cogman plans added

Minimum set for actual daily use:

| Category | Package | Notes |
|---|---|---|
| Terminal multiplexer | `tmux` | sessions survive disconnect |
| Pager | `less` | busybox less exists but limited |
| File manager | `lf` or `ranger` | keyboard-driven |
| Browser (TUI) | `w3m` or `links2` | for headless/SSH use |
| Browser (GUI) | `firefox-esr` | only after X11/Wayland works |
| PDF viewer | `mupdf` | lightweight, no GTK needed |
| Archive | `unzip`, `p7zip` | busybox tar covers .tar.* |
| Image viewer | `feh` | already in rootfs |
| Media | `mpv` | audio + video, minimal deps |
| Monitoring | `htop` | process/resource viewer |

---

## P9 — Cogman-Specific Work Remaining

- [x] `cogman-ctl restart <service>` without reboot
- [x] `cogman-ctl stop-all` graceful shutdown sequence (reverse-order stop)
- [x] `cogman-planner` network heuristic false-positives fixed (`/etc/curl` no longer triggers)
- [x] Service dependency cycle detection (DFS-based, logs offending edge and aborts)
- [x] `cogman-supervisor` re-exec on binary upgrade without killing children
- [x] Cogman web dashboard (local HTTP on port 7070) for service control
- [x] Plan format: add `[uninstaller]` stanza
- [ ] Plan signing: GPG or minisign verification before exec

---

## What's Done

- [x] cogman-supervisor as PID 1 (statically linked, signal-safe)
- [x] rcS mounts proc / sys / dev / run
- [x] Oneshot dep ordering fixed (console waits for rcs to complete)
- [x] Control socket at `/run/cogman-supervisor.sock`
- [x] `cogman-ctl` list / status / start / stop / restart / stop-all working
- [x] `cogman-planner` compiles TOML → binary plan (false-positive fix applied)
- [x] `cogman-exec` runs plans with step-level failure reporting
- [x] 5 packages installed and verified: bash, vim, curl, nano, ssh
- [x] Persistent disk image (`build/rogue-linux-disk.img`, ext4 + EFI)
- [x] GRUB2 EFI bootloader with UUID-based grub.cfg
- [x] `rootfs/init` — dual-mode: initramfs pivot_root + direct disk exec
- [x] `/run` mounted as fresh tmpfs on every boot path before cogman starts
- [x] `void` user (uid 1000), home dir, supplementary groups (wheel, users)
- [x] `/etc/locale.conf` (C.UTF-8), `/etc/timezone` (UTC), `/etc/localtime` (TZif)
- [x] `/etc/profile` — TERM, LANG, EDITOR, PAGER, aliases, bashrc source
- [x] Multi-TTY: tty1–tty6 getty services (services/ and services-minimal/)
- [x] mdev hotplug service registered with kernel
- [x] syslogd + klogd services → `/var/log/syslog`
- [x] ntpd service → `pool.ntp.org`
- [x] DHCP client (udhcpc) + hook script updates resolv.conf on lease
- [x] SSH: dropbear daemon + first-boot host key generation service
- [x] `/var/cache/cogman/` and `/var/lib/cogman/` directories (persistent)
- [x] `/var/lib/cogman/installed.db` — `cogman-exec` appends name+version on successful install
- [x] `cogman-ctl list-pkgs` — reads and displays installed package database
- [x] `[uninstaller]` stanza in TOML schema; `plan_uninstall()` in planner emits steps
- [x] Dependency cycle detection in supervisor (DFS, aborts on cycle at startup)
- [x] PAM configured: `/etc/pam.d/login`, `su`, `sudo`, `other` (pam_unix + deny fallback)
- [x] `/etc/doas.conf` — `permit persist :wheel` and `permit nopass root`
- [x] Firewall service: `firewall.nft` + `firewall.service` (drop-by-default, SSH+ICMP allowed)
- [x] Cogman web dashboard: busybox httpd on port 7070 with CGI status endpoint

---

*Last updated: 2026-05-09*

