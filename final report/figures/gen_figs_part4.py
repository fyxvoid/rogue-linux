"""Part 4: Figure 8.1, DWM UI mockup, Terminal mockup"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Circle
from matplotlib.lines import Line2D
import numpy as np, os

OUT = os.path.dirname(os.path.abspath(__file__))
BG="#F8F9FA"; RUST="#C0392B"; TEAL="#0E6655"; NAVY="#1A3A5C"
GRAY="#5D6D7E"; GREEN="#1E8449"; ORG="#CA6F1E"; RED="#922B21"
PURP="#6C3483"; GOLD="#9A7D0A"; BLK="#1C2833"

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'text.color':BLK})

def save(fig, name):
    fig.savefig(os.path.join(OUT,name), dpi=180, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    plt.close(fig)
    print("  saved", name)

def arr(ax, x1,y1,x2,y2, color=BLK, lw=1.6, label='',
        lx=None, ly=None, rad=0.0):
    ax.annotate('', xy=(x2,y2), xytext=(x1,y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=lw,
                                connectionstyle=f'arc3,rad={rad}'), zorder=5)
    if label:
        mx = lx if lx is not None else (x1+x2)/2
        my = ly if ly is not None else (y1+y2)/2+0.08
        ax.text(mx, my, label, ha='center', va='bottom', fontsize=8,
                color=color, zorder=6,
                bbox=dict(fc=BG, ec='none', pad=1.5))

def rbox(ax, cx, cy, w, h, label, ec, fc=None, fs=9, bold=False):
    if fc is None: fc = ec+'20'
    ax.add_patch(FancyBboxPatch((cx-w/2, cy-h/2), w, h,
                                boxstyle='round,pad=0.04', lw=1.8,
                                ec=ec, fc=fc, zorder=3))
    ax.text(cx, cy, label, ha='center', va='center', fontsize=fs,
            fontweight='bold' if bold else 'normal', color=ec, zorder=4)

# ═════════════════════════════════════════════════════════════════════════════
# Figure 8.1  —  Service Boot Sequence
# ═════════════════════════════════════════════════════════════════════════════
def fig8_1():
    fig, ax = plt.subplots(figsize=(16, 9), facecolor=BG)
    ax.set_facecolor(BG); ax.axis('off')
    ax.set_xlim(0,16); ax.set_ylim(0,9)
    ax.set_title("Figure 8.1 — Service Boot Sequence on Minimal Rootfs  (QEMU Verified)",
                 fontsize=12, fontweight='bold', color=NAVY, pad=8)

    # Timeline bar
    tl_y = 2.0
    ax.add_patch(FancyBboxPatch((0.5, tl_y-0.12), 15.0, 0.24,
                               boxstyle='square,pad=0', lw=0, fc=GRAY, zorder=2))

    events = [
        # (x,  label_y, label,                          color,   ms_label)
        (0.8,  7.5, "Kernel\nboots",                    GRAY,    "0 ms"),
        (2.5,  6.3, "execve\n/sbin/init\n(PID 1)",      TEAL,    "~50 ms"),
        (4.3,  7.5, "mount\nproc sysfs\ndevtmpfs tmpfs", NAVY,   "~80 ms"),
        (6.2,  6.3, "parse *.service\nfiles (×4)",      PURP,    "~90 ms"),
        (8.0,  7.5, "start\nhello.service\n(oneshot)",   GREEN,  "~100 ms"),
        (9.8,  6.3, "hello: DONE\nexit code 0",         GREEN,   "~110 ms"),
        (11.0, 7.5, "start\nheartbeat.service\n(always)",TEAL,   "~120 ms"),
        (12.2, 6.3, "heartbeat:\nRUNNING pid=42",       TEAL,    "~130 ms"),
        (13.2, 7.5, "start\nctl-probe\n(oneshot)",       NAVY,  "~140 ms"),
        (14.2, 6.3, "ctl list: OK\nDONE",               NAVY,   "~150 ms"),
        (15.2, 7.5, "All stages\nPASS ✓",               GREEN,  "~1800 ms"),
    ]

    for ex, ey, lbl, clr, ts in events:
        # stem
        ax.plot([ex, ex], [tl_y+0.12, tl_y+(ey-tl_y)*0.55], color=clr, lw=1, ls=':', zorder=2)
        # dot
        ax.add_patch(Circle((ex, tl_y), 0.15, fc=clr, ec=BG, lw=1.5, zorder=4))
        # label box
        rbox(ax, ex, ey, 2.0, abs(ey-tl_y)*0.65, lbl, clr, fs=8)
        # timestamp below timeline
        ax.text(ex, tl_y-0.45, ts, ha='center', fontsize=7.5, color=GRAY)

    ax.text(0.5, tl_y-0.85, "Boot time", ha='left', fontsize=8.5,
            color=GRAY, style='italic')

    # Phase brackets
    phases = [
        (0.5, 6.5, "Kernel init", GRAY),
        (6.5, 10.5, "Service startup", GREEN),
        (10.5,15.5,"All services verified", TEAL),
    ]
    for x1,x2,lbl,clr in phases:
        ax.plot([x1+0.1, x2-0.1], [1.4, 1.4], color=clr, lw=2.5, zorder=3)
        ax.plot([x1+0.1, x1+0.1], [1.4, 1.6], color=clr, lw=2.5, zorder=3)
        ax.plot([x2-0.1, x2-0.1], [1.4, 1.6], color=clr, lw=2.5, zorder=3)
        ax.text((x1+x2)/2, 1.05, lbl, ha='center', fontsize=8.5,
                color=clr, fontweight='bold')

    # QEMU command
    ax.add_patch(FancyBboxPatch((0.3, 0.15), 15.4, 0.6,
                               boxstyle='round,pad=0.06', lw=1.5,
                               ec=GRAY, fc=GRAY+'18', zorder=2))
    ax.text(8.0, 0.45,
            "qemu-system-x86_64 -kernel /boot/vmlinuz -drive file=rootfs.img,format=raw "
            '-append "console=ttyS0 root=/dev/sda rw init=/sbin/init quiet" '
            "-nographic -m 128M -serial mon:stdio",
            ha='center', va='center', fontsize=7.5, color=BLK,
            fontfamily='monospace', zorder=3)

    # Performance badge
    ax.add_patch(FancyBboxPatch((0.3, 4.8), 5.5, 2.9,
                               boxstyle='round,pad=0.1', lw=2,
                               ec=GREEN, fc=GREEN+'12', zorder=3))
    ax.text(3.05, 7.5, "Performance vs Python reference",
            ha='center', fontsize=9.5, color=GREEN, fontweight='bold')
    perf = [
        ("Plan resolution time", "8 ms",   "vs 450 ms", "56×"),
        ("Peak memory usage",    "4 MB",   "vs 85 MB",  "21×"),
        ("Per-step overhead",    "0.2 ms", "vs 10 ms",  "50×"),
        ("Rootfs size",          "6.3 MB", "boots <2 s","—"),
    ]
    for i,(metric,val,cmp,factor) in enumerate(perf):
        y = 7.1 - i*0.58
        ax.text(0.6,  y, metric, fontsize=8.5, color=BLK)
        ax.text(3.5,  y, val,    fontsize=8.5, color=GREEN, fontweight='bold')
        ax.text(4.3,  y, cmp,    fontsize=8,   color=GRAY)
        if factor != "—":
            rbox(ax, 5.4, y, 0.7, 0.32, factor, GREEN, fs=8, bold=True)

    save(fig, 'fig8_1_boot_sequence.png')

# ═════════════════════════════════════════════════════════════════════════════
# DWM UI Mockup
# ═════════════════════════════════════════════════════════════════════════════
def fig_dwm():
    W, H = 19.2, 10.8   # 16:9 proportions
    fig, ax = plt.subplots(figsize=(W, H))
    ax.set_facecolor('#1a1a2e'); fig.patch.set_facecolor('#1a1a2e')
    ax.axis('off'); ax.set_xlim(0,W); ax.set_ylim(0,H)

    # ── DWM status bar ────────────────────────────────────────────────────
    bar_h = 0.52
    ax.add_patch(plt.Rectangle((0, H-bar_h), W, bar_h,
                               fc='#16213e', zorder=10))

    # tag buttons
    tags = ['1','2','3','4','5','6','7','8','9']
    for i,t in enumerate(tags):
        x = 0.12 + i*0.46
        active = (i == 0)
        fc = '#0f3460' if active else '#16213e'
        ec = '#4ecca3' if active else '#4ecca3'
        ax.add_patch(FancyBboxPatch((x-0.18, H-bar_h+0.05), 0.36, 0.42,
                                   boxstyle='round,pad=0.02',
                                   fc=fc, ec=ec, lw=1.5 if active else 0.8,
                                   zorder=11))
        ax.text(x, H-bar_h+0.26, t, ha='center', va='center',
                fontsize=10, color='#4ecca3' if active else '#8888aa',
                fontfamily='monospace', fontweight='bold', zorder=12)

    # layout mode indicator
    ax.text(4.8, H-bar_h+0.26, '[]=', ha='left', va='center',
            fontsize=11, color='#4ecca3', fontfamily='monospace',
            fontweight='bold', zorder=12)

    # window title in center
    ax.text(W/2, H-bar_h+0.26,
            "cogman-supervisor — Rogue Linux PID1  [RUNNING]",
            ha='center', va='center', fontsize=10.5,
            color='#e2e8f0', fontfamily='monospace', zorder=12)

    # status text right
    ax.text(W-0.3, H-bar_h+0.26,
            "CPU 0.1%  MEM 4.2MB  [heartbeat ✓] [ctl-probe ✓]  2025-05-20 14:32",
            ha='right', va='center', fontsize=9,
            color='#a0aec0', fontfamily='monospace', zorder=12)

    # separator line under bar
    ax.axhline(H-bar_h, color='#4ecca3', lw=1.5, zorder=10)

    content_y_top = H-bar_h
    content_h = content_y_top   # everything below bar down to 0

    # ── LEFT WINDOW: cogman-supervisor terminal ───────────────────────────
    split = W * 0.58
    lw_rect = plt.Rectangle((0, 0), split-1, content_h,
                             fc='#0d1117', ec='#4ecca3', lw=2, zorder=3)
    ax.add_patch(lw_rect)

    # terminal title bar
    ax.add_patch(plt.Rectangle((0, content_h-0.46), split-1, 0.46,
                               fc='#161b22', ec='none', zorder=4))
    # window buttons
    for xi,clr in enumerate(['#ff5f57','#febc2e','#28c840']):
        ax.add_patch(Circle((0.28+xi*0.4, content_h-0.23), 0.12,
                           fc=clr, ec='none', zorder=5))
    ax.text(split/2-0.5, content_h-0.23,
            "st  —  cogman-supervisor  [pid=1]",
            ha='center', va='center', fontsize=9.5,
            color='#8b949e', fontfamily='monospace', zorder=5)

    # terminal output lines
    lines_left = [
        ("#4ecca3", "cogman-supervisor v0.9.0 starting (PID 1)"),
        ("#8888aa", "→ mounting /proc      [procfs]"),
        ("#8888aa", "→ mounting /sys       [sysfs]"),
        ("#8888aa", "→ mounting /dev       [devtmpfs]"),
        ("#8888aa", "→ mounting /run       [tmpfs]"),
        ("#4ecca3", "→ loading services from /etc/cogman/services/"),
        ("#a0aec0", "  found: hello.service       [oneshot]"),
        ("#a0aec0", "  found: heartbeat.service   [process, restart=always]"),
        ("#a0aec0", "  found: ctl-probe.service   [oneshot]"),
        ("#a0aec0", "  found: shutdown.service    [oneshot]"),
        ("#4ecca3", "→ dependency graph resolved (4 services)"),
        ("#e2e8f0", "  starting: hello.service"),
        ("#28c840", "  ✓ hello.service       DONE  (exit=0)"),
        ("#e2e8f0", "  starting: heartbeat.service"),
        ("#28c840", "  ✓ heartbeat.service   RUNNING  (pid=42)"),
        ("#e2e8f0", "  starting: ctl-probe.service"),
        ("#28c840", "  ✓ ctl-probe.service   DONE  (exit=0)"),
        ("#28c840", "  ✓ shutdown.service    DONE  (exit=0)"),
        ("#4ecca3", "→ all verification services passed"),
        ("#8888aa", "─────────────────────────────────────────"),
        ("#e2e8f0", "supervisor entering main loop (100ms poll)"),
        ("#a0aec0", "  select(pipe_r=3, ctl_fd=4, timeout=100ms)"),
        ("#a0aec0", "  [heartbeat] pid=42  state=RUNNING  restarts=0"),
        ("#a0aec0", "  [heartbeat] pid=42  state=RUNNING  restarts=0"),
        ("#febc2e", "  [heartbeat] SIGCHLD received  pid=42 exit=0"),
        ("#febc2e", "  [heartbeat] restart=always → RESTARTING"),
        ("#28c840", "  [heartbeat] restarted  new_pid=43"),
        ("#a0aec0", "  [heartbeat] pid=43  state=RUNNING  restarts=1"),
        ("#4ecca3","$"),
    ]
    lh = 0.285
    for i, (clr, txt) in enumerate(lines_left):
        y = content_h - 0.65 - i*lh
        if y < 0.15: break
        ax.text(0.18, y, txt, ha='left', va='center',
                fontsize=8.5, color=clr.strip(),
                fontfamily='monospace', zorder=5)

    # cursor blink
    ax.add_patch(plt.Rectangle((0.18, 0.22), 0.12, 0.2,
                               fc='#4ecca3', ec='none', zorder=6))

    # ── RIGHT WINDOW: cogman-ctl list ─────────────────────────────────────
    rw_x = split+1
    rw_w = W - rw_x
    ax.add_patch(plt.Rectangle((rw_x, 0), rw_w, content_h,
                               fc='#0d1117', ec='#4ecca3', lw=2, zorder=3))

    # title bar
    ax.add_patch(plt.Rectangle((rw_x, content_h-0.46), rw_w, 0.46,
                               fc='#161b22', ec='none', zorder=4))
    for xi,clr in enumerate(['#ff5f57','#febc2e','#28c840']):
        ax.add_patch(Circle((rw_x+0.28+xi*0.4, content_h-0.23), 0.12,
                           fc=clr, ec='none', zorder=5))
    ax.text(rw_x + rw_w/2, content_h-0.23,
            "st  —  cogman-ctl",
            ha='center', va='center', fontsize=9.5,
            color='#8b949e', fontfamily='monospace', zorder=5)

    lines_right = [
        ("#a0aec0", "void@rogue-linux:~$ cogman-ctl list"),
        ("#8888aa", ""),
        ("#4ecca3", "NAME              STATE       PID    RESTARTS"),
        ("#4ecca3", "────────────────────────────────────────────"),
        ("#28c840", "heartbeat         RUNNING     43     1"),
        ("#a0aec0", "hello             DONE        —      0"),
        ("#a0aec0", "ctl-probe         DONE        —      0"),
        ("#a0aec0", "shutdown          DONE        —      0"),
        ("#8888aa", ""),
        ("#a0aec0", "void@rogue-linux:~$ cogman-ctl status heartbeat"),
        ("#8888aa", ""),
        ("#4ecca3", "Service:     heartbeat"),
        ("#a0aec0", "State:       RUNNING"),
        ("#a0aec0", "PID:         43"),
        ("#a0aec0", "Command:     /usr/bin/heartbeat"),
        ("#a0aec0", "Type:        process"),
        ("#a0aec0", "Restart:     always"),
        ("#a0aec0", "Restarts:    1"),
        ("#a0aec0", "Started:     2025-05-20 14:32:01"),
        ("#8888aa", ""),
        ("#a0aec0", "void@rogue-linux:~$ free -h"),
        ("#4ecca3", "        total   used   free"),
        ("#a0aec0", "Mem:    128Mi   4.2Mi  123Mi"),
        ("#8888aa", ""),
        ("#a0aec0", "void@rogue-linux:~$ ps aux"),
        ("#4ecca3", "PID  COMM                    STAT  RSS"),
        ("#a0aec0", "  1  cogman-supervisor        S     312K"),
        ("#a0aec0", " 43  heartbeat                S     148K"),
        ("#a0aec0", ""),
        ("#a0aec0", "void@rogue-linux:~$ _"),
    ]
    for i,(clr,txt) in enumerate(lines_right):
        y = content_h - 0.65 - i*lh
        if y < 0.15: break
        ax.text(rw_x+0.18, y, txt, ha='left', va='center',
                fontsize=8.5, color=clr,
                fontfamily='monospace', zorder=5)

    # Divider line between windows
    ax.add_patch(plt.Rectangle((split-1, 0), 2, content_h,
                               fc='#0d1117', ec='none', zorder=2))
    ax.axvline(split-0.5, color='#4ecca3', lw=1.5, ymin=0, ymax=(content_h)/H, zorder=6)
    ax.axvline(split+0.5, color='#4ecca3', lw=1.5, ymin=0, ymax=(content_h)/H, zorder=6)

    fig.text(0.5, 0.002,
             "Rogue Linux — DWM x11 Window Manager  ·  "
             "Left: cogman-supervisor PID1 boot log   ·   Right: cogman-ctl service inspection",
             ha='center', fontsize=9, color='#4ecca3', fontfamily='monospace')

    save(fig, 'extra_dwm_ui.png')

# ═════════════════════════════════════════════════════════════════════════════
# Terminal mockup
# ═════════════════════════════════════════════════════════════════════════════
def fig_terminal():
    W, H = 14, 9
    fig, ax = plt.subplots(figsize=(W, H))
    ax.set_facecolor('#0d1117'); fig.patch.set_facecolor('#0d1117')
    ax.axis('off'); ax.set_xlim(0,W); ax.set_ylim(0,H)

    # Window chrome
    ax.add_patch(FancyBboxPatch((0.1, 0.1), W-0.2, H-0.2,
                               boxstyle='round,pad=0.06',
                               fc='#0d1117', ec='#30363d', lw=2, zorder=1))

    # Title bar
    ax.add_patch(plt.Rectangle((0.1, H-0.62), W-0.2, 0.52,
                               fc='#161b22', ec='none', zorder=2))
    ax.add_patch(FancyBboxPatch((0.1, H-0.62), W-0.2, 0.52,
                               boxstyle='round,pad=0.0',
                               fc='#161b22', ec='#30363d', lw=0, zorder=2))
    # Traffic lights
    for xi,clr in enumerate(['#ff5f57','#febc2e','#28c840']):
        ax.add_patch(Circle((0.45+xi*0.38, H-0.36), 0.13,
                           fc=clr, ec='none', zorder=3))
    ax.text(W/2, H-0.36, "st  —  void@rogue-linux: ~",
            ha='center', va='center', fontsize=10,
            color='#8b949e', fontfamily='monospace', zorder=3)

    # Terminal content
    session = [
        # (color,  text)
        ("#4ecca3","void@rogue-linux:~$ uname -a"),
        ("#e2e8f0","Linux rogue-linux 6.1.0 #1 SMP x86_64 GNU/Linux"),
        ("#4ecca3",""),
        ("#4ecca3","void@rogue-linux:~$ cogman-planner --meta packages/cogman.toml --out /tmp/cogman.bin"),
        ("#4ecca3",""),
        ("#28c840","  ✓  cogman  v0.9.0"),
        ("#a0aec0","  →  loading metadata       packages/cogman.toml"),
        ("#a0aec0","  →  validating schema       OK"),
        ("#a0aec0","  →  resolving dependencies  musl-libc → linux-headers → kernel"),
        ("#a0aec0","  →  topological sort        6 packages"),
        ("#a0aec0","  →  checking policy         allow_write=[/tmp, /usr] ✓"),
        ("#a0aec0","  →  checking cache          FNV-1a: 0xdeadbeef (miss)"),
        ("#28c840","  ✓  plan written            /tmp/cogman.bin  (2048 bytes · 14 steps)"),
        ("#a0aec0","  →  elapsed                 8 ms   peak_mem 4.1 MB"),
        ("#4ecca3",""),
        ("#4ecca3","void@rogue-linux:~$ cogman-executor /tmp/cogman.bin"),
        ("#4ecca3",""),
        ("#a0aec0","  →  mmap /tmp/cogman.bin   (PROT_READ · MAP_PRIVATE)"),
        ("#a0aec0","  →  magic=CGM2PLAN  version=1  steps=14"),
        ("#a0aec0","  step  1/14  OP_MKDIR   /tmp/staging/usr/bin"),
        ("#a0aec0","  step  2/14  OP_MKDIR   /tmp/staging/etc/cogman/services"),
        ("#a0aec0","  step  3/14  OP_EXEC    ./configure --prefix=/usr"),
        ("#a0aec0","  step  4/14  OP_EXEC    make -j$(nproc)"),
        ("#a0aec0","  step  5/14  OP_EXEC    make install DESTDIR=/tmp/staging"),
        ("#a0aec0","  step  6/14  OP_COPY    cogman-supervisor → /tmp/staging/usr/bin/"),
        ("#a0aec0","  step  7/14  OP_COPY    cogman-executor   → /tmp/staging/usr/bin/"),
        ("#a0aec0","  step  8/14  OP_SYMLINK /tmp/staging/sbin/init → cogman-supervisor"),
        ("#a0aec0","  step  9/14  OP_CHMOD   /tmp/staging/usr/bin/cogman-supervisor 0755"),
        ("#28c840","  step 10/14  OP_COPY    hello.service → /tmp/staging/etc/cogman/services/"),
        ("#28c840","  step 11/14  OP_COPY    heartbeat.service → ..."),
        ("#28c840","  step 12/14  OP_COPY    ctl-probe.service → ..."),
        ("#28c840","  step 13/14  OP_COPY    shutdown.service  → ..."),
        ("#28c840","  step 14/14  OP_EXEC    mksquashfs /tmp/staging rootfs.sqsh"),
        ("#4ecca3",""),
        ("#28c840","  ✓  all 14 steps completed  exit=0"),
        ("#4ecca3",""),
        ("#4ecca3","void@rogue-linux:~$ ls -lh rootfs.sqsh"),
        ("#e2e8f0","-rw-r--r-- 1 void void 6.3M May 20 14:32 rootfs.sqsh"),
        ("#4ecca3",""),
        ("#4ecca3","void@rogue-linux:~$ _"),
    ]

    lh = 0.215
    y0 = H - 0.9
    for i,(clr,txt) in enumerate(session):
        y = y0 - i*lh
        if y < 0.2: break
        ax.text(0.3, y, txt, ha='left', va='center',
                fontsize=8.5, color=clr,
                fontfamily='monospace', zorder=3)

    # Cursor
    ax.add_patch(plt.Rectangle((0.3, 0.25), 0.12, 0.18,
                               fc='#4ecca3', ec='none', zorder=4))

    save(fig, 'extra_terminal.png')

if __name__ == '__main__':
    print("Part 4 …")
    fig8_1()
    fig_dwm()
    fig_terminal()
    print("Part 4 done.")
