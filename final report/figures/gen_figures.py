"""
Generate all figures for Rogue Linux Cogman Project Report.
Run from the figures/ directory: python3 gen_figures.py
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Ellipse, Arc
from matplotlib.patches import ConnectionPatch
import matplotlib.lines as mlines
import numpy as np
import os

OUT = os.path.dirname(os.path.abspath(__file__))

# ── Colour palette ────────────────────────────────────────────────────────────
C_RUST   = "#B7410E"   # Rust/planner
C_CYAN   = "#0D7377"   # executor / runtime
C_BLUE   = "#1A5276"   # dark navy boxes
C_GRAY   = "#2C3E50"   # background elements
C_LIGHT  = "#ECF0F1"   # light fill
C_GREEN  = "#1E8449"   # success / running
C_ORANGE = "#CA6F1E"   # warning / restarting
C_RED    = "#922B21"   # failed / error
C_PURPLE = "#6C3483"   # IPC / messenger
C_GOLD   = "#B7950B"   # highlight
C_BG     = "#FDFEFE"
C_DARK   = "#1C1C1C"

plt.rcParams.update({
    'figure.facecolor': C_BG,
    'axes.facecolor':   C_BG,
    'font.family':      'DejaVu Sans',
    'font.size':        11,
    'text.color':       C_DARK,
})

def save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  saved {name}")

def box(ax, x, y, w, h, label, color=C_BLUE, fc=None, fontsize=10,
        radius=0.04, bold=False, sub=None, lw=1.5, alpha=1.0):
    if fc is None:
        fc = color + "22"
    rect = FancyBboxPatch((x - w/2, y - h/2), w, h,
                          boxstyle=f"round,pad=0.02,rounding_size={radius}",
                          linewidth=lw, edgecolor=color, facecolor=fc, alpha=alpha, zorder=3)
    ax.add_patch(rect)
    weight = 'bold' if bold else 'normal'
    if sub:
        ax.text(x, y + 0.05, label, ha='center', va='center', fontsize=fontsize,
                fontweight=weight, color=color, zorder=4)
        ax.text(x, y - 0.12, sub, ha='center', va='center', fontsize=fontsize - 2,
                color=C_GRAY, style='italic', zorder=4)
    else:
        ax.text(x, y, label, ha='center', va='center', fontsize=fontsize,
                fontweight=weight, color=color, zorder=4)

def arrow(ax, x1, y1, x2, y2, label='', color=C_DARK, lw=1.5,
          style='->', labelpos=0.5, labeloffset=(0, 0.08)):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color, lw=lw,
                                connectionstyle='arc3,rad=0.0'),
                zorder=5)
    if label:
        mx = x1 + (x2-x1)*labelpos + labeloffset[0]
        my = y1 + (y2-y1)*labelpos + labeloffset[1]
        ax.text(mx, my, label, ha='center', va='bottom', fontsize=9,
                color=color, zorder=6,
                bbox=dict(fc=C_BG, ec='none', pad=1))

def title_box(fig, title, subtitle=''):
    fig.text(0.5, 0.97, title, ha='center', va='top', fontsize=13,
             fontweight='bold', color=C_BLUE)
    if subtitle:
        fig.text(0.5, 0.94, subtitle, ha='center', va='top', fontsize=10,
                 color=C_GRAY, style='italic')

# ══════════════════════════════════════════════════════════════════════════════
# Figure 1.1 — Build Pipeline Overview
# ══════════════════════════════════════════════════════════════════════════════
def fig1_1():
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.set_xlim(0, 14); ax.set_ylim(0, 5); ax.axis('off')
    title_box(fig, 'Figure 1.1 — Rogue Linux Build Pipeline Overview')

    stages = [
        (1.4, 2.5, 'TOML\nPackage\nMetadata', C_RUST, 'packages/foo.toml'),
        (3.8, 2.5, 'cogman-planner\n(Rust)', C_RUST, 'DAG + topo-sort → CGM2PLAN'),
        (6.2, 2.5, 'CGM2PLAN\nBinary Plan', C_BLUE, '64-byte header + step records'),
        (8.6, 2.5, 'cogman-executor\n(C11)', C_CYAN, 'mmap → step dispatch loop'),
        (11.0, 2.5, 'Staged\nRoot FS', C_GREEN, '/tmp/staging/'),
        (12.8, 2.5, 'rootfs\nArchive', C_GREEN, 'rootfs.tar.gz / ext4'),
    ]

    for x, y, lbl, clr, sub in stages:
        box(ax, x, y, 2.0, 1.2, lbl, color=clr, fontsize=9, bold=True, sub=sub)

    for i in range(len(stages) - 1):
        x1 = stages[i][0] + 1.0
        x2 = stages[i+1][0] - 1.0
        arrow(ax, x1, 2.5, x2, 2.5, color=C_DARK, lw=2)

    # Content-addressed cache annotation
    ax.annotate('FNV-1a cache\n(skip re-plan)', xy=(6.2, 1.9), xytext=(6.2, 1.0),
                arrowprops=dict(arrowstyle='->', color=C_ORANGE, lw=1.2),
                ha='center', fontsize=8.5, color=C_ORANGE,
                bbox=dict(fc=C_ORANGE+"22", ec=C_ORANGE, pad=3))

    # Security annotation
    ax.annotate('Path traversal\nguard (OP_COPY)', xy=(8.6, 1.9), xytext=(8.6, 0.9),
                arrowprops=dict(arrowstyle='->', color=C_RED, lw=1.2),
                ha='center', fontsize=8.5, color=C_RED,
                bbox=dict(fc=C_RED+"22", ec=C_RED, pad=3))

    # Top annotation
    ax.text(7.0, 4.4, 'HOST BUILD MACHINE', ha='center', fontsize=10,
            color=C_GRAY, style='italic',
            bbox=dict(fc=C_GRAY+"15", ec=C_GRAY, pad=5, boxstyle='round'))
    ax.add_patch(plt.Rectangle((0.2, 1.5), 13.6, 2.8, fill=False,
                               ec=C_GRAY, lw=1, ls='--', zorder=0))

    save(fig, 'fig1_1_build_pipeline.png')

# ══════════════════════════════════════════════════════════════════════════════
# Figure 1.2 — Cogman Runtime Architecture
# ══════════════════════════════════════════════════════════════════════════════
def fig1_2():
    fig, ax = plt.subplots(figsize=(13, 7))
    ax.set_xlim(0, 13); ax.set_ylim(0, 7); ax.axis('off')
    title_box(fig, 'Figure 1.2 — Cogman Runtime Architecture')

    # Kernel
    box(ax, 6.5, 6.3, 4, 0.8, 'Linux Kernel  (PID 0)', C_GRAY, bold=True, fontsize=11)
    # supervisor
    box(ax, 6.5, 5.1, 4.4, 0.8, 'cogman-supervisor  (PID 1 — /sbin/init)', C_CYAN, bold=True)
    arrow(ax, 6.5, 5.9, 6.5, 5.5, color=C_GRAY)

    # /etc/cogman/services/
    box(ax, 2.2, 5.1, 2.8, 0.7, '/etc/cogman/services/\n*.service  (INI)', C_BLUE, fontsize=9)
    arrow(ax, 3.6, 5.1, 4.3, 5.1, label='parse', color=C_BLUE, lw=1.2)

    # Control socket
    box(ax, 11.0, 5.1, 2.4, 0.7, '/run/cogman-\nsupervisor.sock', C_PURPLE, fontsize=9)
    arrow(ax, 10.73, 5.1, 9.8, 5.1, label='Unix IPC', color=C_PURPLE, lw=1.2, labeloffset=(0, 0.12))

    # Services row
    svcs = [
        (2.0,  3.3, 'hello.service\n(oneshot)', C_GREEN),
        (5.0,  3.3, 'heartbeat.service\n(process, always)', C_CYAN),
        (8.0,  3.3, 'ctl-probe.service\n(oneshot)', C_BLUE),
        (11.0, 3.3, 'shutdown.service\n(oneshot)', C_RUST),
    ]
    for x, y, lbl, clr in svcs:
        box(ax, x, y, 2.6, 0.9, lbl, clr, fontsize=8.5)
        arrow(ax, 6.5, 4.7, x, 3.77, color=clr, lw=1.2)

    # SIGCHLD self-pipe
    ax.annotate('', xy=(5.5, 4.5), xytext=(4.8, 3.77),
                arrowprops=dict(arrowstyle='->', color=C_ORANGE, lw=1.5,
                                connectionstyle='arc3,rad=-0.3'))
    ax.text(4.2, 4.2, 'SIGCHLD\nself-pipe', ha='center', fontsize=8, color=C_ORANGE)

    # 100ms loop
    loop = mpatches.FancyArrowPatch((8.5, 4.7), (8.5, 4.7),
                                    arrowstyle='->', color=C_GOLD, lw=1.2,
                                    connectionstyle='arc3,rad=0.8')
    ax.text(9.4, 4.55, '100 ms\nmain loop', ha='center', fontsize=8.5, color=C_GOLD)

    # cogman-ctl client
    box(ax, 11.0, 3.3, 2.4, 0.7, 'cogman-ctl\n(client)', C_PURPLE, fontsize=9)
    arrow(ax, 11.0, 4.73, 11.0, 3.65, label='connect', color=C_PURPLE, lw=1.2, labeloffset=(0.35, 0))

    # States legend
    legend_items = [
        mpatches.Patch(fc=C_GREEN+"44", ec=C_GREEN, label='RUNNING'),
        mpatches.Patch(fc=C_CYAN+"44",  ec=C_CYAN,  label='STARTING'),
        mpatches.Patch(fc=C_ORANGE+"44",ec=C_ORANGE, label='RESTARTING'),
        mpatches.Patch(fc=C_RED+"44",   ec=C_RED,    label='FAILED'),
    ]
    ax.legend(handles=legend_items, loc='lower left', fontsize=8.5,
              title='Service States', title_fontsize=9,
              framealpha=0.9, edgecolor=C_GRAY)

    # Rootfs boundary
    ax.add_patch(plt.Rectangle((0.2, 2.7), 12.6, 3.5, fill=False,
                               ec=C_GRAY, lw=1.2, ls='--', zorder=0))
    ax.text(0.5, 6.1, 'TARGET ROOTFS  (x86_64, 6.3 MB)', fontsize=9,
            color=C_GRAY, style='italic')

    save(fig, 'fig1_2_runtime_arch.png')

# ══════════════════════════════════════════════════════════════════════════════
# Figure 6.3 — DFD Level 0  (Context Diagram)
# ══════════════════════════════════════════════════════════════════════════════
def fig6_3():
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.set_xlim(0, 12); ax.set_ylim(0, 7); ax.axis('off')
    title_box(fig, 'Figure 6.3 — DFD Level 0: Context Diagram')

    # Central process
    circle = plt.Circle((6, 3.5), 1.5, fc=C_BLUE+"33", ec=C_BLUE, lw=2, zorder=3)
    ax.add_patch(circle)
    ax.text(6, 3.7, 'Cogman', ha='center', va='center', fontsize=12,
            fontweight='bold', color=C_BLUE, zorder=4)
    ax.text(6, 3.2, 'Build + Runtime\nSystem', ha='center', va='center',
            fontsize=9, color=C_BLUE, zorder=4)

    # External entities
    entities = [
        (1.4, 6.0, 'Package\nAuthor', C_RUST),
        (1.4, 1.0, 'Build System\nOperator', C_CYAN),
        (10.6, 3.5, 'Runtime\nOperator', C_GREEN),
    ]
    for x, y, lbl, clr in entities:
        rect = FancyBboxPatch((x-1.1, y-0.45), 2.2, 0.9,
                              boxstyle='round,pad=0.05', lw=2,
                              ec=clr, fc=clr+"22", zorder=3)
        ax.add_patch(rect)
        ax.text(x, y, lbl, ha='center', va='center', fontsize=10,
                fontweight='bold', color=clr, zorder=4)

    # Arrows: Package Author → system
    arrow(ax, 2.5, 5.7, 4.6, 4.5, label='TOML package\nmetadata', color=C_RUST,
          lw=1.5, labeloffset=(-0.5, 0.1))
    # Build Operator → system
    arrow(ax, 2.5, 1.2, 4.6, 2.7, label='invoke\nplanner/executor', color=C_CYAN,
          lw=1.5, labeloffset=(-0.6, 0.1))
    # system → Build Operator
    arrow(ax, 4.6, 2.5, 2.5, 1.0, label='build logs\n& plan file', color=C_CYAN,
          lw=1.5, labelpos=0.4, labeloffset=(0.55, 0.1))
    # Runtime Operator
    arrow(ax, 7.5, 3.6, 9.5, 3.6, label='service\ncommands', color=C_GREEN,
          lw=1.5, labeloffset=(0, 0.12))
    arrow(ax, 9.5, 3.3, 7.5, 3.3, label='service status\n& logs', color=C_GREEN,
          lw=1.5, labeloffset=(0.05, -0.22))

    # Data stores
    ax.text(6, 1.0, '[ D1 ] CGM2PLAN Binary File', ha='center', fontsize=9,
            color=C_GRAY,
            bbox=dict(fc=C_GRAY+"15", ec=C_GRAY, pad=4, boxstyle='square'))
    ax.text(6, 0.4, '[ D2 ] /etc/cogman/services/', ha='center', fontsize=9,
            color=C_GRAY,
            bbox=dict(fc=C_GRAY+"15", ec=C_GRAY, pad=4, boxstyle='square'))

    save(fig, 'fig6_3_dfd_level0.png')

# ══════════════════════════════════════════════════════════════════════════════
# Figure 6.4 — DFD Level 1  (Build Subsystem)
# ══════════════════════════════════════════════════════════════════════════════
def fig6_4():
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.set_xlim(0, 14); ax.set_ylim(0, 7); ax.axis('off')
    title_box(fig, 'Figure 6.4 — DFD Level 1: Build Subsystem')

    processes = [
        (1.8, 5.5, '1\nLoad &\nValidate\nMetadata', C_RUST),
        (4.5, 5.5, '2\nResolve\nDependency\nGraph', C_BLUE),
        (7.2, 5.5, '3\nEnforce\nPolicy', C_ORANGE),
        (9.9, 5.5, '4\nEmit\nBinary\nPlan', C_CYAN),
        (12.4, 5.5, '5\nExecute\nPlan\nSteps', C_GREEN),
    ]

    for x, y, lbl, clr in processes:
        circle = plt.Circle((x, y), 1.1, fc=clr+"22", ec=clr, lw=2, zorder=3)
        ax.add_patch(circle)
        ax.text(x, y, lbl, ha='center', va='center', fontsize=8.5,
                color=clr, fontweight='bold', zorder=4)

    # Arrows between processes
    for i in range(len(processes)-1):
        x1 = processes[i][0] + 1.1
        x2 = processes[i+1][0] - 1.1
        labels = ['PackageMeta', 'Validated DAG', 'Policy-OK DAG', 'CGM2PLAN file']
        arrow(ax, x1, 5.5, x2, 5.5, label=labels[i], color=C_DARK, lw=1.5)

    # External entity — Package Author
    rect = FancyBboxPatch((0.2, 6.2), 2.0, 0.7, boxstyle='round,pad=0.05',
                          lw=2, ec=C_RUST, fc=C_RUST+"22", zorder=3)
    ax.add_patch(rect)
    ax.text(1.2, 6.55, 'Package Author', ha='center', va='center', fontsize=9,
            color=C_RUST, fontweight='bold', zorder=4)
    arrow(ax, 1.2, 6.2, 1.8, 6.6, color=C_RUST)  # nope — downward
    ax.annotate('', xy=(1.8, 6.1), xytext=(1.2, 6.2),
                arrowprops=dict(arrowstyle='->', color=C_RUST, lw=1.5))

    # Data stores (horizontal bars)
    stores = [
        (1.8, 3.3, 'D1 — packages/*.toml', C_RUST),
        (4.5, 2.5, 'D2 — package DAG cache', C_BLUE),
        (9.9, 3.3, 'D3 — CGM2PLAN file', C_CYAN),
        (12.4, 2.5, 'D4 — staging rootfs', C_GREEN),
    ]
    for x, y, lbl, clr in stores:
        ax.add_patch(plt.Rectangle((x-1.5, y-0.25), 3.0, 0.5,
                                   fc=clr+"15", ec=clr, lw=1.5, zorder=3))
        ax.text(x, y, lbl, ha='center', va='center', fontsize=8.5,
                color=clr, zorder=4)

    # Arrows to/from stores
    for (px, py, _, pc), (sx, sy, _, sc) in zip(processes, stores):
        arrow(ax, px, py-1.1, sx, sy+0.25, color=C_GRAY, lw=1, style='->')

    # FNV cache bypass
    ax.annotate('FNV-1a\ncache hit\n→ skip', xy=(9.9, 4.4), xytext=(7.8, 3.5),
                arrowprops=dict(arrowstyle='->', color=C_GOLD, lw=1.2,
                                connectionstyle='arc3,rad=-0.3'),
                ha='center', fontsize=8, color=C_GOLD,
                bbox=dict(fc=C_GOLD+"22", ec=C_GOLD, pad=2))

    save(fig, 'fig6_4_dfd_level1.png')

# ══════════════════════════════════════════════════════════════════════════════
# Figure 6.5 — Use Case Diagram — Build Subsystem
# ══════════════════════════════════════════════════════════════════════════════
def actor(ax, x, y, label, color=C_BLUE, fontsize=9):
    ax.add_patch(Circle((x, y+0.55), 0.18, fc=color+"33", ec=color, lw=1.5, zorder=4))
    ax.plot([x, x], [y+0.37, y+0.05], color=color, lw=1.5, zorder=4)
    ax.plot([x-0.22, x+0.22], [y+0.30, y+0.30], color=color, lw=1.5, zorder=4)
    ax.plot([x, x-0.22], [y+0.05, y-0.2], color=color, lw=1.5, zorder=4)
    ax.plot([x, x+0.22], [y+0.05, y-0.2], color=color, lw=1.5, zorder=4)
    ax.text(x, y-0.35, label, ha='center', va='top', fontsize=fontsize,
            color=color, fontweight='bold', zorder=4)

def usecase(ax, x, y, w, h, label, color=C_BLUE, fontsize=9):
    ax.add_patch(Ellipse((x, y), w, h, fc=color+"22", ec=color, lw=1.5, zorder=3))
    ax.text(x, y, label, ha='center', va='center', fontsize=fontsize,
            color=color, zorder=4, wrap=True)

def fig6_5():
    fig, ax = plt.subplots(figsize=(13, 8))
    ax.set_xlim(0, 13); ax.set_ylim(0, 8); ax.axis('off')
    title_box(fig, 'Figure 6.5 — Use Case Diagram: Build Subsystem')

    # System boundary
    ax.add_patch(plt.Rectangle((3.0, 0.5), 8.5, 7.0, fill=False,
                               ec=C_GRAY, lw=2, ls='-', zorder=0))
    ax.text(7.25, 7.3, 'Build Subsystem', ha='center', fontsize=11,
            color=C_GRAY, fontweight='bold')

    # Actors
    actor(ax, 1.2, 5.0, 'Package\nAuthor', C_RUST)
    actor(ax, 1.2, 2.0, 'Build\nOperator', C_CYAN)

    # Use cases — Package Author
    uc_author = [
        (5.5, 6.5, 'Write Package\nMetadata (TOML)', C_RUST),
        (5.5, 5.2, 'Define Build\nSteps', C_RUST),
        (5.5, 3.9, 'Define Installer\nSteps', C_RUST),
        (5.5, 2.6, 'Declare\nDependencies', C_RUST),
    ]
    for x, y, lbl, clr in uc_author:
        usecase(ax, x, y, 3.5, 0.8, lbl, clr)
        ax.plot([1.5, x-1.75], [5.7, y], color=clr, lw=1, ls='--', zorder=2)

    # Use cases — Build Operator
    uc_oper = [
        (9.5, 6.2, 'Invoke\ncogman-planner', C_CYAN),
        (9.5, 4.7, 'Invoke\ncogman-executor', C_CYAN),
        (9.5, 3.2, 'Inspect Plan\nCache', C_CYAN),
        (9.5, 1.7, 'Verify\nBuild Output', C_CYAN),
    ]
    for x, y, lbl, clr in uc_oper:
        usecase(ax, x, y, 3.5, 0.8, lbl, clr)
        ax.plot([1.5, x-1.75], [2.7, y], color=clr, lw=1, ls='--', zorder=2)

    # Include / extend
    ax.annotate('<<include>>', xy=(9.5, 5.95), xytext=(5.5, 6.5),
                arrowprops=dict(arrowstyle='->', color=C_DARK, lw=1, ls='--'),
                ha='center', fontsize=7.5, color=C_DARK)
    ax.annotate('<<include>>', xy=(9.5, 4.45), xytext=(5.5, 3.9),
                arrowprops=dict(arrowstyle='->', color=C_DARK, lw=1, ls='--'),
                ha='center', fontsize=7.5, color=C_DARK)

    save(fig, 'fig6_5_usecase_build.png')

# ══════════════════════════════════════════════════════════════════════════════
# Figure 6.6 — Use Case Diagram — Runtime Supervisor
# ══════════════════════════════════════════════════════════════════════════════
def fig6_6():
    fig, ax = plt.subplots(figsize=(13, 8))
    ax.set_xlim(0, 13); ax.set_ylim(0, 8); ax.axis('off')
    title_box(fig, 'Figure 6.6 — Use Case Diagram: Runtime Supervisor')

    ax.add_patch(plt.Rectangle((3.0, 0.5), 8.5, 7.0, fill=False,
                               ec=C_GRAY, lw=2, zorder=0))
    ax.text(7.25, 7.3, 'Runtime Supervisor  (cogman-supervisor)', ha='center',
            fontsize=11, color=C_GRAY, fontweight='bold')

    actor(ax, 1.2, 5.5, 'Runtime\nOperator', C_GREEN)
    actor(ax, 11.8, 4.0, 'Linux\nKernel', C_GRAY, fontsize=8.5)

    uc_op = [
        (5.5, 6.3, 'List Services\n(cogman-ctl list)', C_GREEN),
        (5.5, 5.0, 'Start/Stop Service\n(cogman-ctl start/stop)', C_GREEN),
        (5.5, 3.7, 'Query Status\n(cogman-ctl status)', C_GREEN),
        (5.5, 2.4, 'Monitor Logs\n(cogman-ctl logs)', C_GREEN),
    ]
    for x, y, lbl, clr in uc_op:
        usecase(ax, x, y, 3.8, 0.8, lbl, clr)
        ax.plot([1.5, x-1.9], [6.0, y], color=clr, lw=1, ls='--', zorder=2)

    uc_sys = [
        (9.5, 6.3, 'Reap Orphan\nProcesses', C_GRAY),
        (9.5, 4.8, 'Handle\nSIGCHLD (self-pipe)', C_GRAY),
        (9.5, 3.3, 'Mount Virtual\nFilesystems', C_GRAY),
        (9.5, 1.8, 'Shutdown System\n(SIGTERM/SIGINT)', C_GRAY),
    ]
    for x, y, lbl, clr in uc_sys:
        usecase(ax, x, y, 3.6, 0.8, lbl, clr)
        ax.plot([11.5, x+1.8], [4.5, y], color=clr, lw=1, ls='--', zorder=2)

    save(fig, 'fig6_6_usecase_runtime.png')

# ══════════════════════════════════════════════════════════════════════════════
# Figure 6.7 — Class Diagram — Planner
# ══════════════════════════════════════════════════════════════════════════════
def class_box(ax, x, y, w, title, fields, methods, color=C_BLUE, fontsize=8.5):
    line_h = 0.28
    n_fields = len(fields); n_methods = len(methods)
    total_h = 0.45 + line_h*n_fields + 0.08 + line_h*n_methods + 0.1
    top = y + total_h / 2

    # outer rect
    ax.add_patch(FancyBboxPatch((x - w/2, y - total_h/2), w, total_h,
                                boxstyle='round,pad=0.02',
                                lw=1.5, ec=color, fc=C_BG, zorder=3))
    # title bar
    ax.add_patch(FancyBboxPatch((x - w/2, top - 0.45), w, 0.45,
                                boxstyle='round,pad=0.02',
                                lw=0, ec=color, fc=color+"44", zorder=4))
    ax.text(x, top - 0.22, title, ha='center', va='center', fontsize=fontsize,
            fontweight='bold', color=color, zorder=5)

    cur = top - 0.45
    # separator
    ax.plot([x - w/2, x + w/2], [cur, cur], color=color, lw=0.8, zorder=4)
    for f in fields:
        cur -= line_h
        ax.text(x - w/2 + 0.08, cur + line_h/2, f, ha='left', va='center',
                fontsize=fontsize - 1, color=C_DARK, zorder=5)
    cur -= 0.08
    ax.plot([x - w/2, x + w/2], [cur, cur], color=color, lw=0.8, ls='--', zorder=4)
    for m in methods:
        cur -= line_h
        ax.text(x - w/2 + 0.08, cur + line_h/2, m, ha='left', va='center',
                fontsize=fontsize - 1.5, color=C_GRAY, style='italic', zorder=5)

def fig6_7():
    fig, ax = plt.subplots(figsize=(15, 9))
    ax.set_xlim(0, 15); ax.set_ylim(0, 9); ax.axis('off')
    title_box(fig, 'Figure 6.7 — Class Diagram: cogman-planner (Rust)')

    class_box(ax, 1.5, 7.5, 2.6, 'Cli',
              ['cmd: Command'],
              ['+run() → Result'], C_RUST)
    class_box(ax, 4.5, 7.5, 2.8, 'Command',
              ['Build { meta, out }', 'Install { meta }', 'Deploy { plan }'],
              [], C_RUST)
    class_box(ax, 7.8, 8.0, 3.2, 'PackageMetadata',
              ['identity: Identity', 'builder: Builder',
               'installer: Installer', 'policy: Policy', 'depends: Vec<String>'],
              ['+load(path) → Result',
               '+validate() → Result'], C_BLUE)
    class_box(ax, 11.8, 8.0, 2.8, 'Identity',
              ['name: String', 'version: String',
               'category: String', 'source: String'],
              [], C_BLUE)
    class_box(ax, 7.8, 5.3, 3.0, 'DependencyGraph',
              ['nodes: HashMap<String, Node>',
               'edges: Vec<(String,String)>'],
              ['+add_node()', '+add_edge()',
               '+topo_sort() → Vec<String>',
               '+detect_cycles() → bool'], C_CYAN)
    class_box(ax, 3.8, 5.0, 3.0, 'RecursiveLoader',
              ['visited: HashSet<String>',
               'base_dir: PathBuf'],
              ['+load(pkg) → PackageMetadata',
               '+load_all() → Vec<Meta>'], C_CYAN)
    class_box(ax, 11.5, 5.3, 2.8, 'PlanWriter',
              ['steps: Vec<PlanStep>',
               'string_table: Vec<u8>',
               'cache: FnvHashMap'],
              ['+add_step()',
               '+emit(path) → Result'], C_GREEN)
    class_box(ax, 7.8, 2.8, 3.0, 'PlanStep',
              ['op: OpCode', 'fail_policy: FailPolicy',
               'cmd_off: u32', 'workdir_off: u32'],
              [], C_GREEN)
    class_box(ax, 3.8, 2.5, 2.8, 'Policy',
              ['allow_write: Vec<PathBuf>',
               'allow_network: bool',
               'allow_exec: Vec<String>'],
              ['+check(path) → bool'], C_ORANGE)

    # Relationships
    def rel(ax, x1, y1, x2, y2, style='->'):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle=style, color=C_GRAY, lw=1.2,
                                    connectionstyle='arc3,rad=0.0'), zorder=5)

    rel(ax, 2.3, 7.5, 3.6, 7.5)              # Cli → Command
    rel(ax, 5.0, 7.5, 6.5, 8.0)              # Command → PackageMetadata
    rel(ax, 9.4, 8.0, 10.4, 8.0)             # PackageMeta → Identity
    rel(ax, 7.8, 7.1, 7.8, 6.2)             # PackageMeta → DependencyGraph
    rel(ax, 5.0, 5.0, 6.3, 5.3, '-|>')      # RecursiveLoader extends
    rel(ax, 9.3, 5.3, 10.1, 5.3)            # DependencyGraph → PlanWriter
    rel(ax, 11.5, 4.4, 9.3, 3.3)            # PlanWriter → PlanStep
    rel(ax, 5.6, 5.0, 6.3, 3.2, '->')       # RecursiveLoader → Policy

    save(fig, 'fig6_7_class_planner.png')

# ══════════════════════════════════════════════════════════════════════════════
# Figure 6.8 — Class Diagram — Supervisor
# ══════════════════════════════════════════════════════════════════════════════
def fig6_8():
    fig, ax = plt.subplots(figsize=(15, 9))
    ax.set_xlim(0, 15); ax.set_ylim(0, 9); ax.axis('off')
    title_box(fig, 'Figure 6.8 — Class Diagram: cogman-supervisor (C11)')

    class_box(ax, 3.0, 7.8, 3.4, 'Supervisor  [singleton]',
              ['svc_table: Service[64]', 'svc_count: int',
               'sigchld_pipe: int[2]', 'ctl_fd: int', 'running: bool'],
              ['+init()', '+run_loop()',
               '+drain_sigchld()', '+reap_children()',
               '+shutdown()'], C_CYAN)

    class_box(ax, 8.5, 7.8, 3.6, 'Service',
              ['name: char[64]', 'command: char[256]',
               'type: SvcType', 'restart: SvcRestart',
               'state: SvcState', 'pid: pid_t',
               'restart_count: int', 'deps: char[8][64]'],
              ['+start()', '+stop()',
               '+on_exit(status)'], C_BLUE)

    class_box(ax, 3.0, 4.8, 3.0, 'SvcType  [enum]',
              ['PROCESS = 0', 'ONESHOT = 1', 'FORKING = 2'],
              [], C_PURPLE)

    class_box(ax, 7.0, 4.5, 3.0, 'SvcState  [enum]',
              ['STOPPED', 'STARTING', 'RUNNING',
               'RESTARTING', 'FAILED', 'DONE'],
              [], C_ORANGE)

    class_box(ax, 11.2, 4.5, 2.8, 'SvcRestart  [enum]',
              ['NEVER', 'ON_FAILURE', 'ALWAYS'],
              [], C_GREEN)

    class_box(ax, 3.0, 2.2, 3.2, 'CtlServer',
              ['sock_fd: int', 'sock_path: char[128]'],
              ['+ctl_init()', '+ctl_accept()',
               '+cmd_list()', '+cmd_start()',
               '+cmd_stop()', '+cmd_status()'], C_PURPLE)

    class_box(ax, 8.5, 2.5, 3.0, 'ServiceFileParser',
              ['path: char[256]'],
              ['+parse(path) → Service',
               '+parse_all(dir) → int'], C_GRAY)

    # Arrows
    def rel(ax, x1, y1, x2, y2):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', color=C_GRAY, lw=1.2), zorder=5)
    rel(ax, 4.7, 7.8, 6.7, 7.8)   # Sup → Service
    rel(ax, 3.0, 6.6, 3.0, 5.7)   # Sup → SvcType
    rel(ax, 5.5, 6.6, 7.0, 5.4)   # Sup → SvcState
    rel(ax, 5.5, 6.6, 11.2, 5.4)  # Sup → SvcRestart
    rel(ax, 3.0, 5.7, 3.0, 3.0)   # Sup → CtlServer
    rel(ax, 6.5, 7.8, 8.5, 3.3)   # Service → Parser

    ax.text(6.0, 7.95, '1..*', ha='center', fontsize=9, color=C_GRAY)

    save(fig, 'fig6_8_class_supervisor.png')

# ══════════════════════════════════════════════════════════════════════════════
# Figure 6.9 — Sequence Diagram — Package Build Flow
# ══════════════════════════════════════════════════════════════════════════════
def seq_lifeline(ax, x, y_top, y_bot, label, color):
    ax.text(x, y_top + 0.1, label, ha='center', va='bottom', fontsize=8.5,
            color=color, fontweight='bold',
            bbox=dict(fc=color+"22", ec=color, pad=4, boxstyle='round'))
    ax.plot([x, x], [y_top, y_bot], color=color, lw=1, ls='--', zorder=2)

def seq_msg(ax, x1, x2, y, label, color=C_DARK, ret=False):
    style = '<-' if ret else '->'
    ax.annotate('', xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle=style, color=color, lw=1.4,
                                linestyle='dashed' if ret else 'solid'), zorder=4)
    mx = (x1 + x2) / 2
    ax.text(mx, y + 0.07, label, ha='center', va='bottom', fontsize=8,
            color=color, zorder=5,
            bbox=dict(fc=C_BG, ec='none', pad=1))

def activation(ax, x, y_top, y_bot, color):
    ax.add_patch(plt.Rectangle((x - 0.08, y_bot), 0.16, y_top - y_bot,
                               fc=color+"55", ec=color, lw=1, zorder=3))

def fig6_9():
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_xlim(0, 14); ax.set_ylim(0, 10); ax.axis('off')
    title_box(fig, 'Figure 6.9 — Sequence Diagram: Package Build Flow')

    lifelines = [
        (1.2, 'Operator', C_CYAN),
        (3.5, 'cogman-planner', C_RUST),
        (6.0, 'MetadataLoader', C_BLUE),
        (8.5, 'DependencyGraph', C_BLUE),
        (11.0, 'PlanWriter', C_GREEN),
        (13.0, 'CGM2PLAN\nFile', C_GREEN),
    ]
    for x, lbl, clr in lifelines:
        seq_lifeline(ax, x, 9.2, 0.3, lbl, clr)

    msgs = [
        (1.2, 3.5, 8.8, 'invoke planner(meta.toml)', C_CYAN),
        (3.5, 6.0, 8.4, 'load(meta.toml)', C_RUST),
        (6.0, 3.5, 8.0, 'PackageMetadata', C_BLUE, True),
        (3.5, 8.5, 7.7, 'build_graph(metadata)', C_RUST),
        (8.5, 3.5, 7.3, 'sorted_packages[]', C_BLUE, True),
        (3.5, 6.0, 6.9, 'load_dep(libfoo)', C_RUST),
        (6.0, 3.5, 6.5, 'PackageMetadata', C_BLUE, True),
        (3.5, 8.5, 6.1, 'add_edge(foo, libfoo)', C_RUST),
        (8.5, 3.5, 5.7, 'OK', C_BLUE, True),
        (3.5, 8.5, 5.3, 'topo_sort()', C_RUST),
        (8.5, 3.5, 4.9, 'ordered_list[]', C_BLUE, True),
        (3.5, 11.0, 4.5, 'emit_steps(ordered_list)', C_RUST),
        (11.0, 13.0, 4.1, 'write(steps)', C_GREEN),
        (13.0, 11.0, 3.7, 'OK', C_GREEN, True),
        (11.0, 3.5, 3.3, 'plan_path', C_GREEN, True),
        (3.5, 1.2, 2.9, 'exit 0', C_RUST),
    ]
    for m in msgs:
        x1, x2, y, lbl = m[0], m[1], m[2], m[3]
        clr = m[4] if len(m) > 4 else C_DARK
        ret = m[5] if len(m) > 5 else False
        if x2 <= 13.0:
            seq_msg(ax, x1, x2, y, lbl, clr, ret)

    # Activations
    activation(ax, 3.5, 9.0, 2.7, C_RUST)
    activation(ax, 6.0, 8.3, 6.3, C_BLUE)
    activation(ax, 8.5, 7.6, 4.7, C_BLUE)
    activation(ax, 11.0, 4.4, 3.5, C_GREEN)

    save(fig, 'fig6_9_seq_build.png')

# ══════════════════════════════════════════════════════════════════════════════
# Figure 6.10 — Sequence Diagram — Service Start Flow
# ══════════════════════════════════════════════════════════════════════════════
def fig6_10():
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_xlim(0, 14); ax.set_ylim(0, 10); ax.axis('off')
    title_box(fig, 'Figure 6.10 — Sequence Diagram: Service Start Flow')

    lifelines = [
        (1.2,  'Operator\n(cogman-ctl)', C_GREEN),
        (3.5,  'cogman-\nsupervisor', C_CYAN),
        (6.0,  'ServiceFile\nParser', C_BLUE),
        (8.5,  'Linux\nKernel', C_GRAY),
        (11.0, 'Service\nProcess', C_RUST),
        (13.0, 'SIGCHLD\nself-pipe', C_ORANGE),
    ]
    for x, lbl, clr in lifelines:
        seq_lifeline(ax, x, 9.2, 0.3, lbl, clr)

    msgs = [
        (1.2, 3.5, 8.7, 'connect /run/cogman-supervisor.sock', C_GREEN),
        (1.2, 3.5, 8.3, 'send "start heartbeat"', C_GREEN),
        (3.5, 6.0, 7.9, 'parse_all(/etc/cogman/services/)', C_CYAN),
        (6.0, 3.5, 7.5, 'Service{heartbeat,...}', C_BLUE, True),
        (3.5, 3.5, 7.1, 'check_deps(heartbeat)', C_CYAN),
        (3.5, 8.5, 6.7, 'fork()', C_CYAN),
        (8.5, 3.5, 6.3, 'child_pid=42', C_GRAY, True),
        (8.5, 11.0, 5.9, 'exec("/bin/heartbeat")', C_GRAY),
        (3.5, 13.0, 5.5, 'set state=STARTING', C_CYAN),
        (11.0, 13.0, 5.1, 'SIGCHLD → write(pipe_w,1)', C_ORANGE),
        (13.0, 3.5, 4.7, 'read(pipe_r)', C_ORANGE, True),
        (3.5, 3.5, 4.3, 'waitpid(42,WNOHANG)', C_CYAN),
        (3.5, 3.5, 3.9, 'set state=RUNNING', C_CYAN),
        (3.5, 1.2, 3.5, 'send "OK pid=42\\n"', C_CYAN),
        (1.2, 1.2, 3.1, 'display status', C_GREEN),
    ]
    for m in msgs:
        x1, x2, y, lbl = m[0], m[1], m[2], m[3]
        clr = m[4] if len(m) > 4 else C_DARK
        ret = m[5] if len(m) > 5 else False
        if x1 != x2:
            seq_msg(ax, x1, x2, y, lbl, clr, ret)
        else:
            ax.text(x1 + 0.15, y + 0.07, lbl, ha='left', va='bottom',
                    fontsize=8, color=clr,
                    bbox=dict(fc=C_BG, ec='none', pad=1))
            ax.annotate('', xy=(x1 + 0.5, y), xytext=(x1 + 0.5, y + 0.3),
                        arrowprops=dict(arrowstyle='->', color=clr, lw=1))

    activation(ax, 3.5, 9.0, 3.2, C_CYAN)
    activation(ax, 8.5, 6.6, 5.8, C_GRAY)

    save(fig, 'fig6_10_seq_start.png')

# ══════════════════════════════════════════════════════════════════════════════
# Figure 6.11 — Component Diagram
# ══════════════════════════════════════════════════════════════════════════════
def component_box(ax, x, y, w, h, title, ports=None, color=C_BLUE):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.04',
                               lw=2, ec=color, fc=color+"15", zorder=3))
    # Component icon (two small rectangles on left edge)
    icon_x = x + 0.08; icon_y = y + h - 0.35
    ax.add_patch(plt.Rectangle((icon_x, icon_y+0.15), 0.4, 0.18, fc=color, zorder=5))
    ax.add_patch(plt.Rectangle((icon_x, icon_y-0.05), 0.4, 0.18, fc=color, zorder=5))
    ax.add_patch(plt.Rectangle((icon_x - 0.1, icon_y + 0.08), 0.5, 0.3,
                               fc=color+"33", ec=color, lw=1, zorder=4))
    ax.text(x + w/2 + 0.15, y + h - 0.22, title, ha='center', va='center',
            fontsize=9, fontweight='bold', color=color, zorder=6)
    if ports:
        for i, (side, pname) in enumerate(ports):
            py = y + h*0.35 + i*0.3
            if side == 'L':
                ax.add_patch(Circle((x, py), 0.08, fc=color, zorder=6))
                ax.text(x - 0.15, py, pname, ha='right', va='center',
                        fontsize=7.5, color=color)
            else:
                ax.add_patch(Circle((x+w, py), 0.08, fc=color+"55", ec=color,
                                    lw=1.5, zorder=6))
                ax.text(x+w+0.15, py, pname, ha='left', va='center',
                        fontsize=7.5, color=color)

def fig6_11():
    fig, ax = plt.subplots(figsize=(15, 9))
    ax.set_xlim(0, 15); ax.set_ylim(0, 9); ax.axis('off')
    title_box(fig, 'Figure 6.11 — Component Diagram')

    # HOST ENV boundary
    ax.add_patch(plt.Rectangle((0.3, 4.5), 6.5, 4.0, fill=False,
                               ec=C_RUST, lw=2, ls='-', zorder=1))
    ax.text(3.55, 8.25, 'Host Build Environment', ha='center', fontsize=10,
            color=C_RUST, fontweight='bold')

    # HOST components
    component_box(ax, 0.6, 6.4, 2.8, 1.2, 'cogman-planner\n(Rust binary)', color=C_RUST)
    component_box(ax, 0.6, 4.8, 2.8, 1.2, 'cogman-executor\n(C11 binary)', color=C_CYAN)
    component_box(ax, 4.0, 5.5, 2.5, 1.0, 'CGM2PLAN\n.bin file', color=C_GOLD)

    # TARGET ROOT boundary
    ax.add_patch(plt.Rectangle((7.5, 0.3), 7.2, 8.2, fill=False,
                               ec=C_CYAN, lw=2, zorder=1))
    ax.text(11.1, 8.3, 'Target Rootfs  (/)', ha='center', fontsize=10,
            color=C_CYAN, fontweight='bold')

    # TARGET components
    component_box(ax, 7.8, 5.8, 3.0, 1.6, 'cogman-supervisor\n(PID 1)', color=C_CYAN)
    component_box(ax, 7.8, 3.5, 2.8, 1.6, 'cogman-ctl\n(client)', color=C_GREEN)
    component_box(ax, 11.5, 5.8, 2.8, 1.6, 'Service Processes\n(heartbeat, hello…)', color=C_RUST)
    component_box(ax, 11.5, 3.8, 2.8, 1.2, 'messenger\n(IPC broker)', color=C_PURPLE)
    component_box(ax, 7.8, 1.5, 3.0, 1.5, '/etc/cogman/\nservices/*.service', color=C_BLUE)
    component_box(ax, 11.5, 1.5, 2.8, 1.5, '/sbin/init\n→ symlink', color=C_GRAY)

    # Connections HOST
    arrow(ax, 3.4, 7.0, 4.0, 6.2, label='emits', color=C_RUST, lw=1.5)
    arrow(ax, 4.0, 5.8, 3.4, 5.4, label='reads', color=C_CYAN, lw=1.5)

    # HOST → TARGET (deploy)
    ax.annotate('', xy=(7.5, 4.3), xytext=(6.5, 4.3),
                arrowprops=dict(arrowstyle='->', color=C_GOLD, lw=2,
                                ls='dashed'), zorder=5)
    ax.text(7.0, 4.55, 'deploy\nrootfs', ha='center', fontsize=8,
            color=C_GOLD)

    # TARGET internal connections
    arrow(ax, 9.3, 6.6, 11.5, 6.6, label='fork/exec', color=C_CYAN, lw=1.5)
    arrow(ax, 9.3, 6.0, 11.5, 5.0, label='IPC/TLV', color=C_PURPLE, lw=1.2)
    arrow(ax, 10.6, 4.3, 10.6, 5.8, label='socket', color=C_GREEN, lw=1.2)
    arrow(ax, 9.3, 5.8, 8.3, 3.0, label='reads', color=C_CYAN, lw=1.2)
    arrow(ax, 11.5, 3.8, 9.3, 3.8, label='publish', color=C_PURPLE, lw=1.2)
    arrow(ax, 9.3, 5.8, 11.5, 2.0, label='symlink\ntarget', color=C_GRAY, lw=1,
          labeloffset=(0.3, 0.0))

    save(fig, 'fig6_11_component.png')

# ══════════════════════════════════════════════════════════════════════════════
# Figure 7.1 — cogman-planner Dependency Graph Resolution
# ══════════════════════════════════════════════════════════════════════════════
def fig7_1():
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 12); ax.set_ylim(0, 8); ax.axis('off')
    title_box(fig, 'Figure 7.1 — cogman-planner: Dependency Graph Resolution')

    nodes = {
        'busybox':    (6.0, 6.8, C_RUST),
        'cogman-sup': (2.5, 5.5, C_CYAN),
        'cogman-exec':(6.0, 5.5, C_CYAN),
        'cogman-plan':(9.5, 5.5, C_CYAN),
        'musl-libc':  (2.5, 3.5, C_BLUE),
        'linux-hdr':  (5.0, 3.5, C_BLUE),
        'busybox-sh': (7.5, 3.5, C_BLUE),
        'gcc-rt':     (10.0,3.5, C_BLUE),
        'kernel':     (6.0, 1.8, C_GRAY),
    }

    for name, (x, y, clr) in nodes.items():
        ax.add_patch(Circle((x, y), 0.65, fc=clr+"33", ec=clr, lw=2, zorder=3))
        ax.text(x, y, name, ha='center', va='center', fontsize=8.5,
                color=clr, fontweight='bold', zorder=4)

    edges = [
        ('busybox', 'musl-libc'), ('busybox', 'linux-hdr'),
        ('cogman-sup', 'musl-libc'), ('cogman-sup', 'linux-hdr'),
        ('cogman-exec', 'musl-libc'), ('cogman-exec', 'linux-hdr'),
        ('cogman-exec', 'busybox-sh'),
        ('cogman-plan', 'gcc-rt'), ('cogman-plan', 'linux-hdr'),
        ('musl-libc', 'kernel'), ('linux-hdr', 'kernel'),
        ('busybox-sh', 'busybox'),
        ('gcc-rt', 'kernel'),
    ]
    for src, dst in edges:
        x1, y1, c1 = nodes[src]
        x2, y2, c2 = nodes[dst]
        dx = x2 - x1; dy = y2 - y1
        norm = (dx**2 + dy**2)**0.5
        x1s = x1 + 0.65*dx/norm; y1s = y1 + 0.65*dy/norm
        x2e = x2 - 0.65*dx/norm; y2e = y2 - 0.65*dy/norm
        ax.annotate('', xy=(x2e, y2e), xytext=(x1s, y1s),
                    arrowprops=dict(arrowstyle='->', color=C_GRAY, lw=1.3,
                                    connectionstyle='arc3,rad=0.1'), zorder=2)

    # FNV hash annotation
    ax.text(10.5, 7.2, 'FNV-1a hash\nper metadata file\n→ cache key',
            ha='center', fontsize=8.5, color=C_GOLD,
            bbox=dict(fc=C_GOLD+"22", ec=C_GOLD, pad=5, boxstyle='round'))

    # Stage labels
    for y, lbl in [(6.8, 'Root Package'), (5.5, 'Direct Dependencies'),
                   (3.5, 'Transitive Dependencies'), (1.8, 'Base Layer')]:
        ax.text(0.3, y, lbl, ha='left', va='center', fontsize=8,
                color=C_GRAY, style='italic')
        ax.plot([0.3, 0.9], [y, y], color=C_GRAY, lw=0.8, ls=':')

    save(fig, 'fig7_1_dep_graph.png')

# ══════════════════════════════════════════════════════════════════════════════
# Figure 7.2 — Topological Sort Example (Kahn's Algorithm)
# ══════════════════════════════════════════════════════════════════════════════
def fig7_2():
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.set_xlim(0, 14); ax.set_ylim(0, 7); ax.axis('off')
    title_box(fig, "Figure 7.2 — Dependency Topological Sort (Kahn's Algorithm)")

    # LEFT: input DAG
    ax.add_patch(plt.Rectangle((0.2, 0.5), 5.8, 6.1, fill=False,
                               ec=C_BLUE, lw=1.5, ls='--', zorder=0))
    ax.text(3.1, 6.4, 'Input DAG', ha='center', fontsize=10,
            color=C_BLUE, fontweight='bold')

    dag_nodes = {
        'A': (1.5, 5.0), 'B': (3.0, 5.0), 'C': (4.5, 5.0),
        'D': (2.0, 3.5), 'E': (4.0, 3.5),
        'F': (3.0, 2.0),
    }
    colors_map = {'A': C_RUST, 'B': C_RUST, 'C': C_RUST,
                  'D': C_CYAN, 'E': C_CYAN, 'F': C_GREEN}
    for name, (x, y) in dag_nodes.items():
        clr = colors_map[name]
        ax.add_patch(Circle((x, y), 0.5, fc=clr+"33", ec=clr, lw=2, zorder=3))
        ax.text(x, y, name, ha='center', va='center', fontsize=12,
                color=clr, fontweight='bold', zorder=4)

    dag_edges = [('A','D'),('B','D'),('B','E'),('C','E'),('D','F'),('E','F')]
    for s, d in dag_edges:
        x1, y1 = dag_nodes[s]; x2, y2 = dag_nodes[d]
        dx = x2-x1; dy = y2-y1; norm = (dx**2+dy**2)**0.5
        ax.annotate('', xy=(x2-0.5*dx/norm, y2-0.5*dy/norm),
                    xytext=(x1+0.5*dx/norm, y1+0.5*dy/norm),
                    arrowprops=dict(arrowstyle='->', color=C_GRAY, lw=1.4,
                                    connectionstyle='arc3,rad=0.05'), zorder=2)

    # Arrow between halves
    ax.annotate('Kahn\'s\ntopo sort', xy=(8.2, 3.5), xytext=(6.2, 3.5),
                arrowprops=dict(arrowstyle='->', color=C_DARK, lw=2.5),
                ha='center', fontsize=10, color=C_DARK, fontweight='bold',
                bbox=dict(fc=C_LIGHT, ec=C_DARK, pad=5, boxstyle='round'))

    # RIGHT: sorted output
    ax.add_patch(plt.Rectangle((8.5, 0.5), 5.3, 6.1, fill=False,
                               ec=C_GREEN, lw=1.5, ls='--', zorder=0))
    ax.text(11.15, 6.4, 'Topological Order', ha='center', fontsize=10,
            color=C_GREEN, fontweight='bold')

    order = ['A', 'B', 'C', 'D', 'E', 'F']
    labels_full = {
        'A': 'kernel', 'B': 'linux-hdr', 'C': 'gcc-rt',
        'D': 'musl-libc', 'E': 'busybox', 'F': 'cogman-supervisor'
    }
    for i, name in enumerate(order):
        y = 5.5 - i*0.85
        clr = colors_map[name]
        ax.add_patch(FancyBboxPatch((9.0, y-0.28), 4.5, 0.56,
                                   boxstyle='round,pad=0.04', lw=1.5,
                                   ec=clr, fc=clr+"22", zorder=3))
        ax.text(9.3, y, f'{i+1}.  {name}  — {labels_full[name]}',
                ha='left', va='center', fontsize=9.5, color=clr,
                fontweight='bold', zorder=4)

    # In-degree annotation
    ax.text(3.1, 1.1, 'in-degree(F) = 2  →  enqueue when 0',
            ha='center', fontsize=8.5, color=C_GOLD,
            bbox=dict(fc=C_GOLD+"22", ec=C_GOLD, pad=3, boxstyle='round'))

    save(fig, 'fig7_2_topo_sort.png')

# ══════════════════════════════════════════════════════════════════════════════
# Figure 7.3 — cogman-executor Step Execution Loop
# ══════════════════════════════════════════════════════════════════════════════
def fig7_3():
    fig, ax = plt.subplots(figsize=(11, 12))
    ax.set_xlim(0, 11); ax.set_ylim(0, 12); ax.axis('off')
    title_box(fig, 'Figure 7.3 — cogman-executor: Step Execution Loop')

    steps = [
        (5.5, 11.0, 'open(plan_path)', C_GRAY, 'diamond', None),
        (5.5, 9.8,  'mmap(file, PROT_READ)', C_BLUE, 'box', None),
        (5.5, 8.7,  'validate_header()\n(magic + version)', C_BLUE, 'diamond', None),
        (5.5, 7.6,  'i = 0', C_GRAY, 'box', None),
        (5.5, 6.5,  'i < step_count ?', C_GOLD, 'diamond', None),
        (5.5, 5.4,  'dispatch(steps[i].op)', C_CYAN, 'box', None),
        (5.5, 4.2,  'op == OP_EXEC ?', C_CYAN, 'diamond', 'OP_EXEC'),
        (2.0, 3.0,  'fork()+exec()\n/bin/sh -c cmd', C_RUST, 'box', None),
        (5.5, 3.0,  'mkdir_p(path)', C_RUST, 'box', None),
        (9.0, 3.0,  'copy_recursive()\n+path guard', C_RUST, 'box', None),
        (5.5, 1.8,  'fail_policy==ABORT\n&& rc != 0 ?', C_RED, 'diamond', None),
        (5.5, 0.7,  'i++  →  next step', C_GRAY, 'box', None),
    ]

    def draw_step(ax, x, y, label, color, shape):
        if shape == 'diamond':
            w, h = 2.4, 0.7
            d = mpatches.FancyBboxPatch((x-w/2, y-h/2), w, h,
                                        boxstyle='round,pad=0.03',
                                        lw=1.5, ec=color, fc=color+"22", zorder=3)
            ax.add_patch(d)
            # Diamond overlay
            diamond = plt.Polygon([[x, y+h/2+0.1],[x+w/2+0.1,y],[x,y-h/2-0.1],[x-w/2-0.1,y]],
                                  fill=False, ec=color, lw=1.5, zorder=4)
            ax.add_patch(diamond)
        else:
            ax.add_patch(FancyBboxPatch((x-1.3, y-0.32), 2.6, 0.64,
                                       boxstyle='round,pad=0.05', lw=1.5,
                                       ec=color, fc=color+"22", zorder=3))
        ax.text(x, y, label, ha='center', va='center', fontsize=8.5,
                color=color, fontweight='bold' if shape=='box' else 'normal', zorder=5)

    for (x, y, lbl, clr, shp, _) in steps:
        draw_step(ax, x, y, lbl, clr, shp)

    # Main vertical flow
    flow = [(5.5, 10.65), (5.5, 10.15), (5.5, 9.15), (5.5, 8.35),
            (5.5, 7.25), (5.5, 6.85), (5.5, 5.75), (5.5, 4.58)]
    for i in range(len(flow)-1):
        ax.annotate('', xy=flow[i+1], xytext=flow[i],
                    arrowprops=dict(arrowstyle='->', color=C_DARK, lw=1.5), zorder=5)

    # Dispatch branches
    for xdst in [2.0, 5.5, 9.0]:
        ax.annotate('', xy=(xdst, 3.32), xytext=(5.5, 4.0),
                    arrowprops=dict(arrowstyle='->', color=C_CYAN, lw=1.2,
                                    connectionstyle='arc3,rad=0.0'), zorder=5)
    ax.text(3.0, 4.05, 'OP_EXEC', fontsize=7.5, color=C_CYAN)
    ax.text(5.55, 4.05, 'OP_MKDIR', fontsize=7.5, color=C_CYAN)
    ax.text(7.3, 4.05, 'OP_COPY', fontsize=7.5, color=C_CYAN)

    # Converge to fail_policy check
    for xsrc in [2.0, 5.5, 9.0]:
        ax.annotate('', xy=(5.5, 2.15), xytext=(xsrc, 2.68),
                    arrowprops=dict(arrowstyle='->', color=C_GRAY, lw=1.2,
                                    connectionstyle='arc3,rad=0.0'), zorder=5)

    # fail → abort
    ax.annotate('', xy=(9.5, 1.8), xytext=(6.8, 1.8),
                arrowprops=dict(arrowstyle='->', color=C_RED, lw=1.5), zorder=5)
    ax.text(9.7, 1.8, 'exit(2)\nABORT', ha='left', va='center', fontsize=9,
            color=C_RED, fontweight='bold',
            bbox=dict(fc=C_RED+"22", ec=C_RED, pad=3, boxstyle='round'))
    ax.text(7.4, 2.0, 'YES', fontsize=8.5, color=C_RED)

    # pass → i++
    ax.annotate('', xy=(5.5, 1.0), xytext=(5.5, 1.45),
                arrowprops=dict(arrowstyle='->', color=C_GREEN, lw=1.5), zorder=5)
    ax.text(5.7, 1.6, 'NO', fontsize=8.5, color=C_GREEN)

    # loop back arrow
    ax.annotate('', xy=(5.5, 6.15), xytext=(5.5, 1.0),
                arrowprops=dict(arrowstyle='->', color=C_GOLD, lw=1.4,
                                connectionstyle='arc3,rad=-0.7'), zorder=5)

    # exit loop → done
    ax.text(7.8, 6.5, 'NO (done)', fontsize=8.5, color=C_GREEN)
    ax.annotate('', xy=(9.0, 6.5), xytext=(6.8, 6.5),
                arrowprops=dict(arrowstyle='->', color=C_GREEN, lw=1.5), zorder=5)
    ax.text(9.2, 6.5, 'munmap()\nexit(0)', ha='left', va='center', fontsize=9,
            color=C_GREEN, bbox=dict(fc=C_GREEN+"22", ec=C_GREEN, pad=3, boxstyle='round'))

    save(fig, 'fig7_3_executor_loop.png')

# ══════════════════════════════════════════════════════════════════════════════
# Figure 7.4 — Path Traversal Guard Logic
# ══════════════════════════════════════════════════════════════════════════════
def fig7_4():
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 12); ax.set_ylim(0, 8); ax.axis('off')
    title_box(fig, 'Figure 7.4 — Path Traversal Guard Logic  (copy_recursive)')

    # Flowchart
    def fbox(ax, x, y, w, h, lbl, color, shape='rect'):
        if shape == 'diamond':
            pts = [[x, y+h/2],[x+w/2, y],[x, y-h/2],[x-w/2, y]]
            ax.add_patch(plt.Polygon(pts, fc=color+"22", ec=color, lw=1.8, zorder=3))
        else:
            ax.add_patch(FancyBboxPatch((x-w/2, y-h/2), w, h,
                                       boxstyle='round,pad=0.05', lw=1.8,
                                       ec=color, fc=color+"22", zorder=3))
        ax.text(x, y, lbl, ha='center', va='center', fontsize=9,
                color=color, fontweight='bold', zorder=4)

    nodes = [
        (6, 7.4, 2.6, 0.55, 'copy_recursive(src, dst)', C_CYAN, 'rect'),
        (6, 6.4, 3.2, 0.55, 'tokenize(dst) → components[]', C_BLUE, 'rect'),
        (6, 5.4, 3.0, 0.7,  'for each component', C_GOLD, 'diamond'),
        (6, 4.3, 3.0, 0.7,  'component == ".." ?', C_RED, 'diamond'),
        (2.5, 3.1, 2.8, 0.6,'return ERR_TRAVERSAL\n(exit code 2)', C_RED, 'rect'),
        (6, 3.1, 2.8, 0.6,  'component contains\nnull byte?', C_RED, 'diamond'),
        (6, 2.0, 2.8, 0.6,  'all components OK\n→ proceed copy', C_GREEN, 'rect'),
        (9.5, 3.1, 2.8, 0.6,'return ERR_BADPATH\n(exit code 2)', C_RED, 'rect'),
    ]
    for (x, y, w, h, lbl, clr, shp) in nodes:
        fbox(ax, x, y, w, h, lbl, clr, shp)

    # Simple vertical chain
    chain = [(6,7.12),(6,6.68),(6,6.12),(6,5.75),(6,5.05),(6,4.65),(6,3.45)]
    for i in range(len(chain)-1):
        ax.annotate('', xy=chain[i+1], xytext=chain[i],
                    arrowprops=dict(arrowstyle='->', color=C_DARK, lw=1.5), zorder=5)

    # YES branch → error
    ax.annotate('', xy=(2.5, 3.4), xytext=(4.5, 4.3),
                arrowprops=dict(arrowstyle='->', color=C_RED, lw=1.5), zorder=5)
    ax.text(3.0, 4.0, 'YES\n("..")', fontsize=8.5, color=C_RED)

    # NO → null check
    ax.annotate('', xy=(6, 3.45), xytext=(6, 3.95),
                arrowprops=dict(arrowstyle='->', color=C_GREEN, lw=1.5), zorder=5)
    ax.text(6.15, 3.75, 'NO', fontsize=8.5, color=C_GREEN)

    # null byte YES
    ax.annotate('', xy=(9.5, 3.4), xytext=(7.4, 3.1),
                arrowprops=dict(arrowstyle='->', color=C_RED, lw=1.5), zorder=5)
    ax.text(8.6, 3.35, 'YES', fontsize=8.5, color=C_RED)

    # null byte NO → proceed
    ax.annotate('', xy=(6, 2.3), xytext=(6, 2.7),
                arrowprops=dict(arrowstyle='->', color=C_GREEN, lw=1.5), zorder=5)
    ax.text(6.15, 2.55, 'NO', fontsize=8.5, color=C_GREEN)

    # loop back
    ax.annotate('', xy=(6, 5.05), xytext=(6, 2.0),
                arrowprops=dict(arrowstyle='->', color=C_GOLD, lw=1.2,
                                connectionstyle='arc3,rad=0.7'), zorder=5)

    # Examples
    examples = [
        ('../etc/passwd',    C_RED,   'BLOCKED  (bare ".." component)'),
        ('/tmp/build/foo',   C_GREEN, 'ALLOWED  (clean path)'),
        ('/tmp/../etc/cron', C_RED,   'BLOCKED  (traversal via "..")'),
        ('/tmp/build/',      C_GREEN, 'ALLOWED  (trailing slash)'),
    ]
    ax.text(0.4, 1.5, 'Examples:', fontsize=10, fontweight='bold', color=C_DARK)
    for i, (path, clr, verdict) in enumerate(examples):
        y = 1.1 - i*0.28
        ax.text(0.5, y, f'{path}', fontsize=8.5, color=clr,
                fontfamily='monospace')
        ax.text(5.5, y, f'→  {verdict}', fontsize=8.5, color=clr)

    save(fig, 'fig7_4_path_guard.png')

# ══════════════════════════════════════════════════════════════════════════════
# Figure 7.5 — SIGCHLD Self-Pipe Pattern
# ══════════════════════════════════════════════════════════════════════════════
def fig7_5():
    fig, ax = plt.subplots(figsize=(13, 8))
    ax.set_xlim(0, 13); ax.set_ylim(0, 8); ax.axis('off')
    title_box(fig, 'Figure 7.5 — cogman-supervisor: SIGCHLD Self-Pipe Pattern')

    # Three swim-lanes
    for y, lbl, clr in [(6.5, 'Linux Kernel  / Signal Delivery', C_GRAY),
                        (3.8, 'SIGCHLD Handler  (async, signal-safe)', C_ORANGE),
                        (1.2, 'Main Loop  (select() + 100 ms timeout)', C_CYAN)]:
        ax.add_patch(plt.Rectangle((0.2, y-1.0), 12.6, 2.0, fill=False,
                                   ec=clr, lw=1.2, ls='--', zorder=0,
                                   fc=clr+"08"))
        ax.text(0.4, y+0.75, lbl, fontsize=9, color=clr, fontweight='bold')

    # Pipe graphic
    ax.add_patch(FancyBboxPatch((5.5, 2.5), 2.0, 0.8, boxstyle='round,pad=0.05',
                               lw=2, ec=C_ORANGE, fc=C_ORANGE+"33", zorder=3))
    ax.text(6.5, 2.9, 'pipe()\n[pipe_r, pipe_w]', ha='center', va='center',
            fontsize=8.5, color=C_ORANGE, fontweight='bold', zorder=4)

    # Events
    events = [
        (1.8, 6.5, 'Child process\nexits', C_GRAY),
        (1.8, 3.8, 'sigaction(SIGCHLD,\n  handler)', C_ORANGE),
        (4.5, 3.8, 'write(pipe_w, "\\1", 1)\n(async-signal-safe)', C_ORANGE),
        (9.0, 1.2, 'select(pipe_r,\n  timeout=100ms)', C_CYAN),
        (11.5, 1.2, 'read(pipe_r)\nwaitpid(−1,WNOHANG)', C_CYAN),
    ]
    for x, y, lbl, clr in events:
        box(ax, x, y, 2.6, 0.9, lbl, clr, fontsize=8.5)

    # Flow arrows
    arrow(ax, 1.8, 6.05, 1.8, 4.25, label='SIGCHLD\ndelivered', color=C_GRAY)
    arrow(ax, 1.8, 3.35, 4.5, 3.35, label='signal fires\nhandler', color=C_ORANGE)
    arrow(ax, 5.5, 3.35, 6.5, 3.3, color=C_ORANGE)
    arrow(ax, 6.5, 2.5, 9.0, 1.65, label='pipe_r\nreadable', color=C_ORANGE)
    arrow(ax, 10.25, 1.2, 11.5, 1.2, color=C_CYAN)

    # Return loop
    ax.annotate('update service\nstate table', xy=(4.0, 1.2), xytext=(11.5, 1.2),
                arrowprops=dict(arrowstyle='<-', color=C_CYAN, lw=1.2,
                                connectionstyle='arc3,rad=-0.3'),
                ha='center', fontsize=8, color=C_CYAN,
                bbox=dict(fc=C_CYAN+"22", ec=C_CYAN, pad=2))

    # Annotation: why self-pipe
    ax.text(0.5, 0.3, 'Key invariant: write() is async-signal-safe (POSIX).  '
            'waitpid() is NOT called from the handler — avoids reentrancy.  '
            'select() in the main loop wakes immediately when pipe_r becomes readable.',
            fontsize=8.5, color=C_DARK, style='italic',
            wrap=True)

    save(fig, 'fig7_5_sigchld.png')

# ══════════════════════════════════════════════════════════════════════════════
# Figure 7.6 — Service Lifecycle State Machine
# ══════════════════════════════════════════════════════════════════════════════
def fig7_6():
    fig, ax = plt.subplots(figsize=(13, 9))
    ax.set_xlim(0, 13); ax.set_ylim(0, 9); ax.axis('off')
    title_box(fig, 'Figure 7.6 — Service Lifecycle State Machine')

    states = {
        'STOPPED':    (2.0,  7.0, C_GRAY),
        'STARTING':   (6.5,  7.0, C_BLUE),
        'RUNNING':    (11.0, 7.0, C_GREEN),
        'RESTARTING': (11.0, 3.5, C_ORANGE),
        'FAILED':     (2.0,  3.5, C_RED),
        'DONE':       (6.5,  1.2, C_PURPLE),
    }

    # Initial pseudo-state
    ax.add_patch(Circle((2.0, 8.4), 0.22, fc=C_DARK, zorder=5))
    ax.annotate('', xy=(2.0, 7.5), xytext=(2.0, 8.18),
                arrowprops=dict(arrowstyle='->', color=C_DARK, lw=2), zorder=5)

    for name, (x, y, clr) in states.items():
        ax.add_patch(Circle((x, y), 0.9, fc=clr+"33", ec=clr, lw=2.5, zorder=3))
        ax.text(x, y, name, ha='center', va='center', fontsize=9.5,
                fontweight='bold', color=clr, zorder=4)

    def st(n): return states[n][0], states[n][1]

    def st_arrow(ax, src, dst, label, color=C_DARK, rad=0.1, labelpos=0.5):
        x1, y1 = st(src); x2, y2 = st(dst)
        dx = x2-x1; dy = y2-y1; norm = (dx**2+dy**2)**0.5
        ax.annotate('', xy=(x2-0.9*dx/norm, y2-0.9*dy/norm),
                    xytext=(x1+0.9*dx/norm, y1+0.9*dy/norm),
                    arrowprops=dict(arrowstyle='->', color=color, lw=1.8,
                                    connectionstyle=f'arc3,rad={rad}'), zorder=5)
        mx = x1 + (x2-x1)*labelpos; my = y1 + (y2-y1)*labelpos
        ax.text(mx + 0.1, my + 0.2, label, ha='center', fontsize=8,
                color=color, zorder=6,
                bbox=dict(fc=C_BG, ec='none', pad=1))

    st_arrow(ax, 'STOPPED', 'STARTING', 'cmd_start()\ndeps satisfied', C_BLUE)
    st_arrow(ax, 'STARTING', 'RUNNING',  'exec() confirmed\nPID live', C_GREEN)
    st_arrow(ax, 'RUNNING', 'RESTARTING','SIGCHLD:\nrestart=always', C_ORANGE, rad=-0.2)
    st_arrow(ax, 'RESTARTING', 'STARTING','restart_at\ndeadline passed', C_ORANGE, rad=-0.1)
    st_arrow(ax, 'RUNNING', 'FAILED',    'exit≠0,\nrestart=never', C_RED, rad=0.2)
    st_arrow(ax, 'STARTING', 'FAILED',   'exec() failed', C_RED, rad=0.3)
    st_arrow(ax, 'FAILED', 'STOPPED',    'cmd_reset()', C_GRAY, rad=-0.2)
    st_arrow(ax, 'RUNNING', 'DONE',      'exit=0,\noneshot', C_PURPLE, rad=0.15)
    st_arrow(ax, 'STARTING', 'DONE',     'oneshot exits 0', C_PURPLE, rad=-0.15)
    # cmd_stop
    st_arrow(ax, 'RUNNING', 'STOPPED',   'cmd_stop()\nSIGTERM+SIGKILL', C_GRAY, rad=-0.3)

    # Terminal state double-circle for DONE
    ax.add_patch(Circle((6.5, 1.2), 1.1, fill=False, ec=C_PURPLE, lw=2.5, ls='--', zorder=5))

    # Restart count annotation
    ax.text(11.0, 1.5, 'max_restart\nexceeded → FAILED',
            ha='center', fontsize=8.5, color=C_RED,
            bbox=dict(fc=C_RED+"22", ec=C_RED, pad=3, boxstyle='round'))
    ax.annotate('', xy=(11.0, 2.6), xytext=(11.0, 2.0),
                arrowprops=dict(arrowstyle='->', color=C_RED, lw=1.2), zorder=5)

    save(fig, 'fig7_6_state_machine.png')

# ══════════════════════════════════════════════════════════════════════════════
# Figure 7.7 — cogman-ctl Unix Socket Protocol
# ══════════════════════════════════════════════════════════════════════════════
def fig7_7():
    fig, ax = plt.subplots(figsize=(13, 7))
    ax.set_xlim(0, 13); ax.set_ylim(0, 7); ax.axis('off')
    title_box(fig, 'Figure 7.7 — cogman-ctl Unix Domain Socket Protocol')

    # Client / Server
    box(ax, 2.0, 5.5, 3.0, 1.0, 'cogman-ctl\n(client)', C_GREEN, bold=True)
    box(ax, 11.0, 5.5, 3.0, 1.0, 'cogman-supervisor\n(server)', C_CYAN, bold=True)

    # Socket path
    ax.add_patch(plt.Rectangle((4.5, 5.0), 4.0, 0.8, fill=False,
                               ec=C_PURPLE, lw=1.5, ls='--', fc=C_PURPLE+"10", zorder=2))
    ax.text(6.5, 5.4, '/run/cogman-supervisor.sock\n(AF_UNIX, SOCK_STREAM)', ha='center',
            fontsize=8.5, color=C_PURPLE, zorder=3)

    # Protocol exchange
    exchanges = [
        (4.4, 'connect()', C_GREEN, True),
        (3.6, 'send: "list\\n"', C_GREEN, True),
        (2.8, 'recv: "heartbeat RUNNING pid=42\\n...\\nOK\\n"', C_CYAN, False),
        (2.0, 'close()', C_GREEN, True),
    ]
    for y, msg, clr, to_server in exchanges:
        x1, x2 = (2.5, 10.5) if to_server else (10.5, 2.5)
        ax.annotate('', xy=(x2, y), xytext=(x1, y),
                    arrowprops=dict(arrowstyle='->', color=clr, lw=1.8), zorder=4)
        ax.text(6.5, y+0.12, msg, ha='center', va='bottom', fontsize=8.5,
                color=clr, zorder=5,
                bbox=dict(fc=C_BG, ec='none', pad=1))

    # Commands table
    ax.add_patch(FancyBboxPatch((0.2, 0.2), 5.8, 1.5, boxstyle='round,pad=0.05',
                               lw=1.5, ec=C_GREEN, fc=C_GREEN+"10", zorder=2))
    ax.text(0.4, 1.55, 'Client Commands:', fontsize=9.5, color=C_GREEN,
            fontweight='bold', zorder=3)
    cmds = ['list', 'status <svc>', 'start <svc>', 'stop <svc>', 'restart <svc>']
    for i, c in enumerate(cmds):
        ax.text(0.6 + (i % 3)*1.9, 1.1 - (i//3)*0.35, c, fontsize=8.5,
                color=C_GREEN, fontfamily='monospace', zorder=3)

    # Timeout annotation
    ax.text(11.0, 1.2, 'SO_RCVTIMEO = 2 s\nchmod 0666\nnon-blocking accept',
            ha='center', fontsize=8.5, color=C_CYAN,
            bbox=dict(fc=C_CYAN+"22", ec=C_CYAN, pad=5, boxstyle='round'))

    save(fig, 'fig7_7_ctl_protocol.png')

# ══════════════════════════════════════════════════════════════════════════════
# Figure 7.8 — Messenger IPC Protocol (TLV Format)
# ══════════════════════════════════════════════════════════════════════════════
def fig7_8():
    fig, ax = plt.subplots(figsize=(13, 7))
    ax.set_xlim(0, 13); ax.set_ylim(0, 7); ax.axis('off')
    title_box(fig, 'Figure 7.8 — Messenger IPC Protocol: TLV Message Format')

    # Header bytes layout
    header_fields = [
        (0.5, 4, 'magic\n0x434F4731\n("COG1")', C_PURPLE),
        (4.5, 2, 'version\n(u16 = 1)', C_BLUE),
        (6.5, 2, 'msg_type\n(u16)', C_BLUE),
        (8.5, 4, 'payload_len\n(u32)', C_CYAN),
        (12.5, 4, 'src_pid\n(u32)', C_CYAN),
    ]
    # Draw byte ruler
    y_ruler = 5.8
    total_bytes = 16
    byte_w = 12.0 / total_bytes
    ax.text(0.3, 6.3, '16-byte Fixed Header', fontsize=10, color=C_PURPLE, fontweight='bold')

    colors_ruler = [C_PURPLE]*4 + [C_BLUE]*2 + [C_BLUE]*2 + [C_CYAN]*4 + [C_CYAN]*4
    for i in range(total_bytes):
        x = 0.5 + i*byte_w
        clr = colors_ruler[i]
        ax.add_patch(FancyBboxPatch((x, y_ruler-0.3), byte_w-0.04, 0.6,
                                   boxstyle='round,pad=0.01', lw=1,
                                   ec=clr, fc=clr+"33", zorder=3))
        ax.text(x + byte_w/2, y_ruler, f'{i}', ha='center', va='center',
                fontsize=7, color=clr, fontweight='bold', zorder=4)

    # Field labels below ruler
    field_spans = [(0, 4, 'magic[4]', C_PURPLE),
                   (4, 6, 'version', C_BLUE), (6, 8, 'msg_type', C_BLUE),
                   (8, 12, 'payload_len', C_CYAN), (12, 16, 'src_pid', C_CYAN)]
    for start, end, lbl, clr in field_spans:
        x1 = 0.5 + start*byte_w; x2 = 0.5 + end*byte_w
        ax.plot([x1+0.05, x2-0.05], [y_ruler-0.3, y_ruler-0.3], color=clr, lw=0)
        ax.text((x1+x2)/2, y_ruler-0.65, lbl, ha='center', fontsize=8, color=clr)

    # Variable payload
    ax.add_patch(FancyBboxPatch((0.5, y_ruler-1.8), 12.0, 0.6,
                               boxstyle='round,pad=0.02', lw=1.5,
                               ec=C_GREEN, fc=C_GREEN+"22",
                               linestyle='dashed', zorder=3))
    ax.text(6.5, y_ruler-1.5, 'Variable-length Payload  (0 … payload_len bytes)',
            ha='center', va='center', fontsize=9, color=C_GREEN, fontweight='bold', zorder=4)
    ax.text(0.3, y_ruler-1.8, '16', fontsize=7.5, color=C_GREEN)
    ax.text(0.3, y_ruler-2.05, f'+n', fontsize=7.5, color=C_GREEN)

    # Message types
    ax.add_patch(FancyBboxPatch((0.3, 0.3), 5.5, 2.8, boxstyle='round,pad=0.05',
                               lw=1.5, ec=C_BLUE, fc=C_BLUE+"10", zorder=2))
    ax.text(0.6, 2.95, 'Message Types:', fontsize=10, color=C_BLUE, fontweight='bold')
    msg_types = [
        ('0', 'MSG_HEARTBEAT', 'Keepalive ping'),
        ('1', 'MSG_HUD_ALERT', 'Status alert to terminal'),
        ('2', 'MSG_POLICY_REQ', 'Policy enforcement request'),
        ('3', 'MSG_DATA_XFER', 'Binary payload transfer'),
        ('4', 'MSG_LOG_INFO', 'Structured log record'),
    ]
    for i, (code, name, desc) in enumerate(msg_types):
        y = 2.55 - i*0.48
        ax.text(0.6, y, f'{code}:', fontsize=8.5, color=C_BLUE,
                fontfamily='monospace', fontweight='bold')
        ax.text(1.1, y, name, fontsize=8.5, color=C_DARK, fontfamily='monospace')
        ax.text(3.2, y, f'— {desc}', fontsize=8, color=C_GRAY)

    # Broker diagram
    box(ax, 9.5, 2.2, 2.5, 0.8, 'Messenger\nBroker\n(:7201 TCP)', C_PURPLE, bold=True)
    clients = [
        (7.5, 1.0, 'cogman-sup\n(publisher)', C_CYAN),
        (9.5, 0.8, 'cogman-exec\n(publisher)', C_RUST),
        (11.5, 1.0, 'log-collector\n(subscriber)', C_GREEN),
    ]
    for cx, cy, lbl, clr in clients:
        box(ax, cx, cy, 2.2, 0.55, lbl, clr, fontsize=8)
        ax.annotate('', xy=(9.5 + (cx-9.5)*0.3, 1.8),
                    xytext=(cx, cy+0.28),
                    arrowprops=dict(arrowstyle='<->', color=clr, lw=1.2), zorder=4)

    save(fig, 'fig7_8_messenger.png')

# ══════════════════════════════════════════════════════════════════════════════
# Figure 7.9 — Rootfs Directory Layout
# ══════════════════════════════════════════════════════════════════════════════
def fig7_9():
    fig, ax = plt.subplots(figsize=(13, 9))
    ax.set_xlim(0, 13); ax.set_ylim(0, 9); ax.axis('off')
    title_box(fig, 'Figure 7.9 — Minimal Rootfs Directory Layout  (6.3 MB total)')

    tree = [
        (0, '/',                         C_DARK,   True),
        (1,  'sbin/',                    C_CYAN,   True),
        (2,   'init → cogman-supervisor',C_CYAN,   False),
        (1,  'bin/',                     C_BLUE,   True),
        (2,   'sh → /bin/busybox',       C_BLUE,   False),
        (2,   'busybox  (multi-call)',    C_BLUE,   False),
        (1,  'usr/bin/',                 C_BLUE,   True),
        (2,   'cogman-supervisor  (PID1)',C_CYAN,   False),
        (2,   'cogman-executor',         C_CYAN,   False),
        (2,   'cogman-planner',          C_RUST,   False),
        (2,   'cogman-ctl',              C_GREEN,  False),
        (1,  'etc/',                     C_PURPLE, True),
        (2,   'cogman/',                 C_PURPLE, True),
        (3,    'services/',              C_PURPLE, True),
        (4,     'hello.service',         C_GREEN,  False),
        (4,     'heartbeat.service',     C_GREEN,  False),
        (4,     'ctl-probe.service',     C_GREEN,  False),
        (4,     'shutdown.service',      C_GREEN,  False),
        (1,  'proc/  (procfs mount)',     C_GRAY,   True),
        (1,  'sys/   (sysfs mount)',      C_GRAY,   True),
        (1,  'dev/   (devtmpfs mount)',   C_GRAY,   True),
        (1,  'run/   (tmpfs mount)',      C_ORANGE, True),
        (2,   'cogman-supervisor.sock',  C_ORANGE, False),
        (1,  'tmp/',                     C_GRAY,   True),
        (1,  'lib/',                     C_GOLD,   True),
        (2,   'libc.so → musl-libc',     C_GOLD,   False),
    ]

    y_start = 8.5
    x_base = 0.5
    indent = 0.7

    for (depth, name, clr, is_dir) in tree:
        y = y_start
        y_start -= 0.32
        x = x_base + depth * indent
        icon = '📁 ' if is_dir else '   '
        style = 'bold' if is_dir else 'normal'
        ax.text(x, y, ('├─ ' if depth > 0 else '') + name,
                ha='left', va='center', fontsize=9, color=clr,
                fontfamily='monospace', fontweight=style)

    # Size annotations
    sizes = [
        (8.5, 8.5, 'cogman-supervisor', '312 KB', C_CYAN),
        (8.5, 8.0, 'cogman-executor',   '180 KB', C_CYAN),
        (8.5, 7.5, 'cogman-planner',    '1.4 MB', C_RUST),
        (8.5, 7.0, 'busybox',           '1.1 MB', C_BLUE),
        (8.5, 6.5, 'kernel + initramfs','~2.8 MB', C_GRAY),
        (8.5, 6.0, 'Total rootfs',      '6.3 MB', C_DARK),
    ]
    ax.add_patch(FancyBboxPatch((8.2, 5.7), 4.5, 3.2, boxstyle='round,pad=0.1',
                               lw=1.5, ec=C_DARK, fc=C_DARK+"08", zorder=2))
    ax.text(10.45, 8.75, 'Binary Sizes', ha='center', fontsize=10,
            color=C_DARK, fontweight='bold')
    for (x, y, name, sz, clr) in sizes:
        ax.text(x+0.2, y, name, ha='left', va='center', fontsize=8.5, color=clr)
        ax.text(12.5, y, sz, ha='right', va='center', fontsize=8.5, color=clr,
                fontweight='bold')

    # Boot note
    ax.text(0.5, 0.4,
            'Boot: kernel → /sbin/init (cogman-supervisor, PID 1) → mounts vfs → '
            'reads /etc/cogman/services/ → starts 4 verification services',
            fontsize=8.5, color=C_DARK, style='italic')

    save(fig, 'fig7_9_rootfs_layout.png')

# ══════════════════════════════════════════════════════════════════════════════
# Figure 8.1 — Service Boot Sequence on Minimal Rootfs
# ══════════════════════════════════════════════════════════════════════════════
def fig8_1():
    fig, ax = plt.subplots(figsize=(14, 9))
    ax.set_xlim(0, 14); ax.set_ylim(0, 9); ax.axis('off')
    title_box(fig, 'Figure 8.1 — Service Boot Sequence on Minimal Rootfs (QEMU Verified)')

    # Timeline axis
    ax.axhline(1.5, xmin=0.04, xmax=0.96, color=C_DARK, lw=2, zorder=2)
    for x in np.linspace(0.5, 13.5, 14):
        ax.plot([x, x], [1.35, 1.65], color=C_DARK, lw=0.8, zorder=3)
    ax.text(0.5, 1.1, '0 ms', ha='center', fontsize=8, color=C_GRAY)
    ax.text(13.5, 1.1, '~1800 ms', ha='center', fontsize=8, color=C_GRAY)
    ax.text(7.0, 0.7, 'Boot Timeline  (QEMU x86_64, -m 128M)', ha='center',
            fontsize=9, color=C_GRAY, style='italic')

    events = [
        (0.5,  8.5, 'Kernel\nboots', C_GRAY, False),
        (1.5,  7.5, 'execve\n/sbin/init\n(PID 1)', C_CYAN, True),
        (2.8,  8.3, 'mount\nproc sysfs\ndevtmpfs', C_BLUE, False),
        (4.2,  7.2, 'parse\n*.service\nfiles (4)', C_PURPLE, True),
        (5.3,  8.3, 'start\nhello.service\n(oneshot)', C_GREEN, False),
        (6.5,  7.2, 'hello: exit 0\nDONE', C_GREEN, True),
        (7.5,  8.3, 'start\nheartbeat\n(always)', C_CYAN, False),
        (8.6,  7.2, 'heartbeat\nRUNNING\npid=42', C_CYAN, True),
        (9.8,  8.3, 'start\nctl-probe\n(oneshot)', C_BLUE, False),
        (10.8, 7.2, 'ctl list:\nOK\nDONE', C_BLUE, True),
        (11.8, 8.3, 'start\nshutdown\n(oneshot)', C_ORANGE, False),
        (12.8, 7.2, 'All 4 stages\nPASS ✓', C_GREEN, True),
    ]

    for x, y, lbl, clr, above in events:
        ax.plot([x, x], [1.5, 1.5 + (y-1.5)*0.4], color=clr, lw=1, ls=':', zorder=2)
        ax.add_patch(Circle((x, 1.5), 0.12, fc=clr, zorder=4))
        ax.text(x, y, lbl, ha='center', va='center', fontsize=8,
                color=clr, fontweight='bold', zorder=5,
                bbox=dict(fc=clr+"22", ec=clr, pad=3, boxstyle='round'))

    # QEMU command
    ax.text(0.4, 0.3,
            'qemu-system-x86_64 -kernel /boot/vmlinuz -drive file=rootfs.img,format=raw '
            '-append "console=ttyS0 root=/dev/sda rw init=/sbin/init quiet" '
            '-nographic -m 128M -serial mon:stdio',
            fontsize=7.5, color=C_DARK, fontfamily='monospace',
            bbox=dict(fc=C_GRAY+"15", ec=C_GRAY, pad=5, boxstyle='round'))

    # Performance badge
    ax.add_patch(FancyBboxPatch((10.0, 2.5), 3.5, 2.0, boxstyle='round,pad=0.1',
                               lw=2, ec=C_GREEN, fc=C_GREEN+"15", zorder=3))
    ax.text(11.75, 4.3, 'Performance', ha='center', fontsize=9.5,
            color=C_GREEN, fontweight='bold')
    perf = [('Plan resolution', '8 ms', '56× faster'),
            ('Peak memory', '4 MB', '21× less'),
            ('Per-step overhead', '0.2 ms', '50× faster')]
    for i, (metric, val, vs) in enumerate(perf):
        y = 3.9 - i*0.48
        ax.text(10.2, y, metric, fontsize=8, color=C_DARK)
        ax.text(12.1, y, val, fontsize=8.5, color=C_GREEN, fontweight='bold')
        ax.text(13.0, y, vs, fontsize=7.5, color=C_GRAY)

    save(fig, 'fig8_1_boot_sequence.png')

# ══════════════════════════════════════════════════════════════════════════════
# Run all
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print('Generating figures ...')
    fig1_1()
    fig1_2()
    fig6_3()
    fig6_4()
    fig6_5()
    fig6_6()
    fig6_7()
    fig6_8()
    fig6_9()
    fig6_10()
    fig6_11()
    fig7_1()
    fig7_2()
    fig7_3()
    fig7_4()
    fig7_5()
    fig7_6()
    fig7_7()
    fig7_8()
    fig7_9()
    fig8_1()
    print('Done — all 21 figures written to', OUT)
