"""Part 1: Figures 1.1, 1.2, 6.3, 6.4, 6.5, 6.6"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Circle, Ellipse, FancyArrowPatch
import numpy as np, os

OUT = os.path.dirname(os.path.abspath(__file__))

# ── palette ──────────────────────────────────────────────────────────────────
BG    = "#F8F9FA"
RUST  = "#C0392B"
TEAL  = "#0E6655"
NAVY  = "#1A3A5C"
GRAY  = "#5D6D7E"
GREEN = "#1E8449"
ORG   = "#CA6F1E"
RED   = "#922B21"
PURP  = "#6C3483"
GOLD  = "#9A7D0A"
BLK   = "#1C2833"

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'text.color':BLK})

def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=180, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    plt.close(fig)
    print("  saved", name)

# ── primitives ────────────────────────────────────────────────────────────────
def rect(ax, cx, cy, w, h, label, fc, ec, fs=9, bold=False, lw=1.8,
         corner=0.06, alpha=1.0, sublabel=None):
    r = FancyBboxPatch((cx-w/2, cy-h/2), w, h,
                       boxstyle=f"round,pad=0.01,rounding_size={corner}",
                       lw=lw, ec=ec, fc=fc, zorder=3, alpha=alpha)
    ax.add_patch(r)
    fw = 'bold' if bold else 'normal'
    if sublabel:
        ax.text(cx, cy+0.08, label, ha='center', va='center', fontsize=fs,
                fontweight=fw, color=ec, zorder=4)
        ax.text(cx, cy-0.13, sublabel, ha='center', va='center', fontsize=fs-1.5,
                color=GRAY, style='italic', zorder=4)
    else:
        ax.text(cx, cy, label, ha='center', va='center', fontsize=fs,
                fontweight=fw, color=ec, zorder=4)

def arr(ax, x1, y1, x2, y2, color=BLK, lw=1.6, label='',
        lx=None, ly=None, rad=0.0, ls='-', style='->'):
    ax.annotate('', xy=(x2,y2), xytext=(x1,y1),
                arrowprops=dict(arrowstyle=style, color=color, lw=lw,
                                connectionstyle=f'arc3,rad={rad}',
                                linestyle=ls), zorder=5)
    if label:
        mx = lx if lx is not None else (x1+x2)/2
        my = ly if ly is not None else (y1+y2)/2 + 0.07
        ax.text(mx, my, label, ha='center', va='bottom', fontsize=8.5,
                color=color, zorder=6,
                bbox=dict(fc=BG, ec='none', pad=1.5))

def diamond(ax, cx, cy, w, h, label, ec, fs=9):
    pts = np.array([[cx, cy+h/2],[cx+w/2, cy],[cx, cy-h/2],[cx-w/2, cy]])
    ax.add_patch(plt.Polygon(pts, closed=True, fc=ec+'22', ec=ec, lw=1.8, zorder=3))
    ax.text(cx, cy, label, ha='center', va='center', fontsize=fs,
            color=ec, fontweight='bold', zorder=4)

def htitle(fig, ax, text):
    ax.set_title(text, fontsize=12, fontweight='bold', color=NAVY, pad=10)

# ═════════════════════════════════════════════════════════════════════════════
# Figure 1.1  —  Build Pipeline Overview
# ═════════════════════════════════════════════════════════════════════════════
def fig1_1():
    fig, ax = plt.subplots(figsize=(16, 5.5), facecolor=BG)
    ax.set_facecolor(BG); ax.axis('off')
    ax.set_xlim(0,16); ax.set_ylim(0,5.5)
    htitle(fig, ax, "Figure 1.1 — Rogue Linux Build Pipeline Overview")

    # host boundary box
    ax.add_patch(FancyBboxPatch((0.2,0.6),15.6,4.1, boxstyle='round,pad=0.1',
                                lw=1.5, ec=GRAY, fc=GRAY+'08', ls='--', zorder=0))
    ax.text(0.55, 4.55, "HOST BUILD MACHINE", fontsize=9, color=GRAY, style='italic')

    boxes = [
        # cx   cy    w    h    label                    fc          ec
        (1.4,  2.7,  2.0, 1.4, "TOML\nPackage\nMetadata",  RUST+'18',  RUST),
        (4.4,  2.7,  2.4, 1.4, "cogman-planner\n(Rust)",    RUST+'18',  RUST),
        (7.4,  2.7,  2.2, 1.4, "CGM2PLAN\nBinary File",     NAVY+'22',  NAVY),
        (10.4, 2.7,  2.4, 1.4, "cogman-executor\n(C11)",     TEAL+'18',  TEAL),
        (13.6, 2.7,  2.2, 1.4, "Staged\nRoot FS",           GREEN+'18', GREEN),
    ]
    for cx,cy,w,h,lbl,fc,ec in boxes:
        rect(ax, cx, cy, w, h, lbl, fc, ec, fs=10, bold=True)

    # Arrows between boxes
    gaps = [(2.4,3.4),(5.6,6.3),(8.5,9.2),(11.6,12.5)]
    labels = ['parse &\nvalidate','emit binary\nplan','mmap &\ndispatch','install\nsteps']
    for (x1,x2),lbl in zip(gaps, labels):
        arr(ax, x1, 2.7, x2, 2.7, color=BLK, lw=2, label=lbl,
            ly=3.1)

    # Sub-labels below boxes
    sublabels = [
        (1.4, 1.75, "packages/foo.toml", RUST),
        (4.4, 1.75, "serde + toml → DAG", RUST),
        (7.4, 1.75, "64-byte hdr + step[]", NAVY),
        (10.4,1.75, "step dispatch table", TEAL),
        (13.6,1.75, "/tmp/staging/", GREEN),
    ]
    for cx,cy,lbl,clr in sublabels:
        ax.text(cx, cy, lbl, ha='center', va='center', fontsize=8,
                color=clr, style='italic')

    # Cache bypass annotation
    ax.annotate('FNV-1a cache → skip re-plan',
                xy=(7.4, 2.0), xytext=(7.4, 0.9),
                arrowprops=dict(arrowstyle='->', color=GOLD, lw=1.3),
                ha='center', fontsize=8.5, color=GOLD,
                bbox=dict(fc=GOLD+'22', ec=GOLD, pad=3, boxstyle='round'))

    # Path guard annotation
    ax.annotate('path traversal\nguard on OP_COPY',
                xy=(10.4, 2.0), xytext=(10.4, 0.85),
                arrowprops=dict(arrowstyle='->', color=RED, lw=1.3),
                ha='center', fontsize=8.5, color=RED,
                bbox=dict(fc=RED+'22', ec=RED, pad=3, boxstyle='round'))

    save(fig, 'fig1_1_build_pipeline.png')

# ═════════════════════════════════════════════════════════════════════════════
# Figure 1.2  —  Cogman Runtime Architecture
# ═════════════════════════════════════════════════════════════════════════════
def fig1_2():
    fig, ax = plt.subplots(figsize=(15, 9), facecolor=BG)
    ax.set_facecolor(BG); ax.axis('off')
    ax.set_xlim(0,15); ax.set_ylim(0,9)
    htitle(fig, ax, "Figure 1.2 — Cogman Runtime Architecture")

    # Rootfs boundary
    ax.add_patch(FancyBboxPatch((0.3,0.4),14.4,8.0, boxstyle='round,pad=0.1',
                                lw=2, ec=TEAL, fc=TEAL+'06', ls='--', zorder=0))
    ax.text(0.65, 8.2, "TARGET ROOTFS  (x86_64 · 6.3 MB)", fontsize=9.5,
            color=TEAL, fontweight='bold')

    # Kernel
    rect(ax, 7.5, 8.05, 5.0, 0.8, "Linux Kernel  (PID 0)", BLK+'22', GRAY,
         fs=11, bold=True)

    # Supervisor PID1
    rect(ax, 7.5, 6.85, 7.0, 0.95,
         "cogman-supervisor  (PID 1  ·  /sbin/init)",
         TEAL+'25', TEAL, fs=11, bold=True)

    arr(ax, 7.5, 7.65, 7.5, 7.35, color=GRAY, lw=2,
        label='execve /sbin/init', ly=7.55)

    # Service file input
    rect(ax, 2.2, 6.85, 3.0, 0.85,
         "/etc/cogman/services/\n*.service  (INI format)",
         NAVY+'20', NAVY, fs=8.5)
    arr(ax, 3.7, 6.85, 4.0, 6.85, color=NAVY, lw=1.5, label='parse', ly=7.0)

    # Control socket
    rect(ax, 13.2, 6.85, 2.8, 0.85,
         "/run/cogman-\nsupervisor.sock",
         PURP+'20', PURP, fs=8.5)
    arr(ax, 11.0, 6.85, 12.3, 6.85, color=PURP, lw=1.5,
        label='Unix SOCK_STREAM', ly=7.05)

    # Four services
    svcs = [
        (2.0,  4.5, "hello.service\n(oneshot)",          GREEN+'25', GREEN),
        (5.5,  4.5, "heartbeat.service\n(process·always)",TEAL+'25',  TEAL),
        (9.0,  4.5, "ctl-probe.service\n(oneshot)",       NAVY+'25',  NAVY),
        (12.5, 4.5, "shutdown.service\n(oneshot)",        RUST+'25',  RUST),
    ]
    for cx,cy,lbl,fc,ec in svcs:
        rect(ax, cx, cy, 2.9, 1.0, lbl, fc, ec, fs=8.5, bold=True)
        arr(ax, cx, 6.38, cx, 5.0, color=ec, lw=1.4,
            label='fork/exec', ly=5.75)

    # SIGCHLD self-pipe
    ax.annotate('SIGCHLD\nself-pipe', xy=(5.5, 6.0), xytext=(3.2, 5.3),
                arrowprops=dict(arrowstyle='->', color=ORG, lw=1.5,
                                connectionstyle='arc3,rad=-0.35'),
                ha='center', fontsize=8.5, color=ORG,
                bbox=dict(fc=ORG+'22', ec=ORG, pad=3, boxstyle='round'))

    # 100 ms main loop label
    ax.text(10.0, 6.45, "100 ms main loop  ·  select(pipe_r, ctl_fd)",
            ha='center', fontsize=8.5, color=TEAL, style='italic',
            bbox=dict(fc=TEAL+'12', ec=TEAL, pad=3, boxstyle='round'))

    # cogman-ctl client
    rect(ax, 13.2, 4.5, 2.8, 0.9, "cogman-ctl\n(client)", PURP+'22', PURP, fs=8.5)
    arr(ax, 13.2, 5.0, 13.2, 6.42, color=PURP, lw=1.4,
        label='connect sock', lx=13.7, ly=5.7)

    # State legend
    legend_el = [
        mpatches.Patch(fc=GREEN+'55', ec=GREEN, label='RUNNING'),
        mpatches.Patch(fc=TEAL+'55',  ec=TEAL,  label='STARTING'),
        mpatches.Patch(fc=ORG+'55',   ec=ORG,   label='RESTARTING'),
        mpatches.Patch(fc=RED+'55',   ec=RED,   label='FAILED'),
        mpatches.Patch(fc=PURP+'55',  ec=PURP,  label='DONE'),
    ]
    ax.legend(handles=legend_el, loc='lower left', fontsize=8.5,
              title='Service States', title_fontsize=9,
              framealpha=0.95, edgecolor=GRAY, ncol=5,
              bbox_to_anchor=(0.02, 0.01))

    save(fig, 'fig1_2_runtime_arch.png')

# ═════════════════════════════════════════════════════════════════════════════
# Figure 6.3  —  DFD Level 0 (Context Diagram)
# ═════════════════════════════════════════════════════════════════════════════
def fig6_3():
    fig, ax = plt.subplots(figsize=(13, 8), facecolor=BG)
    ax.set_facecolor(BG); ax.axis('off')
    ax.set_xlim(0,13); ax.set_ylim(0,8)
    htitle(fig, ax, "Figure 6.3 — DFD Level 0: Context Diagram")

    # Central process circle
    ax.add_patch(Circle((6.5,4.0), 1.6, fc=NAVY+'25', ec=NAVY, lw=2.5, zorder=3))
    ax.text(6.5, 4.2, "Cogman", ha='center', va='center', fontsize=13,
            fontweight='bold', color=NAVY, zorder=4)
    ax.text(6.5, 3.7, "Build + Runtime\nSystem", ha='center', va='center',
            fontsize=9, color=NAVY, zorder=4)

    # External entities (rectangles)
    ents = [
        (1.5, 6.5, "Package\nAuthor",        RUST,  3.0, 1.0),
        (1.5, 1.8, "Build System\nOperator", TEAL,  3.0, 1.0),
        (11.5,4.0, "Runtime\nOperator",      GREEN, 3.0, 1.0),
    ]
    for cx,cy,lbl,clr,w,h in ents:
        rect(ax, cx, cy, w, h, lbl, clr+'22', clr, fs=10, bold=True, lw=2)

    # Data stores
    stores = [
        (6.5, 1.2, "D1 — CGM2PLAN binary file"),
        (6.5, 0.55,"D2 — /etc/cogman/services/"),
    ]
    for cx,cy,lbl in stores:
        ax.add_patch(FancyBboxPatch((cx-2.2, cy-0.22), 4.4, 0.44,
                                   boxstyle='square,pad=0.02',
                                   lw=1.5, ec=GRAY, fc=GRAY+'15', zorder=2))
        ax.text(cx, cy, lbl, ha='center', va='center', fontsize=8.5, color=GRAY)

    # Arrows: Package Author → system
    arr(ax, 2.9, 6.2,  5.05, 4.9, RUST, 1.8,
        label='TOML package\nmetadata files', lx=3.5, ly=5.8)
    # Build Op → system
    arr(ax, 2.9, 1.9,  5.05, 3.1, TEAL, 1.8,
        label='invoke planner\n& executor', lx=3.5, ly=2.2)
    # system → Build Op
    arr(ax, 5.05, 2.9, 2.9, 1.7, TEAL, 1.5,
        label='build logs\n& plan file', lx=3.4, ly=2.5, rad=0.15)
    # Runtime Op ↔ system
    arr(ax, 7.95, 4.2, 10.05, 4.2, GREEN, 1.8,
        label='service commands\n(cogman-ctl)', ly=4.55)
    arr(ax, 10.05, 3.8, 7.95, 3.8, GREEN, 1.5,
        label='service status & logs', ly=3.5, rad=0.0)

    save(fig, 'fig6_3_dfd_level0.png')

# ═════════════════════════════════════════════════════════════════════════════
# Figure 6.4  —  DFD Level 1 (Build Subsystem)
# ═════════════════════════════════════════════════════════════════════════════
def fig6_4():
    fig, ax = plt.subplots(figsize=(16, 9), facecolor=BG)
    ax.set_facecolor(BG); ax.axis('off')
    ax.set_xlim(0,16); ax.set_ylim(0,9)
    htitle(fig, ax, "Figure 6.4 — DFD Level 1: Build Subsystem")

    # 5 process circles
    procs = [
        (2.0,  6.5, "1\nLoad &\nValidate\nMetadata",   RUST),
        (5.5,  6.5, "2\nResolve\nDep Graph",            NAVY),
        (9.0,  6.5, "3\nEnforce\nPolicy",               ORG),
        (12.5, 6.5, "4\nEmit\nBinary Plan",             TEAL),
        (14.5, 3.5, "5\nExecute\nPlan Steps",           GREEN),
    ]
    for cx,cy,lbl,clr in procs:
        ax.add_patch(Circle((cx,cy), 1.1, fc=clr+'22', ec=clr, lw=2, zorder=3))
        ax.text(cx, cy, lbl, ha='center', va='center', fontsize=8.5,
                color=clr, fontweight='bold', zorder=4)

    # Arrows between processes
    arr(ax, 3.1, 6.5, 4.4, 6.5, BLK, 1.6, label='PackageMetadata\nstruct', ly=7.15)
    arr(ax, 6.6, 6.5, 7.9, 6.5, BLK, 1.6, label='validated DAG\nnodes+edges', ly=7.15)
    arr(ax, 10.1,6.5, 11.4,6.5, BLK, 1.6, label='policy-approved\nDAG', ly=7.15)
    arr(ax, 13.6,6.5, 14.2,4.6, BLK, 1.6, label='CGM2PLAN\nfile path', lx=14.4, ly=5.6)

    # External entity: Package Author
    rect(ax, 2.0, 8.4, 2.8, 0.8, "Package Author", RUST+'22', RUST, fs=9, bold=True)
    arr(ax, 2.0, 8.0, 2.0, 7.6, RUST, 1.5, label='TOML files', ly=7.9)

    # Data stores (open-ended rectangles per DFD convention)
    def dstore(ax, cx, cy, w, lbl, clr):
        x = cx - w/2
        ax.add_patch(FancyBboxPatch((x, cy-0.28), w, 0.56,
                                   boxstyle='square,pad=0.0', lw=1.5,
                                   ec=clr, fc=clr+'18', zorder=2))
        # left wall
        ax.plot([x, x], [cy-0.28, cy+0.28], color=clr, lw=2.5, zorder=3)
        ax.text(cx+0.1, cy, lbl, ha='center', va='center', fontsize=8.5, color=clr)

    dstore(ax, 2.0,  4.8, 3.2, "D1 · packages/*.toml",     RUST)
    dstore(ax, 5.5,  4.2, 3.2, "D2 · dep graph cache",     NAVY)
    dstore(ax, 9.0,  4.8, 3.2, "D3 · policy rules",        ORG)
    dstore(ax, 12.5, 4.2, 3.2, "D4 · CGM2PLAN file",       TEAL)
    dstore(ax, 14.5, 1.7, 3.2, "D5 · staging rootfs",      GREEN)

    # Arrows process → store
    arr(ax, 2.0, 5.4, 2.0, 5.1, RUST, 1.2)
    arr(ax, 5.5, 5.4, 5.5, 4.5, NAVY, 1.2)
    arr(ax, 9.0, 5.4, 9.0, 5.1, ORG,  1.2)
    arr(ax, 12.5,5.4, 12.5,4.5, TEAL, 1.2)
    arr(ax, 14.5,2.4, 14.5,2.0, GREEN,1.2)

    # FNV cache bypass
    ax.annotate('FNV-1a cache hit\n→ skip processes 2–4',
                xy=(9.0, 6.5), xytext=(7.0, 4.0),
                arrowprops=dict(arrowstyle='->', color=GOLD, lw=1.5,
                                connectionstyle='arc3,rad=-0.2'),
                ha='center', fontsize=8.5, color=GOLD,
                bbox=dict(fc=GOLD+'22', ec=GOLD, pad=4, boxstyle='round'))

    save(fig, 'fig6_4_dfd_level1.png')

# ═════════════════════════════════════════════════════════════════════════════
# helpers for use-case diagrams
# ═════════════════════════════════════════════════════════════════════════════
def draw_actor(ax, cx, cy, name, color):
    r = 0.22
    ax.add_patch(Circle((cx, cy+1.1*r+0.55), r, fc=color+'33', ec=color, lw=1.8, zorder=4))
    for dx,dy in [((0,0),(0,-0.65)),
                  ((-0.32,0),(0.32,0)),
                  ((0,-0.65),(-0.28,-1.1)),
                  ((0,-0.65),( 0.28,-1.1))]:
        y_off = cy + 1.1*r + 0.55
        ax.plot([cx+dx[0], cx+dy[0]], [y_off+dx[1], y_off+dy[1]],
                color=color, lw=1.8, zorder=4)
    ax.text(cx, cy-0.5, name, ha='center', va='top', fontsize=8.5,
            color=color, fontweight='bold', zorder=4)

def draw_usecase(ax, cx, cy, w, h, text, color):
    ax.add_patch(Ellipse((cx,cy), w, h, fc=color+'18', ec=color, lw=1.5, zorder=3))
    ax.text(cx, cy, text, ha='center', va='center', fontsize=8.5, color=color, zorder=4)

# ═════════════════════════════════════════════════════════════════════════════
# Figure 6.5  —  Use Case: Build Subsystem
# ═════════════════════════════════════════════════════════════════════════════
def fig6_5():
    fig, ax = plt.subplots(figsize=(14, 9), facecolor=BG)
    ax.set_facecolor(BG); ax.axis('off')
    ax.set_xlim(0,14); ax.set_ylim(0,9)
    htitle(fig, ax, "Figure 6.5 — Use Case Diagram: Build Subsystem")

    # System boundary
    ax.add_patch(FancyBboxPatch((3.5, 0.5), 9.5, 8.0,
                                boxstyle='round,pad=0.1',
                                lw=2, ec=NAVY, fc=NAVY+'06', zorder=0))
    ax.text(8.25, 8.3, "Build Subsystem", ha='center', fontsize=11,
            color=NAVY, fontweight='bold')

    # Actors
    draw_actor(ax, 1.5, 4.8, "Package\nAuthor", RUST)
    draw_actor(ax, 1.5, 1.5, "Build\nOperator", TEAL)

    # Author use cases (left inside boundary)
    uc_author = [
        (5.8, 7.2, "Write Package\nMetadata (TOML)"),
        (5.8, 5.8, "Define Build\nSteps"),
        (5.8, 4.4, "Define Installer\nSteps"),
        (5.8, 3.0, "Declare\nDependencies"),
    ]
    for cx,cy,lbl in uc_author:
        draw_usecase(ax, cx, cy, 3.6, 0.9, lbl, RUST)
        ax.plot([2.0, cx-1.8], [5.6, cy], color=RUST, lw=1, ls='--', zorder=2)

    # Operator use cases (right inside boundary)
    uc_oper = [
        (10.8, 7.0, "Invoke\ncogman-planner"),
        (10.8, 5.5, "Invoke\ncogman-executor"),
        (10.8, 4.0, "Inspect Plan\nCache"),
        (10.8, 2.5, "Verify\nBuild Output"),
    ]
    for cx,cy,lbl in uc_oper:
        draw_usecase(ax, cx, cy, 3.6, 0.9, lbl, TEAL)
        ax.plot([2.0, cx-1.8], [2.2, cy], color=TEAL, lw=1, ls='--', zorder=2)

    # Include relationships
    for src,dst in [((5.8,7.2),(10.8,7.0)), ((5.8,3.0),(10.8,5.5))]:
        ax.annotate('', xy=(dst[0]-1.8, dst[1]), xytext=(src[0]+1.8, src[1]),
                    arrowprops=dict(arrowstyle='->', color=GRAY, lw=1,
                                   linestyle='dashed'), zorder=2)
        mx = (src[0]+dst[0])/2; my = (src[1]+dst[1])/2 + 0.18
        ax.text(mx, my, '«include»', ha='center', fontsize=7.5,
                color=GRAY, style='italic')

    save(fig, 'fig6_5_usecase_build.png')

# ═════════════════════════════════════════════════════════════════════════════
# Figure 6.6  —  Use Case: Runtime Supervisor
# ═════════════════════════════════════════════════════════════════════════════
def fig6_6():
    fig, ax = plt.subplots(figsize=(14, 9), facecolor=BG)
    ax.set_facecolor(BG); ax.axis('off')
    ax.set_xlim(0,14); ax.set_ylim(0,9)
    htitle(fig, ax, "Figure 6.6 — Use Case Diagram: Runtime Supervisor")

    ax.add_patch(FancyBboxPatch((3.5, 0.5), 9.5, 8.0,
                                boxstyle='round,pad=0.1',
                                lw=2, ec=TEAL, fc=TEAL+'06', zorder=0))
    ax.text(8.25, 8.3, "Runtime Supervisor  (cogman-supervisor)", ha='center',
            fontsize=11, color=TEAL, fontweight='bold')

    draw_actor(ax, 1.5, 5.5, "Runtime\nOperator", GREEN)
    draw_actor(ax, 12.5, 4.5, "Linux\nKernel", GRAY)

    uc_op = [
        (6.0, 7.2, "List Services\n(cogman-ctl list)"),
        (6.0, 5.8, "Start Service\n(cogman-ctl start)"),
        (6.0, 4.4, "Stop Service\n(cogman-ctl stop)"),
        (6.0, 3.0, "Query Status\n(cogman-ctl status)"),
    ]
    for cx,cy,lbl in uc_op:
        draw_usecase(ax, cx, cy, 3.8, 0.9, lbl, GREEN)
        ax.plot([2.0, cx-1.9], [6.2, cy], color=GREEN, lw=1, ls='--', zorder=2)

    uc_sys = [
        (10.5, 7.0, "Reap Orphan\nProcesses"),
        (10.5, 5.6, "Handle SIGCHLD\n(self-pipe)"),
        (10.5, 4.2, "Mount Virtual\nFilesystems"),
        (10.5, 2.8, "System Shutdown\n(SIGTERM/SIGINT)"),
    ]
    for cx,cy,lbl in uc_sys:
        draw_usecase(ax, cx, cy, 3.8, 0.9, lbl, GRAY)
        ax.plot([12.0, cx+1.9], [5.2, cy], color=GRAY, lw=1, ls='--', zorder=2)

    save(fig, 'fig6_6_usecase_runtime.png')

if __name__ == '__main__':
    print("Part 1 …")
    fig1_1(); fig1_2(); fig6_3(); fig6_4(); fig6_5(); fig6_6()
    print("Part 1 done.")
