"""Part 3: Figures 7.1 – 7.9"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Circle, Ellipse
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
        lx=None, ly=None, rad=0.0, ls='-', style='->'):
    ax.annotate('', xy=(x2,y2), xytext=(x1,y1),
                arrowprops=dict(arrowstyle=style, color=color, lw=lw,
                                connectionstyle=f'arc3,rad={rad}',
                                linestyle=ls), zorder=5)
    if label:
        mx = lx if lx is not None else (x1+x2)/2
        my = ly if ly is not None else (y1+y2)/2+0.08
        ax.text(mx, my, label, ha='center', va='bottom', fontsize=8,
                color=color, zorder=6,
                bbox=dict(fc=BG, ec='none', pad=1.5))

def rbox(ax, cx, cy, w, h, label, ec, fc=None, fs=9, bold=False, lw=1.8):
    if fc is None: fc = ec+'20'
    ax.add_patch(FancyBboxPatch((cx-w/2, cy-h/2), w, h,
                                boxstyle='round,pad=0.04', lw=lw,
                                ec=ec, fc=fc, zorder=3))
    ax.text(cx, cy, label, ha='center', va='center', fontsize=fs,
            fontweight='bold' if bold else 'normal', color=ec, zorder=4)

def dmd(ax, cx, cy, w, h, label, ec, fs=9):
    pts = np.array([[cx,cy+h/2],[cx+w/2,cy],[cx,cy-h/2],[cx-w/2,cy]])
    ax.add_patch(plt.Polygon(pts, closed=True, fc=ec+'22', ec=ec, lw=1.8, zorder=3))
    ax.text(cx, cy, label, ha='center', va='center', fontsize=fs,
            color=ec, fontweight='bold', zorder=4)

# ═════════════════════════════════════════════════════════════════════════════
# Figure 7.1  —  Dependency Graph Resolution
# ═════════════════════════════════════════════════════════════════════════════
def fig7_1():
    fig, ax = plt.subplots(figsize=(14, 9), facecolor=BG)
    ax.set_facecolor(BG); ax.axis('off')
    ax.set_xlim(0,14); ax.set_ylim(0,9)
    ax.set_title("Figure 7.1 — cogman-planner: Dependency Graph Resolution",
                 fontsize=12, fontweight='bold', color=NAVY, pad=8)

    nodes = {
        # name:     (cx,  cy,  color,  radius)
        'busybox':        (7.0,  7.8,  RUST,  0.7),
        'cogman-sup':     (3.0,  6.2,  TEAL,  0.7),
        'cogman-exec':    (7.0,  6.2,  TEAL,  0.7),
        'cogman-planner': (11.0, 6.2,  TEAL,  0.7),
        'musl-libc':      (2.0,  4.2,  NAVY,  0.7),
        'linux-headers':  (5.5,  4.2,  NAVY,  0.7),
        'busybox-sh':     (8.5,  4.2,  NAVY,  0.7),
        'gcc-runtime':    (12.0, 4.2,  NAVY,  0.7),
        'kernel':         (7.0,  2.2,  GRAY,  0.7),
    }

    for name,(cx,cy,clr,r) in nodes.items():
        ax.add_patch(Circle((cx,cy), r, fc=clr+'28', ec=clr, lw=2, zorder=3))
        ax.text(cx, cy, name, ha='center', va='center', fontsize=8,
                color=clr, fontweight='bold', zorder=4)

    edges = [
        ('busybox','musl-libc'),('busybox','linux-headers'),
        ('cogman-sup','musl-libc'),('cogman-sup','linux-headers'),
        ('cogman-exec','musl-libc'),('cogman-exec','linux-headers'),
        ('cogman-exec','busybox-sh'),
        ('cogman-planner','gcc-runtime'),('cogman-planner','linux-headers'),
        ('musl-libc','kernel'),('linux-headers','kernel'),
        ('gcc-runtime','kernel'),
        ('busybox-sh','busybox'),
    ]
    for s,d in edges:
        cx1,cy1,clr1,r1 = nodes[s]; cx2,cy2,clr2,r2 = nodes[d]
        dx=cx2-cx1; dy=cy2-cy1; dist=(dx**2+dy**2)**0.5
        ax.annotate('', xy=(cx2-r2*dx/dist, cy2-r2*dy/dist),
                    xytext=(cx1+r1*dx/dist, cy1+r1*dy/dist),
                    arrowprops=dict(arrowstyle='->', color=GRAY, lw=1.2,
                                   connectionstyle='arc3,rad=0.05'), zorder=2)

    # layer labels
    for y, lbl in [(7.8,'Root packages'),(6.2,'Direct deps'),
                   (4.2,'Transitive deps'),(2.2,'Base layer')]:
        ax.text(0.3, y, lbl, ha='left', va='center', fontsize=8.5,
                color=GRAY, style='italic')

    # FNV annotation
    ax.text(12.5, 8.3, "FNV-1a hash per\nmetadata file\n→ plan cache key",
            ha='center', fontsize=8.5, color=GOLD,
            bbox=dict(fc=GOLD+'22', ec=GOLD, pad=5, boxstyle='round'))

    save(fig, 'fig7_1_dep_graph.png')

# ═════════════════════════════════════════════════════════════════════════════
# Figure 7.2  —  Topological Sort (Kahn's Algorithm)
# ═════════════════════════════════════════════════════════════════════════════
def fig7_2():
    fig, ax = plt.subplots(figsize=(15, 8), facecolor=BG)
    ax.set_facecolor(BG); ax.axis('off')
    ax.set_xlim(0,15); ax.set_ylim(0,8)
    ax.set_title("Figure 7.2 — Dependency Topological Sort  (Kahn's Algorithm)",
                 fontsize=12, fontweight='bold', color=NAVY, pad=8)

    # LEFT: input DAG
    ax.add_patch(FancyBboxPatch((0.2,0.4),6.0,7.1, boxstyle='round,pad=0.1',
                                lw=1.5, ec=NAVY, fc=NAVY+'06', ls='--', zorder=0))
    ax.text(3.2, 7.3, "Input DAG  (package dependencies)", ha='center',
            fontsize=10, color=NAVY, fontweight='bold')

    dag = {
        'kernel':      (1.5, 5.8, GRAY),
        'linux-hdr':   (3.0, 5.8, GRAY),
        'gcc-rt':      (5.0, 5.8, GRAY),
        'musl-libc':   (2.0, 4.0, NAVY),
        'busybox':     (4.5, 4.0, RUST),
        'cogman-sup':  (3.0, 2.2, TEAL),
    }
    for name,(cx,cy,clr) in dag.items():
        ax.add_patch(Circle((cx,cy), 0.55, fc=clr+'28', ec=clr, lw=2, zorder=3))
        ax.text(cx,cy, name, ha='center', va='center', fontsize=7.5,
                color=clr, fontweight='bold', zorder=4)

    dag_edges = [
        ('musl-libc','kernel'),('musl-libc','linux-hdr'),
        ('busybox','linux-hdr'),('busybox','gcc-rt'),
        ('cogman-sup','musl-libc'),('cogman-sup','busybox'),
    ]
    for s,d in dag_edges:
        cx1,cy1,clr1=dag[s]; cx2,cy2,clr2=dag[d]
        dx=cx2-cx1; dy=cy2-cy1; dist=(dx**2+dy**2)**0.5
        ax.annotate('', xy=(cx2-0.55*dx/dist, cy2-0.55*dy/dist),
                    xytext=(cx1+0.55*dx/dist, cy1+0.55*dy/dist),
                    arrowprops=dict(arrowstyle='->', color=GRAY, lw=1.3,
                                   connectionstyle='arc3,rad=0.05'), zorder=2)

    # in-degree labels
    indeg = {'kernel':0,'linux-hdr':0,'gcc-rt':0,'musl-libc':2,'busybox':2,'cogman-sup':0}
    for name,(cx,cy,clr) in dag.items():
        ax.text(cx+0.5, cy+0.5, f"in={indeg[name]}", fontsize=7,
                color=clr, ha='center', bbox=dict(fc=BG,ec=clr,pad=1.5,boxstyle='round'))

    # Arrow middle
    ax.annotate("Kahn's\ntopo-sort", xy=(9.0,4.0), xytext=(7.2,4.0),
                arrowprops=dict(arrowstyle='->', color=BLK, lw=2.5),
                ha='center', fontsize=10, color=BLK, fontweight='bold',
                bbox=dict(fc=BG, ec=BLK, pad=5, boxstyle='round'))

    # RIGHT: sorted output
    ax.add_patch(FancyBboxPatch((9.5,0.4),5.3,7.1, boxstyle='round,pad=0.1',
                                lw=1.5, ec=GREEN, fc=GREEN+'06', ls='--', zorder=0))
    ax.text(12.15, 7.3, "Build Order  (topological sort)", ha='center',
            fontsize=10, color=GREEN, fontweight='bold')

    order = [
        ('kernel',    GRAY,  "base layer (no deps)"),
        ('linux-hdr', GRAY,  "base layer (no deps)"),
        ('gcc-rt',    GRAY,  "base layer (no deps)"),
        ('musl-libc', NAVY,  "depends on: kernel, linux-hdr"),
        ('busybox',   RUST,  "depends on: linux-hdr, gcc-rt"),
        ('cogman-sup',TEAL,  "depends on: musl-libc, busybox"),
    ]
    for i,(name,clr,reason) in enumerate(order):
        y = 6.5 - i*0.95
        ax.add_patch(FancyBboxPatch((9.7,y-0.33), 4.9, 0.66,
                                   boxstyle='round,pad=0.04', lw=1.5,
                                   ec=clr, fc=clr+'20', zorder=3))
        ax.text(10.0, y, f"{i+1}.  {name}", ha='left', va='center',
                fontsize=9, color=clr, fontweight='bold', zorder=4)
        ax.text(14.4, y, str(i+1), ha='right', va='center',
                fontsize=9, color=clr, fontweight='bold', zorder=4)
        ax.text(10.0, y-0.22, reason, ha='left', va='center',
                fontsize=7.5, color=GRAY, style='italic', zorder=4)

    save(fig, 'fig7_2_topo_sort.png')

# ═════════════════════════════════════════════════════════════════════════════
# Figure 7.3  —  cogman-executor Step Execution Loop
# ═════════════════════════════════════════════════════════════════════════════
def fig7_3():
    fig, ax = plt.subplots(figsize=(12, 14), facecolor=BG)
    ax.set_facecolor(BG); ax.axis('off')
    ax.set_xlim(0,12); ax.set_ylim(0,14)
    ax.set_title("Figure 7.3 — cogman-executor: Step Execution Loop",
                 fontsize=12, fontweight='bold', color=NAVY, pad=8)

    # Flow boxes (cx, cy, w, h, label, color, shape)
    steps = [
        (6.0, 13.0, 3.2, 0.6, "open(plan_path, O_RDONLY)",     TEAL,  'rect'),
        (6.0, 12.1, 3.2, 0.6, "mmap(file, PROT_READ)",          TEAL,  'rect'),
        (6.0, 11.1, 3.8, 0.7, "validate_header()\nmagic=CGM2PLAN  version=1", NAVY, 'rect'),
        (6.0, 10.0, 2.6, 0.7, "Invalid?",                       RED,   'dmd'),
        (6.0,  9.0, 2.0, 0.6, "i = 0",                          GRAY,  'rect'),
        (6.0,  8.0, 2.8, 0.7, "i < step_count?",                GOLD,  'dmd'),
        (6.0,  7.0, 3.2, 0.6, "load steps[i] via offset arith", TEAL,  'rect'),
        (6.0,  6.0, 2.8, 0.7, "steps[i].op?",                   NAVY,  'dmd'),
        # dispatch targets
        (2.5,  4.5, 3.0, 0.9, "exec_command()\nfork+exec /bin/sh -c cmd", RUST, 'rect'),
        (6.0,  4.5, 2.8, 0.9, "mkdir_p(path)\nrecursive create",          TEAL, 'rect'),
        (9.5,  4.5, 3.0, 0.9, "copy_recursive()\n+ path traversal guard", NAVY, 'rect'),
        # fail check
        (6.0,  3.1, 3.4, 0.7, "fail_policy==ABORT\n&& rc != 0?",          RED,  'dmd'),
        (6.0,  2.0, 2.4, 0.6, "i = i + 1",                                GRAY, 'rect'),
        # exit boxes
        (10.2, 3.1, 2.4, 0.7, "exit(2)\nABORT",                           RED,  'rect'),
        (6.0,  1.1, 3.0, 0.6, "munmap()  exit(0)",                        GREEN,'rect'),
    ]

    for cx,cy,w,h,lbl,clr,shp in steps:
        if shp == 'dmd':
            dmd(ax, cx, cy, w, h, lbl, clr, fs=8.5)
        else:
            rbox(ax, cx, cy, w, h, lbl, clr, fs=8.5)

    # Vertical spine arrows
    spine = [
        (13.0, 12.7), (12.7, 12.4), (12.4, 11.45),
        (11.45,10.35),(10.35, 9.35),(9.35,  8.35),
        (8.35,  7.3), (7.3,   6.35),
    ]
    for y1,y2 in spine:
        arr(ax, 6.0, y1, 6.0, y2, BLK, 1.5)

    # Invalid → abort label
    arr(ax, 7.3, 10.0, 9.8, 10.0, RED, 1.5, label='YES → exit(2)')

    # dispatch fan-out
    for (xdst, yoff) in [(2.5, 5.0),(6.0, 5.0),(9.5, 5.0)]:
        arr(ax, 6.0, 5.65, xdst, 4.95, NAVY, 1.3)
    ax.text(2.5, 5.85, "OP_EXEC", ha='center', fontsize=8, color=RUST)
    ax.text(6.0, 5.85, "OP_MKDIR", ha='center', fontsize=8, color=TEAL)
    ax.text(9.5, 5.85, "OP_COPY", ha='center', fontsize=8, color=NAVY)

    # converge to fail check
    for xsrc in [2.5, 6.0, 9.5]:
        arr(ax, xsrc, 4.05, 6.0, 3.45, GRAY, 1.2, rad=0.0)

    # fail YES → abort
    arr(ax, 7.7, 3.1, 9.0, 3.1, RED, 1.5, label='YES')

    # fail NO → i++
    arr(ax, 6.0, 2.75, 6.0, 2.3, GREEN, 1.5, label='NO', lx=6.4, ly=2.6)

    # i++ → check loop (loop-back arc)
    ax.annotate('', xy=(6.0, 7.65), xytext=(6.0, 1.7),
                arrowprops=dict(arrowstyle='->', color=GOLD, lw=1.5,
                                connectionstyle='arc3,rad=-0.6'), zorder=5)
    ax.text(4.3, 4.6, "loop back\n(next step)", ha='center', fontsize=8,
            color=GOLD, style='italic')

    # i >= step_count → exit
    arr(ax, 7.4, 8.0, 9.5, 8.0, GREEN, 1.5, label='NO  (done)')
    ax.annotate('', xy=(6.0, 1.4), xytext=(9.5, 8.0),
                arrowprops=dict(arrowstyle='->', color=GREEN, lw=1.5,
                                connectionstyle='arc3,rad=0.4'), zorder=5)

    save(fig, 'fig7_3_executor_loop.png')

# ═════════════════════════════════════════════════════════════════════════════
# Figure 7.4  —  Path Traversal Guard
# ═════════════════════════════════════════════════════════════════════════════
def fig7_4():
    fig, ax = plt.subplots(figsize=(13, 9), facecolor=BG)
    ax.set_facecolor(BG); ax.axis('off')
    ax.set_xlim(0,13); ax.set_ylim(0,9)
    ax.set_title('Figure 7.4 — Path Traversal Guard Logic  (copy_recursive)',
                 fontsize=12, fontweight='bold', color=NAVY, pad=8)

    # Flowchart  (cx, cy, w, h, label, color, shape)
    flow = [
        (5.5, 8.3, 3.8, 0.6, "copy_recursive(src, dst)",               TEAL, 'rect'),
        (5.5, 7.3, 4.2, 0.6, "split dst → path components[]",           NAVY, 'rect'),
        (5.5, 6.3, 3.2, 0.7, "more components?",                        GOLD, 'dmd'),
        (5.5, 5.3, 3.0, 0.7, 'component == ".." ?',                     RED,  'dmd'),
        (5.5, 4.3, 3.0, 0.7, "component has null\nbyte or '/'?",        RED,  'dmd'),
        (5.5, 3.3, 3.4, 0.6, "resolve & join path component",           GREEN,'rect'),
        (5.5, 2.3, 3.2, 0.6, "proceed: open / sendfile copy",           GREEN,'rect'),
    ]
    for cx,cy,w,h,lbl,clr,shp in flow:
        if shp=='dmd': dmd(ax,cx,cy,w,h,lbl,clr,fs=8.5)
        else:          rbox(ax,cx,cy,w,h,lbl,clr,fs=8.5)

    # vertical spine
    for y1,y2 in [(8.0,7.6),(7.6,7.0),(7.0,6.65),(6.65,5.65),(5.65,4.65),(4.65,3.65),(3.65,2.6)]:
        arr(ax, 5.5, y1, 5.5, y2, BLK, 1.5)

    # more components? NO → done
    arr(ax, 7.1, 6.3, 9.5, 6.3, GREEN, 1.5, label='NO  (all clean)')
    rbox(ax, 10.7, 6.3, 2.2, 0.6, "return 0\n(success)", GREEN, fs=8.5)

    # ".." YES → error
    arr(ax, 5.5, 4.97, 1.8, 4.97, RED, 1.5, label='YES', lx=3.3, ly=5.2)
    rbox(ax, 1.1, 4.97, 2.0, 0.75, "return\nERR_TRAVERSAL\nexit code 2", RED, fs=8)

    # null YES → error
    arr(ax, 7.0, 4.3, 9.5, 4.3, RED, 1.5, label='YES')
    rbox(ax, 10.7, 4.3, 2.2, 0.7, "return\nERR_BADPATH\nexit code 2", RED, fs=8)

    # NO labels
    ax.text(5.75, 5.0, "NO", fontsize=8.5, color=GREEN)
    ax.text(5.75, 4.0, "NO", fontsize=8.5, color=GREEN)

    # loop back (next component)
    ax.annotate('next\ncomponent', xy=(5.5, 6.0), xytext=(5.5, 3.0),
                arrowprops=dict(arrowstyle='->', color=GOLD, lw=1.3,
                                connectionstyle='arc3,rad=0.55'), zorder=5)
    ax.text(3.3, 4.5, "loop\nnext", ha='center', fontsize=8, color=GOLD, style='italic')

    # Examples table
    examples = [
        ("../etc/passwd",        RED,   "BLOCKED  — bare '..' component"),
        ("/tmp/staging/foo",     GREEN, "ALLOWED  — clean path"),
        ("/tmp/build/../shadow", RED,   "BLOCKED  — traversal via '..'"),
        ("/tmp/build/file.so",   GREEN, "ALLOWED  — normal install path"),
        ("file\x00name",         RED,   "BLOCKED  — embedded null byte"),
    ]
    ax.add_patch(FancyBboxPatch((0.2, 0.1), 12.6, 1.9,
                               boxstyle='round,pad=0.08', lw=1.5,
                               ec=GRAY, fc=GRAY+'12', zorder=2))
    ax.text(6.5, 1.85, "Example paths and outcomes:", ha='center',
            fontsize=9, color=GRAY, fontweight='bold')
    for i,(path,clr,verdict) in enumerate(examples):
        row = i % 3; col = i // 3
        x = 0.5 + col*6.5; y = 1.55 - row*0.44
        ax.text(x, y, path, fontsize=8, color=clr, fontfamily='monospace')
        ax.text(x+2.5, y, f"→  {verdict}", fontsize=8, color=clr)

    save(fig, 'fig7_4_path_guard.png')

# ═════════════════════════════════════════════════════════════════════════════
# Figure 7.5  —  SIGCHLD Self-Pipe
# ═════════════════════════════════════════════════════════════════════════════
def fig7_5():
    fig, ax = plt.subplots(figsize=(14, 8), facecolor=BG)
    ax.set_facecolor(BG); ax.axis('off')
    ax.set_xlim(0,14); ax.set_ylim(0,8)
    ax.set_title("Figure 7.5 — cogman-supervisor: SIGCHLD Self-Pipe Pattern",
                 fontsize=12, fontweight='bold', color=NAVY, pad=8)

    # Swim lanes
    lanes = [
        (6.7, 1.5, "Linux Kernel  /  Signal Delivery",            GRAY),
        (4.2, 1.5, "SIGCHLD Handler  (async · signal-safe only)",  ORG),
        (1.5, 1.5, "Main Loop  (select() · 100 ms timeout)",       TEAL),
    ]
    for yc, lh, lbl, clr in lanes:
        ax.add_patch(FancyBboxPatch((0.2, yc-lh/2), 13.6, lh,
                                   boxstyle='round,pad=0.1',
                                   lw=1.5, ec=clr, fc=clr+'10', zorder=0))
        ax.text(0.45, yc+0.55, lbl, fontsize=9, color=clr, fontweight='bold')

    # Pipe graphic
    rbox(ax, 7.0, 3.2, 2.8, 0.75, "pipe()\n[ pipe_r · pipe_w ]", ORG, fs=9)

    # Events
    rbox(ax, 2.0,  6.7, 2.6, 0.7, "child process\nexits", GRAY, fs=8.5)
    rbox(ax, 1.9,  4.2, 2.6, 0.75, "sigaction(SIGCHLD,\n  handler)", ORG, fs=8.5)
    rbox(ax, 5.5,  4.2, 3.2, 0.75, "write(pipe_w, '\\x01', 1)\nasync-signal-safe", ORG, fs=8.5)
    rbox(ax, 10.5, 1.5, 3.0, 0.75, "select(pipe_r,\n  timeout=100ms)", TEAL, fs=8.5)
    rbox(ax, 3.5,  1.5, 3.2, 0.75, "read(pipe_r) →\nwaitpid(-1, WNOHANG)", TEAL, fs=8.5)

    # Arrows
    arr(ax, 2.0, 6.35, 2.0, 4.58, GRAY, 1.8, label='SIGCHLD\ndelivered', ly=5.65)
    arr(ax, 3.2, 4.2, 3.9, 4.2, ORG, 1.8, label='handler fires')
    arr(ax, 7.1, 4.2, 7.1, 3.58, ORG, 1.5, label='', rad=0.0)
    arr(ax, 7.1, 2.82, 10.5, 1.88, ORG, 1.5, label='pipe_r\nreadable', lx=9.3, ly=2.65)
    arr(ax, 9.0, 1.5, 7.1, 1.5, TEAL, 1.8)
    arr(ax, 5.1, 1.5, 3.2, 1.5, TEAL, 1.8, label='update\nstate table', ly=1.8)

    # Return arrow (state update → supervisor loop continues)
    ax.annotate('100ms loop\ncontinues', xy=(11.8, 1.88), xytext=(11.8, 0.5),
                arrowprops=dict(arrowstyle='->', color=TEAL, lw=1.2),
                ha='center', fontsize=8, color=TEAL,
                bbox=dict(fc=TEAL+'22', ec=TEAL, pad=3, boxstyle='round'))

    # Key note
    ax.text(0.3, 0.25,
            "Key: write() is async-signal-safe (POSIX). "
            "waitpid() is NOT called from the handler — avoids reentrancy. "
            "select() wakes immediately when pipe_r becomes readable.",
            fontsize=8.5, color=GRAY, style='italic')

    save(fig, 'fig7_5_sigchld.png')

# ═════════════════════════════════════════════════════════════════════════════
# Figure 7.6  —  Service Lifecycle State Machine
# ═════════════════════════════════════════════════════════════════════════════
def fig7_6():
    fig, ax = plt.subplots(figsize=(14, 10), facecolor=BG)
    ax.set_facecolor(BG); ax.axis('off')
    ax.set_xlim(0,14); ax.set_ylim(0,10)
    ax.set_title("Figure 7.6 — Service Lifecycle State Machine",
                 fontsize=12, fontweight='bold', color=NAVY, pad=8)

    # states: (cx, cy, color, label)
    states = {
        'STOPPED':    (2.5,  7.5, GRAY),
        'STARTING':   (7.0,  7.5, NAVY),
        'RUNNING':    (11.5, 7.5, GREEN),
        'RESTARTING': (11.5, 4.5, ORG),
        'FAILED':     (2.5,  4.5, RED),
        'DONE':       (7.0,  2.0, PURP),
    }

    # Initial pseudo state
    ax.add_patch(Circle((2.5, 8.8), 0.25, fc=BLK, zorder=5))
    arr(ax, 2.5, 8.55, 2.5, 8.05, BLK, 2.0)

    r = 0.85
    for name,(cx,cy,clr) in states.items():
        ax.add_patch(Circle((cx,cy), r, fc=clr+'28', ec=clr, lw=2.5, zorder=3))
        ax.text(cx, cy, name, ha='center', va='center', fontsize=10,
                fontweight='bold', color=clr, zorder=4)

    # DONE is terminal (double circle)
    ax.add_patch(Circle((7.0,2.0), r+0.12, fill=False, ec=PURP, lw=2, ls='--', zorder=4))

    def st_arr(ax, src, dst, lbl, color=GRAY, rad=0.15):
        cx1,cy1,_=states[src]; cx2,cy2,_=states[dst]
        dx=cx2-cx1; dy=cy2-cy1; dist=(dx**2+dy**2)**0.5
        ax.annotate('', xy=(cx2-r*dx/dist, cy2-r*dy/dist),
                    xytext=(cx1+r*dx/dist, cy1+r*dy/dist),
                    arrowprops=dict(arrowstyle='->', color=color, lw=1.8,
                                   connectionstyle=f'arc3,rad={rad}'), zorder=5)
        mx=cx1+(cx2-cx1)*0.5; my=cy1+(cy2-cy1)*0.5
        off = 0.3
        ax.text(mx, my+off, lbl, ha='center', fontsize=8, color=color, zorder=6,
                bbox=dict(fc=BG+'CC', ec='none', pad=1.5))

    st_arr(ax,'STOPPED','STARTING',  "cmd_start()\ndeps satisfied", NAVY, 0.0)
    st_arr(ax,'STARTING','RUNNING',  "exec() OK\nPID live",         GREEN, 0.0)
    st_arr(ax,'RUNNING','RESTARTING',"SIGCHLD exit\nrestart=always", ORG, -0.25)
    st_arr(ax,'RESTARTING','STARTING',"restart_at\ndeadline passed", ORG, -0.25)
    st_arr(ax,'RUNNING','FAILED',    "exit≠0\nrestart=never",       RED,  0.2)
    st_arr(ax,'STARTING','FAILED',   "exec() failed",               RED,  0.3)
    st_arr(ax,'FAILED','STOPPED',    "cmd_reset()",                  GRAY, -0.25)
    st_arr(ax,'RUNNING','DONE',      "exit=0\noneshot",             PURP,  0.15)
    st_arr(ax,'STARTING','DONE',     "oneshot exits 0",             PURP, -0.15)
    # cmd_stop
    ax.annotate('', xy=(states['STOPPED'][0]+r, states['STOPPED'][1]),
                xytext=(states['RUNNING'][0]-r, states['RUNNING'][1]),
                arrowprops=dict(arrowstyle='->', color=GRAY, lw=1.5,
                                connectionstyle='arc3,rad=0.3'), zorder=5)
    ax.text(7.0, 8.55, "cmd_stop() · SIGTERM+SIGKILL", ha='center', fontsize=8,
            color=GRAY, bbox=dict(fc=BG+'CC', ec='none', pad=1))

    # max restart exceeded
    ax.annotate('max_restart\nexceeded → FAILED', xy=(11.5,3.6), xytext=(11.5,1.3),
                arrowprops=dict(arrowstyle='->', color=RED, lw=1.3),
                ha='center', fontsize=8.5, color=RED,
                bbox=dict(fc=RED+'22', ec=RED, pad=3, boxstyle='round'))

    save(fig, 'fig7_6_state_machine.png')

# ═════════════════════════════════════════════════════════════════════════════
# Figure 7.7  —  cogman-ctl Unix Socket Protocol
# ═════════════════════════════════════════════════════════════════════════════
def fig7_7():
    fig, ax = plt.subplots(figsize=(13, 8), facecolor=BG)
    ax.set_facecolor(BG); ax.axis('off')
    ax.set_xlim(0,13); ax.set_ylim(0,8)
    ax.set_title("Figure 7.7 — cogman-ctl Unix Domain Socket Protocol",
                 fontsize=12, fontweight='bold', color=NAVY, pad=8)

    # Client & server
    rbox(ax, 1.9, 7.0, 2.8, 0.9, "cogman-ctl\n(client)", GREEN, bold=True)
    rbox(ax, 11.1,7.0, 2.8, 0.9, "cogman-supervisor\n(server)", TEAL, bold=True)

    # Socket path
    rbox(ax, 6.5, 7.0, 4.6, 0.75,
         "/run/cogman-supervisor.sock  (AF_UNIX · SOCK_STREAM · chmod 0666)",
         PURP, fs=8.5)
    arr(ax, 2.8, 7.0, 4.2, 7.0, PURP, 1.3)
    arr(ax, 8.8, 7.0, 9.7, 7.0, PURP, 1.3)

    # Protocol exchange timeline
    exchanges = [
        # (y,   x1,    x2,   label,                           color, return)
        (5.8,  2.0, 11.0, "1. connect()",                    GREEN, False),
        (5.0,  2.0, 11.0, '2. send: "list\\n"',              GREEN, False),
        (4.1, 11.0,  2.0, '3. recv: "heartbeat RUNNING pid=42\\n...\\nOK\\n"', TEAL, True),
        (3.2,  2.0, 11.0, "4. close()",                      GREEN, False),
    ]
    for y,x1,x2,lbl,clr,ret in exchanges:
        sty = '<-' if ret else '->'
        ls  = 'dashed' if ret else 'solid'
        ax.annotate('', xy=(x2,y), xytext=(x1,y),
                    arrowprops=dict(arrowstyle=sty, color=clr, lw=1.8,
                                   linestyle=ls), zorder=4)
        ax.text((x1+x2)/2, y+0.1, lbl, ha='center', va='bottom',
                fontsize=8.5, color=clr, zorder=5,
                bbox=dict(fc=BG, ec='none', pad=1))

    # Lifelines
    for cx in [2.0, 11.0]:
        ax.plot([cx,cx],[6.55,2.8], color=GRAY, lw=1, ls=':', zorder=1)

    # Commands table
    ax.add_patch(FancyBboxPatch((0.2,0.2), 5.8, 2.3,
                               boxstyle='round,pad=0.08', lw=1.5,
                               ec=GREEN, fc=GREEN+'12', zorder=2))
    ax.text(0.5, 2.35, "Client command verbs:", fontsize=9.5,
            color=GREEN, fontweight='bold')
    cmds = [
        ("list",           "print all services + state"),
        ("status <name>",  "detailed info for one service"),
        ("start  <name>",  "start a STOPPED service"),
        ("stop   <name>",  "SIGTERM then SIGKILL"),
        ("restart <name>", "stop then start"),
    ]
    for i,(cmd,desc) in enumerate(cmds):
        y = 2.0 - i*0.38
        ax.text(0.4, y, cmd, fontsize=8.5, color=GREEN, fontfamily='monospace')
        ax.text(2.2, y, f"— {desc}", fontsize=8, color=GRAY)

    # Server options
    ax.add_patch(FancyBboxPatch((7.0,0.2), 5.8, 2.3,
                               boxstyle='round,pad=0.08', lw=1.5,
                               ec=TEAL, fc=TEAL+'12', zorder=2))
    ax.text(7.3, 2.35, "Server socket options:", fontsize=9.5,
            color=TEAL, fontweight='bold')
    opts = [
        "SO_RCVTIMEO = 2 seconds",
        "Non-blocking accept (one per loop tick)",
        "chmod 0666  (operator readable)",
        "Bind path: /run/cogman-supervisor.sock",
    ]
    for i,o in enumerate(opts):
        ax.text(7.3, 2.0 - i*0.38, f"• {o}", fontsize=8.5, color=TEAL)

    save(fig, 'fig7_7_ctl_protocol.png')

# ═════════════════════════════════════════════════════════════════════════════
# Figure 7.8  —  Messenger IPC Protocol (TLV)
# ═════════════════════════════════════════════════════════════════════════════
def fig7_8():
    fig, ax = plt.subplots(figsize=(14, 8), facecolor=BG)
    ax.set_facecolor(BG); ax.axis('off')
    ax.set_xlim(0,14); ax.set_ylim(0,8)
    ax.set_title("Figure 7.8 — Messenger IPC Protocol: Fixed Header + Variable Payload",
                 fontsize=12, fontweight='bold', color=NAVY, pad=8)

    # ── 16-byte header diagram ─────────────────────────────────────────────
    ax.text(0.4, 7.55, "16-byte Fixed Header:", fontsize=10, color=PURP, fontweight='bold')

    fields = [
        # (byte_start, byte_end, label, sublabel, color)
        (0,  4,  "magic[4]",     "0x434F4731\n'COG1'",    PURP),
        (4,  6,  "version",      "u16 = 1",               NAVY),
        (6,  8,  "msg_type",     "u16",                   NAVY),
        (8,  12, "payload_len",  "u32  (0…N)",            TEAL),
        (12, 16, "src_pid",      "u32",                   TEAL),
    ]
    total_bytes = 16
    ruler_w = 12.0; ruler_x0 = 0.4; ruler_y = 6.8
    bw = ruler_w / total_bytes  # width per byte

    # byte ruler
    for f_start, f_end, lbl, sub, clr in fields:
        fx = ruler_x0 + f_start*bw
        fw = (f_end - f_start)*bw
        ax.add_patch(FancyBboxPatch((fx+0.02, ruler_y-0.3), fw-0.04, 0.6,
                                   boxstyle='round,pad=0.02', lw=1.8,
                                   ec=clr, fc=clr+'30', zorder=3))
        ax.text(fx+fw/2, ruler_y+0.05, lbl, ha='center', va='center',
                fontsize=8.5, color=clr, fontweight='bold', zorder=4)
        ax.text(fx+fw/2, ruler_y-0.18, sub, ha='center', va='center',
                fontsize=7, color=clr, zorder=4)
        # byte numbers
        for b in range(f_start, f_end):
            ax.text(ruler_x0 + (b+0.5)*bw, ruler_y-0.45, str(b),
                    ha='center', fontsize=6.5, color=GRAY)

    # variable payload row
    ax.add_patch(FancyBboxPatch((ruler_x0+0.02, ruler_y-1.1), ruler_w-0.04, 0.5,
                               boxstyle='round,pad=0.02', lw=1.8, ls='dashed',
                               ec=GREEN, fc=GREEN+'20', zorder=3))
    ax.text(ruler_x0+ruler_w/2, ruler_y-0.85, "Variable-length Payload  (0 … payload_len bytes)",
            ha='center', va='center', fontsize=9, color=GREEN, fontweight='bold', zorder=4)
    ax.text(ruler_x0-0.1, ruler_y-0.3, "0", ha='right', fontsize=8, color=GRAY)
    ax.text(ruler_x0-0.1, ruler_y-0.88, "16", ha='right', fontsize=8, color=GRAY)

    # ── Message type table ─────────────────────────────────────────────────
    ax.add_patch(FancyBboxPatch((0.3, 0.2), 6.2, 3.8,
                               boxstyle='round,pad=0.1', lw=1.5,
                               ec=NAVY, fc=NAVY+'10', zorder=2))
    ax.text(3.4, 3.8, "Message Types  (msg_type field)", ha='center',
            fontsize=9.5, color=NAVY, fontweight='bold')
    mtypes = [
        ("0", "MSG_HEARTBEAT",  "Keepalive ping"),
        ("1", "MSG_HUD_ALERT",  "Status alert to terminal"),
        ("2", "MSG_POLICY_REQ", "Policy enforcement check"),
        ("3", "MSG_DATA_XFER",  "Binary data transfer"),
        ("4", "MSG_LOG_INFO",   "Structured log record"),
    ]
    for i,(code,name,desc) in enumerate(mtypes):
        y = 3.5 - i*0.64
        ax.text(0.6,  y, code, fontsize=9, color=PURP, fontfamily='monospace', fontweight='bold')
        ax.text(1.0,  y, name, fontsize=9, color=NAVY, fontfamily='monospace')
        ax.text(1.0, y-0.24, desc, fontsize=8, color=GRAY, style='italic')

    # ── Broker topology ────────────────────────────────────────────────────
    ax.add_patch(FancyBboxPatch((7.2, 0.2), 6.5, 3.8,
                               boxstyle='round,pad=0.1', lw=1.5,
                               ec=PURP, fc=PURP+'10', zorder=2))
    ax.text(10.45, 3.8, "Messenger Broker Topology", ha='center',
            fontsize=9.5, color=PURP, fontweight='bold')

    rbox(ax, 10.45, 2.8, 2.6, 0.75, "messenger\nbroker  :7201", PURP, bold=True)

    clients = [
        (8.1,  1.5, "cogman-sup\n(publisher)", TEAL),
        (10.45,1.5, "cogman-exec\n(publisher)", RUST),
        (12.8, 1.5, "log-collector\n(subscriber)", GREEN),
    ]
    for cx,cy,lbl,clr in clients:
        rbox(ax, cx, cy, 2.4, 0.7, lbl, clr, fs=8.5)
        arr(ax, cx, cy+0.35, 10.45, 2.42, clr, 1.3,
            style='<->' if 'subscriber' not in lbl else '->')

    save(fig, 'fig7_8_messenger.png')

# ═════════════════════════════════════════════════════════════════════════════
# Figure 7.9  —  Rootfs Directory Layout
# ═════════════════════════════════════════════════════════════════════════════
def fig7_9():
    fig, ax = plt.subplots(figsize=(14, 10), facecolor=BG)
    ax.set_facecolor(BG); ax.axis('off')
    ax.set_xlim(0,14); ax.set_ylim(0,10)
    ax.set_title("Figure 7.9 — Minimal Rootfs Directory Layout  (6.3 MB)",
                 fontsize=12, fontweight='bold', color=NAVY, pad=8)

    # Tree entries: (indent, name, color, is_dir, size_note)
    tree = [
        (0, "/",                                  BLK,   True,  "6.3 MB total"),
        (1, "sbin/",                              TEAL,  True,  ""),
        (2, "init",                               TEAL,  False, "→ symlink to cogman-supervisor"),
        (1, "bin/",                               NAVY,  True,  ""),
        (2, "sh",                                 NAVY,  False, "→ symlink to /bin/busybox"),
        (2, "busybox",                            NAVY,  False, "1.1 MB  multi-call binary"),
        (1, "usr/bin/",                           NAVY,  True,  ""),
        (2, "cogman-supervisor",                  TEAL,  False, "312 KB  (PID 1)"),
        (2, "cogman-executor",                    TEAL,  False, "180 KB"),
        (2, "cogman-planner",                     RUST,  False, "1.4 MB"),
        (2, "cogman-ctl",                         GREEN, False, "45 KB"),
        (1, "etc/",                               PURP,  True,  ""),
        (2, "cogman/",                            PURP,  True,  ""),
        (3, "services/",                          PURP,  True,  ""),
        (4, "hello.service",                      GREEN, False, "oneshot · no deps"),
        (4, "heartbeat.service",                  GREEN, False, "process · restart=always"),
        (4, "ctl-probe.service",                  GREEN, False, "oneshot · after=heartbeat"),
        (4, "shutdown.service",                   GREEN, False, "oneshot · last"),
        (1, "proc/",                              GRAY,  True,  "← procfs mount"),
        (1, "sys/",                               GRAY,  True,  "← sysfs mount"),
        (1, "dev/",                               GRAY,  True,  "← devtmpfs mount"),
        (1, "run/",                               ORG,   True,  "← tmpfs mount"),
        (2, "cogman-supervisor.sock",             ORG,   False, "AF_UNIX control socket"),
        (1, "lib/",                               GOLD,  True,  ""),
        (2, "libc.so",                            GOLD,  False, "→ musl-libc static"),
        (1, "tmp/",                               GRAY,  True,  ""),
    ]

    x0 = 0.5; indent_w = 0.55; y_start = 9.35; line_h = 0.32

    for i,(depth,name,clr,is_dir,note) in enumerate(tree):
        y = y_start - i*line_h
        x = x0 + depth*indent_w
        prefix = "" if depth==0 else ("├─ " if i < len(tree)-1 else "└─ ")
        style = 'bold' if is_dir else 'normal'
        ax.text(x, y, prefix+name, ha='left', va='center',
                fontsize=9, color=clr, fontfamily='monospace',
                fontweight=style)
        if note:
            ax.text(7.5, y, note, ha='left', va='center', fontsize=8,
                    color=GRAY, style='italic')

    # Size breakdown panel
    ax.add_patch(FancyBboxPatch((8.5,0.2), 5.2,3.9, boxstyle='round,pad=0.1',
                               lw=1.5, ec=NAVY, fc=NAVY+'0C', zorder=2))
    ax.text(11.1, 3.9, "Binary Sizes (ELF · stripped)", ha='center',
            fontsize=9.5, color=NAVY, fontweight='bold')
    sizes = [
        ("cogman-planner",    "1.40 MB", RUST),
        ("busybox",           "1.10 MB", NAVY),
        ("cogman-supervisor", " 312 KB", TEAL),
        ("cogman-executor",   " 180 KB", TEAL),
        ("cogman-ctl",        "  45 KB", GREEN),
        ("musl-libc (shared)","  90 KB", GOLD),
        ("service files (×4)","  <1 KB", PURP),
        ("────────────────",  "────────",""),
        ("Total rootfs",      "6.30 MB", BLK),
    ]
    for j,(name,sz,clr) in enumerate(sizes):
        y = 3.5 - j*0.38
        ax.text(8.8,  y, name, ha='left',  va='center', fontsize=8.5,
                color=clr if clr else GRAY)
        ax.text(13.5, y, sz,   ha='right', va='center', fontsize=8.5,
                color=clr if clr else GRAY, fontweight='bold' if j==len(sizes)-1 else 'normal')

    # Boot annotation
    ax.text(0.3, 0.3,
            "Boot: kernel → execve(/sbin/init) → cogman-supervisor (PID 1) "
            "→ mount {proc,sys,dev,run} → parse /etc/cogman/services/ "
            "→ start 4 verification services",
            fontsize=8.5, color=GRAY, style='italic')

    save(fig, 'fig7_9_rootfs_layout.png')

if __name__ == '__main__':
    print("Part 3 …")
    fig7_1(); fig7_2(); fig7_3(); fig7_4()
    fig7_5(); fig7_6(); fig7_7(); fig7_8(); fig7_9()
    print("Part 3 done.")
