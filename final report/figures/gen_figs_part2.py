"""Part 2: Figures 6.7, 6.8, 6.9, 6.10, 6.11"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Circle
import numpy as np, os

OUT = os.path.dirname(os.path.abspath(__file__))

BG=  "#F8F9FA"; RUST="#C0392B"; TEAL="#0E6655"; NAVY="#1A3A5C"
GRAY="#5D6D7E"; GREEN="#1E8449"; ORG="#CA6F1E"; RED="#922B21"
PURP="#6C3483"; GOLD="#9A7D0A"; BLK="#1C2833"

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'text.color':BLK})

def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=180, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    plt.close(fig)
    print("  saved", name)

def arr(ax, x1, y1, x2, y2, color=BLK, lw=1.5, label='',
        lx=None, ly=None, rad=0.0, ls='-', style='->'):
    ax.annotate('', xy=(x2,y2), xytext=(x1,y1),
                arrowprops=dict(arrowstyle=style, color=color, lw=lw,
                                connectionstyle=f'arc3,rad={rad}',
                                linestyle=ls), zorder=5)
    if label:
        mx = lx if lx is not None else (x1+x2)/2
        my = ly if ly is not None else (y1+y2)/2 + 0.08
        ax.text(mx, my, label, ha='center', va='bottom', fontsize=8,
                color=color, zorder=6,
                bbox=dict(fc=BG, ec='none', pad=1))

# ─── UML class box ────────────────────────────────────────────────────────────
def uml_class(ax, cx, cy, title, attrs, methods, color, fs=7.8):
    line_h = 0.26
    n_a = len(attrs); n_m = len(methods)
    hdr_h = 0.38
    body_h = line_h * (n_a + n_m) + (0.12 if (n_a and n_m) else 0) + 0.12
    total_h = hdr_h + body_h
    w = 3.2
    left = cx - w/2; bot = cy - total_h/2; top = cy + total_h/2

    # outer box
    ax.add_patch(FancyBboxPatch((left, bot), w, total_h,
                                boxstyle='round,pad=0.01', lw=1.8,
                                ec=color, fc=BG, zorder=3))
    # header fill
    ax.add_patch(FancyBboxPatch((left, top-hdr_h), w, hdr_h,
                                boxstyle='round,pad=0.01',
                                lw=0, ec=color, fc=color+'35', zorder=4))
    ax.text(cx, top - hdr_h/2, title, ha='center', va='center',
            fontsize=fs+0.5, fontweight='bold', color=color, zorder=5)

    cur = top - hdr_h
    ax.plot([left, left+w], [cur, cur], color=color, lw=1, zorder=4)

    for a in attrs:
        cur -= line_h
        ax.text(left+0.1, cur+line_h/2, a, ha='left', va='center',
                fontsize=fs, color=BLK, zorder=5)

    if attrs and methods:
        ax.plot([left, left+w], [cur, cur], color=color, lw=0.8, ls='--', zorder=4)

    for m in methods:
        cur -= line_h
        ax.text(left+0.1, cur+line_h/2, m, ha='left', va='center',
                fontsize=fs-0.5, color=GRAY, style='italic', zorder=5)

    return w, total_h

def rel_arrow(ax, x1,y1, x2,y2, style='->', color=GRAY, lw=1.3, rad=0.0, label=''):
    ax.annotate('', xy=(x2,y2), xytext=(x1,y1),
                arrowprops=dict(arrowstyle=style, color=color, lw=lw,
                                connectionstyle=f'arc3,rad={rad}'), zorder=6)
    if label:
        mx=(x1+x2)/2; my=(y1+y2)/2+0.1
        ax.text(mx,my,label,ha='center',fontsize=7.5,color=color,zorder=7,
                bbox=dict(fc=BG,ec='none',pad=1))

# ═════════════════════════════════════════════════════════════════════════════
# Figure 6.7  —  Class Diagram: cogman-planner
# ═════════════════════════════════════════════════════════════════════════════
def fig6_7():
    fig, ax = plt.subplots(figsize=(18, 11), facecolor=BG)
    ax.set_facecolor(BG); ax.axis('off')
    ax.set_xlim(0, 18); ax.set_ylim(0, 11)
    ax.set_title("Figure 6.7 — Class Diagram: cogman-planner (Rust)",
                 fontsize=12, fontweight='bold', color=NAVY, pad=8)

    # ── class positions (cx, cy) ──────────────────────────────────────────
    uml_class(ax, 2.2, 9.5, "Cli",
              ["cmd: Command"],
              ["+run() → Result<(),Error>"], RUST)

    uml_class(ax, 6.0, 9.5, "Command",
              ["Build { meta: PathBuf, out: PathBuf }",
               "Install { meta: PathBuf }",
               "Deploy  { plan: PathBuf }"],
              [], RUST)

    uml_class(ax, 11.0, 9.5, "PackageMetadata",
              ["identity: Identity",
               "builder:  Builder",
               "installer: Installer",
               "policy:   Policy",
               "depends:  Vec<String>"],
              ["+validate() → Result",
               "+load(path) → Result"], NAVY)

    uml_class(ax, 15.5, 9.5, "Identity",
              ["name:     String",
               "version:  String",
               "category: String",
               "source:   String"],
              [], NAVY)

    uml_class(ax, 2.2, 6.2, "RecursiveLoader",
              ["visited:  HashSet<String>",
               "base_dir: PathBuf"],
              ["+load(pkg) → PackageMetadata",
               "+load_all() → Vec<PackageMetadata>"], TEAL)

    uml_class(ax, 7.0, 6.2, "DependencyGraph",
              ["nodes: HashMap<String,Node>",
               "edges: Vec<(String,String)>"],
              ["+add_node(name: &str)",
               "+add_edge(a,b: &str)",
               "+topo_sort() → Vec<String>",
               "+has_cycle() → bool"], TEAL)

    uml_class(ax, 12.2, 6.2, "PlanWriter",
              ["steps:  Vec<PlanStep>",
               "strtab: Vec<u8>",
               "cache:  FnvHashMap<u64,PathBuf>"],
              ["+add_step(s: PlanStep)",
               "+emit(path: &Path) → Result"], GREEN)

    uml_class(ax, 2.2, 3.0, "Policy",
              ["allow_write:   Vec<PathBuf>",
               "allow_network: bool",
               "allow_exec:    Vec<String>"],
              ["+check_path(p) → bool"], ORG)

    uml_class(ax, 7.0, 3.0, "PlanStep",
              ["op:          OpCode",
               "fail_policy: FailPolicy",
               "cmd_off:     u32",
               "workdir_off: u32",
               "env_off:     u32"],
              [], GREEN)

    uml_class(ax, 12.2, 3.0, "OpCode",
              ["OP_EXEC   = 0",
               "OP_MKDIR  = 1",
               "OP_COPY   = 2",
               "OP_CHMOD  = 3",
               "OP_SYMLINK= 4"],
              [], GREEN)

    # ── relationships ──────────────────────────────────────────────────────
    rel_arrow(ax, 3.8, 9.5, 4.4, 9.5, label='composes')       # Cli → Command
    rel_arrow(ax, 7.6, 9.5, 8.4, 9.5, label='creates')        # Cmd → PkgMeta
    rel_arrow(ax, 13.6, 9.5, 14.0, 9.5, label='contains')     # PkgMeta → Identity
    rel_arrow(ax, 11.0, 8.4, 7.0, 7.2, label='feeds', rad=0.1) # PkgMeta → DepGraph
    rel_arrow(ax, 8.6, 6.2, 10.6, 6.2, label='→ sort')        # DepGraph → PlanWriter
    rel_arrow(ax, 12.2, 5.1, 7.0, 3.8, label='writes')        # PlanWriter → PlanStep
    rel_arrow(ax, 8.6, 3.0, 10.6, 3.0, label='uses')          # PlanStep → OpCode
    rel_arrow(ax, 2.2, 5.1, 2.2, 3.8)                         # Loader → Policy
    rel_arrow(ax, 3.8, 6.2, 5.4, 6.2, style='-|>', label='invokes') # Loader → DepGraph

    save(fig, 'fig6_7_class_planner.png')

# ═════════════════════════════════════════════════════════════════════════════
# Figure 6.8  —  Class Diagram: cogman-supervisor
# ═════════════════════════════════════════════════════════════════════════════
def fig6_8():
    fig, ax = plt.subplots(figsize=(18, 10), facecolor=BG)
    ax.set_facecolor(BG); ax.axis('off')
    ax.set_xlim(0,18); ax.set_ylim(0,10)
    ax.set_title("Figure 6.8 — Class Diagram: cogman-supervisor (C11)",
                 fontsize=12, fontweight='bold', color=NAVY, pad=8)

    uml_class(ax, 3.0, 8.0, "Supervisor  [global singleton]",
              ["svc_table[64]: Service",
               "svc_count:     int",
               "sigchld_pipe:  int[2]",
               "ctl_fd:        int",
               "running:       bool"],
              ["+init()",
               "+run_loop()",
               "+drain_sigchld()",
               "+reap_children()",
               "+shutdown()"], TEAL)

    uml_class(ax, 9.5, 8.0, "Service",
              ["name[64]:       char",
               "command[256]:   char",
               "type:           SvcType",
               "restart:        SvcRestart",
               "state:          SvcState",
               "pid:            pid_t",
               "restart_count:  int",
               "deps[8][64]:    char"],
              ["+start(sup: *Supervisor)",
               "+stop()",
               "+on_exit(status: int)"], NAVY)

    uml_class(ax, 15.5, 8.0, "ServiceFileParser",
              ["path[256]: char"],
              ["+parse(path) → Service",
               "+parse_all(dir) → int"], GRAY)

    uml_class(ax, 2.0, 4.0, "SvcType  [enum]",
              ["PROCESS = 0",
               "ONESHOT  = 1",
               "FORKING  = 2"],
              [], TEAL)

    uml_class(ax, 7.0, 4.0, "SvcState  [enum]",
              ["STOPPED",
               "STARTING",
               "RUNNING",
               "RESTARTING",
               "FAILED",
               "DONE"],
              [], ORG)

    uml_class(ax, 12.5, 4.0, "SvcRestart  [enum]",
              ["NEVER      = 0",
               "ON_FAILURE = 1",
               "ALWAYS     = 2"],
              [], GREEN)

    uml_class(ax, 3.0, 1.3, "CtlServer",
              ["sock_fd:       int",
               "sock_path[128]:char"],
              ["+ctl_init(path: char*)",
               "+ctl_accept(sup: *Supervisor)",
               "+cmd_list(fd: int)",
               "+cmd_start/stop(fd,name)"], PURP)

    # relationships
    rel_arrow(ax, 4.6, 8.0, 7.9, 8.0, label='owns 0..*', rad=0.0)
    rel_arrow(ax, 11.1, 8.0, 13.9, 8.0, label='parsed by')
    rel_arrow(ax, 3.0, 6.6, 2.0, 5.1,  label='has type')
    rel_arrow(ax, 5.0, 6.6, 7.0, 5.2,  label='has state')
    rel_arrow(ax, 5.0, 6.6, 12.5, 5.2, label='has restart', rad=-0.1)
    rel_arrow(ax, 3.0, 6.6, 3.0, 2.2,  label='uses CtlServer')

    save(fig, 'fig6_8_class_supervisor.png')

# ─── Sequence diagram helpers ─────────────────────────────────────────────────
def lifeline(ax, cx, y_top, y_bot, label, color, fs=8.5):
    w = 2.4; h = 0.55
    ax.add_patch(FancyBboxPatch((cx-w/2, y_top), w, h,
                                boxstyle='round,pad=0.04',
                                lw=1.8, ec=color, fc=color+'30', zorder=4))
    ax.text(cx, y_top+h/2, label, ha='center', va='center',
            fontsize=fs, fontweight='bold', color=color, zorder=5)
    ax.plot([cx, cx], [y_top, y_bot], color=color, lw=1, ls='--', zorder=2)

def activation(ax, cx, y_top, y_bot, color):
    ax.add_patch(FancyBboxPatch((cx-0.1, y_bot), 0.2, y_top-y_bot,
                                boxstyle='square,pad=0', lw=1.2,
                                ec=color, fc=color+'40', zorder=3))

def smsg(ax, x1, x2, y, label, color=BLK, ret=False, fs=8):
    sty = '<-' if ret else '->'
    ls  = 'dashed' if ret else 'solid'
    ax.annotate('', xy=(x2,y), xytext=(x1,y),
                arrowprops=dict(arrowstyle=sty, color=color, lw=1.5,
                                linestyle=ls), zorder=4)
    mx = (x1+x2)/2
    dy = 0.07
    ax.text(mx, y+dy, label, ha='center', va='bottom', fontsize=fs,
            color=color, zorder=5,
            bbox=dict(fc=BG, ec='none', pad=1))

def snote(ax, cx, y, text, color):
    """self-message (loop arrow on a lifeline)"""
    ax.annotate(text, xy=(cx, y-0.2), xytext=(cx+0.9, y),
                fontsize=7.5, color=color, ha='left',
                arrowprops=dict(arrowstyle='->', color=color, lw=1.0,
                                connectionstyle='arc3,rad=-0.4'))

# ═════════════════════════════════════════════════════════════════════════════
# Figure 6.9  —  Sequence: Package Build Flow
# ═════════════════════════════════════════════════════════════════════════════
def fig6_9():
    fig, ax = plt.subplots(figsize=(16, 12), facecolor=BG)
    ax.set_facecolor(BG); ax.axis('off')
    ax.set_xlim(0,16); ax.set_ylim(0,12)
    ax.set_title("Figure 6.9 — Sequence Diagram: Package Build Flow",
                 fontsize=12, fontweight='bold', color=NAVY, pad=8)

    # Lifelines  cx, y_top (header bottom = y_top), y_bot
    LLs = [
        (1.3,  "Operator",       TEAL,  11.0, 0.5),
        (4.2,  "cogman-planner", RUST,  11.0, 0.5),
        (7.2,  "MetadataLoader", NAVY,  11.0, 0.5),
        (10.2, "DepGraph",       NAVY,  11.0, 0.5),
        (13.2, "PlanWriter",     GREEN, 11.0, 0.5),
    ]
    for cx,lbl,clr,yt,yb in LLs:
        lifeline(ax, cx, yt, yb, lbl, clr)

    # Messages (x1, x2, y, label, color, is_return)
    msgs = [
        (1.3, 4.2,  10.5, "invoke cogman-planner(meta.toml, out.bin)", TEAL),
        (4.2, 7.2,  9.9,  "load(path='meta.toml')", RUST),
        (7.2, 4.2,  9.3,  "return PackageMetadata", NAVY, True),
        (4.2, 7.2,  8.7,  "load_dep('libssl')", RUST),
        (7.2, 4.2,  8.1,  "return PackageMetadata(libssl)", NAVY, True),
        (4.2, 10.2, 7.5,  "build_graph(all_meta[])", RUST),
        (10.2,4.2,  6.9,  "return sorted_packages[]", NAVY, True),
        (4.2, 10.2, 6.3,  "topo_sort()", RUST),
        (10.2,4.2,  5.7,  "return ordered_list[]", NAVY, True),
        (4.2, 13.2, 5.1,  "emit_plan(ordered_list)", RUST),
        (13.2,13.2, 4.5,  "check FNV-1a cache", GREEN),
        (13.2,4.2,  3.9,  "return plan_path", GREEN, True),
        (4.2, 1.3,  3.3,  "exit 0  (plan written)", TEAL),
    ]
    for m in msgs:
        x1,x2,y,lbl = m[0],m[1],m[2],m[3]
        clr = m[4] if len(m)>4 else BLK
        ret = m[5] if len(m)>5 else False
        if x1 == x2:
            snote(ax, x1, y, lbl, clr)
        else:
            smsg(ax, x1, x2, y, lbl, clr, ret)

    # Activation bars
    activation(ax, 4.2, 10.8, 3.1, RUST)
    activation(ax, 7.2, 9.8, 8.0, NAVY)
    activation(ax, 10.2,7.4, 5.5, NAVY)
    activation(ax, 13.2,5.0, 3.7, GREEN)

    save(fig, 'fig6_9_seq_build.png')

# ═════════════════════════════════════════════════════════════════════════════
# Figure 6.10 —  Sequence: Service Start Flow
# ═════════════════════════════════════════════════════════════════════════════
def fig6_10():
    fig, ax = plt.subplots(figsize=(17, 12), facecolor=BG)
    ax.set_facecolor(BG); ax.axis('off')
    ax.set_xlim(0,17); ax.set_ylim(0,12)
    ax.set_title("Figure 6.10 — Sequence Diagram: Service Start Flow",
                 fontsize=12, fontweight='bold', color=NAVY, pad=8)

    LLs = [
        (1.3,  "Operator\n(cogman-ctl)", GREEN, 11.0, 0.5),
        (4.5,  "cogman-\nsupervisor",   TEAL,  11.0, 0.5),
        (7.5,  "SvcFile\nParser",       NAVY,  11.0, 0.5),
        (10.5, "Linux\nKernel",         GRAY,  11.0, 0.5),
        (13.5, "Service\nProcess",      RUST,  11.0, 0.5),
        (15.8, "SIGCHLD\nPipe",         ORG,   11.0, 0.5),
    ]
    for cx,lbl,clr,yt,yb in LLs:
        lifeline(ax, cx, yt, yb, lbl, clr)

    msgs = [
        (1.3, 4.5,  10.5, "connect /run/cogman-supervisor.sock", GREEN),
        (1.3, 4.5,  9.8,  'send "start heartbeat\\n"', GREEN),
        (4.5, 7.5,  9.1,  "parse_all(/etc/cogman/services/)", TEAL),
        (7.5, 4.5,  8.4,  "return Service{heartbeat,...}", NAVY, True),
        (4.5, 4.5,  7.7,  "check_deps(heartbeat) → OK", TEAL),
        (4.5, 10.5, 7.0,  "fork()", TEAL),
        (10.5,4.5,  6.3,  "return child_pid=42", GRAY, True),
        (10.5,13.5, 5.6,  'exec("/usr/bin/heartbeat")', GRAY),
        (4.5, 4.5,  4.9,  "set state=STARTING, pid=42", TEAL),
        (13.5,15.8, 4.2,  "process running → SIGCHLD raised", RUST),
        (15.8,15.8, 3.5,  "write(pipe_w, 1)", ORG),
        (15.8,4.5,  2.8,  "pipe_r readable", ORG, True),
        (4.5, 4.5,  2.1,  "waitpid(42, WNOHANG) → set RUNNING", TEAL),
        (4.5, 1.3,  1.4,  'send "OK pid=42\\n"', TEAL),
    ]
    for m in msgs:
        x1,x2,y,lbl = m[0],m[1],m[2],m[3]
        clr = m[4] if len(m)>4 else BLK
        ret = m[5] if len(m)>5 else False
        if x1 == x2:
            snote(ax, x1, y, lbl, clr)
        else:
            smsg(ax, x1, x2, y, lbl, clr, ret)

    activation(ax, 4.5, 10.8, 1.2, TEAL)
    activation(ax, 10.5,6.9, 5.5, GRAY)

    save(fig, 'fig6_10_seq_start.png')

# ═════════════════════════════════════════════════════════════════════════════
# Figure 6.11 —  Component Diagram
# ═════════════════════════════════════════════════════════════════════════════
def component(ax, cx, cy, w, h, title, sub, color):
    """Draw a UML component box"""
    ax.add_patch(FancyBboxPatch((cx-w/2, cy-h/2), w, h,
                                boxstyle='round,pad=0.06',
                                lw=2, ec=color, fc=color+'18', zorder=3))
    # component icon (two small tabs)
    ix = cx + w/2 - 0.45; iy = cy + h/2 - 0.22
    for dy in [0.0, -0.18]:
        ax.add_patch(FancyBboxPatch((ix, iy+dy), 0.35, 0.14,
                                   boxstyle='square,pad=0',
                                   lw=1, ec=color, fc=color+'60', zorder=5))
    ax.text(cx - 0.15, cy + 0.12, title, ha='center', va='center',
            fontsize=9, fontweight='bold', color=color, zorder=4)
    if sub:
        ax.text(cx - 0.15, cy - 0.18, sub, ha='center', va='center',
                fontsize=7.5, color=GRAY, style='italic', zorder=4)

def fig6_11():
    fig, ax = plt.subplots(figsize=(16, 10), facecolor=BG)
    ax.set_facecolor(BG); ax.axis('off')
    ax.set_xlim(0,16); ax.set_ylim(0,10)
    ax.set_title("Figure 6.11 — Component Diagram",
                 fontsize=12, fontweight='bold', color=NAVY, pad=8)

    # HOST BUILD env
    ax.add_patch(FancyBboxPatch((0.3, 4.5), 6.4, 5.0,
                                boxstyle='round,pad=0.1', lw=2,
                                ec=RUST, fc=RUST+'06', ls='--', zorder=0))
    ax.text(3.5, 9.3, "Host Build Environment", ha='center',
            fontsize=10, color=RUST, fontweight='bold')

    component(ax, 3.0, 8.1, 4.8, 1.1,
              "cogman-planner", "Rust · ~1200 LOC", RUST)
    component(ax, 3.0, 6.4, 4.8, 1.1,
              "cogman-executor", "C11 · ~1144 LOC", TEAL)
    component(ax, 3.0, 5.1, 3.8, 0.7,
              "CGM2PLAN binary", "64-byte hdr + step[]", GOLD)

    # planner → plan file
    arr(ax, 3.0, 7.55, 3.0, 5.45, GOLD, 1.5, label='emits', lx=3.5, ly=6.55)
    # executor reads plan file
    arr(ax, 2.0, 5.45, 2.0, 6.95, TEAL, 1.5, label='reads', lx=1.4, ly=6.15)

    # TARGET ROOTFS
    ax.add_patch(FancyBboxPatch((7.8, 0.3), 8.0, 9.2,
                                boxstyle='round,pad=0.1', lw=2,
                                ec=TEAL, fc=TEAL+'06', ls='--', zorder=0))
    ax.text(11.8, 9.3, "Target Rootfs  (/)",
            ha='center', fontsize=10, color=TEAL, fontweight='bold')

    component(ax, 10.2, 7.8, 4.0, 1.1,
              "cogman-supervisor", "PID 1 · C11 · 1561 LOC", TEAL)
    component(ax, 10.2, 5.9, 4.0, 1.1,
              "cogman-ctl", "client · C11 · 142 LOC", GREEN)
    component(ax, 14.5, 7.8, 2.6, 1.1,
              "Service\nProcesses", "heartbeat, hello…", RUST)
    component(ax, 14.5, 5.9, 2.6, 1.1,
              "messenger\nbroker", "TLV · :7201", PURP)
    component(ax, 9.0,  4.0, 3.8, 0.9,
              "/etc/cogman/services/", "*.service (INI)", NAVY)
    component(ax, 13.5, 4.0, 3.0, 0.9,
              "/sbin/init", "symlink → cogman-sup", GRAY)
    component(ax, 9.0,  2.2, 3.8, 0.9,
              "/run/cogman-\nsupervisor.sock", "AF_UNIX socket", PURP)

    # Internal connections
    arr(ax, 12.2, 7.8, 13.2, 7.8, RUST, 1.5, label='fork/exec')
    arr(ax, 12.2, 7.5, 13.2, 6.3, PURP, 1.3, label='IPC/TLV', rad=0.1)
    arr(ax, 12.2, 5.9, 12.2, 7.25, GREEN, 1.5, label='socket', lx=12.7, ly=6.5)
    arr(ax, 10.2, 7.25, 9.5, 4.45, NAVY, 1.3, label='reads services', lx=8.8, ly=5.9)
    arr(ax, 10.2, 7.25, 10.2, 2.65, PURP, 1.3, label='creates sock', lx=11.0, ly=4.9)
    arr(ax, 13.5, 3.55, 13.5, 2.0, GRAY, 1.0, label='resolved as')

    # Deploy arrow HOST → TARGET
    ax.annotate('', xy=(7.8, 5.5), xytext=(6.7, 5.5),
                arrowprops=dict(arrowstyle='->', color=GOLD, lw=2.5,
                                linestyle='dashed'), zorder=5)
    ax.text(7.25, 5.75, 'deploy\nrootfs', ha='center', fontsize=8.5, color=GOLD)

    save(fig, 'fig6_11_component.png')

if __name__ == '__main__':
    print("Part 2 …")
    fig6_7(); fig6_8(); fig6_9(); fig6_10(); fig6_11()
    print("Part 2 done.")
