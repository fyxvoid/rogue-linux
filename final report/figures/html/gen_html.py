"""Generate all HTML figure files."""
import os
DIR = os.path.dirname(os.path.abspath(__file__))

def write(name, content):
    with open(os.path.join(DIR, name), 'w') as f:
        f.write(content)
    print(f"  wrote {name}")

CSS = '<link rel="stylesheet" href="common.css">'

# ── helpers ───────────────────────────────────────────────────────────────────
def page(title, body, extra_css=""):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">{CSS}
<style>{extra_css}</style></head><body><div class="page">
<h1 class="fig-title">{title}</h1>
{body}
</div></body></html>"""

def box(label, cls, w=150, sub=""):
    sub_html = f'<br><small style="font-weight:400;font-size:10px;color:var(--gray)">{sub}</small>' if sub else ""
    return f'<div class="box {cls}" style="min-width:{w}px;display:flex;flex-direction:column;justify-content:center">{label}{sub_html}</div>'

def arr(label="", color="var(--gray)"):
    lbl = f'<div class="lbl">{label}</div>' if label else ""
    return f'<div class="arrow" style="color:{color}">→{lbl}</div>'

def darr(label=""):  # down arrow
    lbl = f'<div style="font-size:10px;color:var(--gray);text-align:center">{label}</div>' if label else ""
    return f'<div style="text-align:center;font-size:22px;color:var(--gray);line-height:1">{lbl}↓</div>'

# ══════════════════════════════════════════════════════════════════════════════
# fig1_2  Runtime Architecture
# ══════════════════════════════════════════════════════════════════════════════
write("fig1_2.html", page("Figure 1.2 — Cogman Runtime Architecture", """
<style>
.layer{display:flex;align-items:center;justify-content:center;gap:14px;margin:6px 0;}
.boundary2{border:2px dashed var(--teal);border-radius:12px;padding:18px 24px;}
.lbl2{font-size:11px;color:var(--teal);font-weight:700;margin-bottom:10px;}
.pipe-note{font-size:11px;color:var(--org);border:1.5px solid var(--org);border-radius:6px;padding:5px 10px;background:#CA6F1E0D;}
</style>
<div class="boundary2">
<div class="lbl2">TARGET ROOTFS (x86_64 · 6.3 MB)</div>

<div class="layer">
  <div class="box gray" style="min-width:400px;min-height:50px">Linux Kernel &nbsp;(PID 0)</div>
</div>
<div style="text-align:center;font-size:13px;color:var(--gray);margin:2px 0">↓ execve /sbin/init</div>
<div class="layer">
  <div class="box teal" style="min-width:560px;min-height:56px;font-size:13px">
    cogman-supervisor &nbsp;(PID 1 · /sbin/init)<br>
    <small style="font-weight:400;font-size:10.5px;color:var(--gray)">100 ms main loop · select(pipe_r, ctl_fd) · drain SIGCHLD · accept ctl</small>
  </div>
</div>

<div class="layer" style="margin-top:4px">
  <div class="box navy" style="min-width:200px;font-size:11px">/etc/cogman/services/<br>*.service (INI)</div>
  <div class="arrow" style="font-size:13px;color:var(--navy)">→<div class="lbl">parse on<br>startup</div></div>
  <div style="width:60px"></div>
  <div class="arrow" style="font-size:13px;color:var(--purp)">→<div class="lbl">Unix socket<br>SOCK_STREAM</div></div>
  <div class="box purp" style="min-width:200px;font-size:11px">/run/cogman-<br>supervisor.sock</div>
  <div class="arrow" style="font-size:13px;color:var(--purp)">←<div class="lbl">connect</div></div>
  <div class="box purp" style="min-width:160px;font-size:11px">cogman-ctl<br>(client)</div>
</div>

<div style="display:flex;justify-content:center;gap:8px;margin:6px 0;font-size:12px;color:var(--gray)">fork/exec &nbsp;↙&nbsp;&nbsp;&nbsp;↓&nbsp;&nbsp;&nbsp;↓&nbsp;&nbsp;&nbsp;↘&nbsp; fork/exec</div>

<div class="layer" style="gap:8px">
  <div class="box green"  style="min-width:175px;font-size:11px">hello.service<br><small style="font-weight:400">oneshot · no deps</small></div>
  <div class="box teal"   style="min-width:185px;font-size:11px">heartbeat.service<br><small style="font-weight:400">process · restart=always</small></div>
  <div class="box navy"   style="min-width:175px;font-size:11px">ctl-probe.service<br><small style="font-weight:400">oneshot · after=heartbeat</small></div>
  <div class="box rust"   style="min-width:175px;font-size:11px">shutdown.service<br><small style="font-weight:400">oneshot · last</small></div>
</div>

<div class="layer" style="margin-top:10px;gap:20px">
  <div class="pipe-note">SIGCHLD → write(pipe_w,1) &nbsp;[async-signal-safe]</div>
  <div class="pipe-note">waitpid(-1, WNOHANG) in main loop</div>
  <div class="pipe-note">state: STOPPED→STARTING→RUNNING→RESTARTING→FAILED→DONE</div>
</div>
</div>
"""))

# ══════════════════════════════════════════════════════════════════════════════
# fig6_3  DFD Level 0
# ══════════════════════════════════════════════════════════════════════════════
write("fig6_3.html", page("Figure 6.3 — DFD Level 0: Context Diagram", """
<style>
.dfd0{display:grid;grid-template-columns:220px 1fr 220px;grid-template-rows:auto auto auto;gap:0;align-items:center;justify-items:center;width:900px;margin:auto;}
.entity{border:2.5px solid;border-radius:8px;padding:14px 18px;font-size:12.5px;font-weight:700;text-align:center;width:190px;}
.process-circle{width:200px;height:200px;border-radius:50%;border:3px solid var(--navy);background:#1A3A5C0D;display:flex;flex-direction:column;align-items:center;justify-content:center;font-size:13px;font-weight:700;color:var(--navy);text-align:center;}
.arr-cell{display:flex;flex-direction:column;align-items:center;justify-content:center;font-size:13px;color:var(--gray);gap:4px;padding:10px;}
.arr-lbl{font-size:10px;text-align:center;line-height:1.3;}
.store{border-left:3px solid var(--gray);border-right:none;border-top:1px solid var(--gray);border-bottom:1px solid var(--gray);padding:8px 16px;font-size:11px;color:var(--gray);background:#5D6D7E0A;width:340px;text-align:center;}
</style>
<div class="dfd0">
  <!-- row1: top entity -->
  <div></div>
  <div class="entity" style="color:var(--rust);border-color:var(--rust);background:#C0392B0D">Package<br>Author</div>
  <div></div>

  <!-- row2: left, center, right -->
  <div style="display:flex;flex-direction:column;gap:40px;align-items:center">
    <div class="entity" style="color:var(--rust);border-color:var(--rust);background:#C0392B0D">Package<br>Author</div>
    <div class="entity" style="color:var(--teal);border-color:var(--teal);background:#0E66550D">Build System<br>Operator</div>
  </div>

  <div style="display:flex;flex-direction:column;align-items:center;gap:6px">
    <div class="arr-cell">
      <span style="color:var(--rust)">→ TOML package metadata →</span>
    </div>
    <div class="process-circle">Cogman<br><span style="font-size:11px;font-weight:400;color:var(--gray)">Build +<br>Runtime System</span></div>
    <div class="arr-cell" style="display:flex;flex-direction:row;gap:20px">
      <span style="color:var(--teal);font-size:11px">← build logs &amp; plan file ←</span>
    </div>
    <div class="arr-cell">
      <span style="color:var(--teal);font-size:11px">→ invoke planner / executor →</span>
    </div>
  </div>

  <div style="display:flex;flex-direction:column;gap:40px;align-items:center">
    <div></div>
    <div class="entity" style="color:var(--green);border-color:var(--green);background:#1E84490D">Runtime<br>Operator</div>
  </div>

  <!-- row3: data stores -->
  <div></div>
  <div style="display:flex;flex-direction:column;gap:8px;align-items:center;margin-top:12px">
    <div class="store">D1 — CGM2PLAN binary file</div>
    <div class="store">D2 — /etc/cogman/services/</div>
  </div>
  <div></div>
</div>
<div style="margin-top:16px;display:flex;justify-content:center;gap:30px">
  <div style="font-size:11px;color:var(--green)">Runtime Operator: service commands (cogman-ctl) ⇄ service status &amp; logs</div>
</div>
"""))

# ══════════════════════════════════════════════════════════════════════════════
# fig6_4  DFD Level 1
# ══════════════════════════════════════════════════════════════════════════════
write("fig6_4.html", page("Figure 6.4 — DFD Level 1: Build Subsystem", """
<style>
.dfd1{display:flex;align-items:center;justify-content:center;gap:0;}
.proc{width:120px;height:120px;border-radius:50%;border:2.5px solid;display:flex;flex-direction:column;align-items:center;justify-content:center;font-size:11px;font-weight:700;text-align:center;padding:8px;}
.darr{display:flex;flex-direction:column;align-items:center;font-size:20px;color:var(--gray);margin:4px 0;}
.dstore{border-left:3px solid;border-top:1.5px solid;border-bottom:1.5px solid;border-right:none;padding:6px 12px;font-size:10.5px;font-weight:600;text-align:center;border-radius:0 6px 6px 0;margin-top:4px;}
.pcol{display:flex;flex-direction:column;align-items:center;gap:6px;}
.harr{padding:0 4px;font-size:20px;color:var(--gray);display:flex;flex-direction:column;align-items:center;justify-content:center;}
.harr .lbl{font-size:9.5px;text-align:center;white-space:nowrap;}
</style>
<div class="dfd1">
  <div class="pcol">
    <div class="proc" style="color:var(--rust);border-color:var(--rust);background:#C0392B0D">1<br>Load &amp;<br>Validate<br>Metadata</div>
    <div class="darr">↕<div style="font-size:9px">D1·packages/<br>*.toml</div></div>
    <div class="dstore" style="color:var(--rust);border-color:var(--rust);background:#C0392B0A;width:110px">D1 packages/<br>*.toml</div>
  </div>
  <div class="harr">→<div class="lbl">PackageMeta<br>struct</div></div>
  <div class="pcol">
    <div class="proc" style="color:var(--navy);border-color:var(--navy);background:#1A3A5C0D">2<br>Resolve<br>Dep<br>Graph</div>
    <div class="darr">↕<div style="font-size:9px">D2·dep cache</div></div>
    <div class="dstore" style="color:var(--navy);border-color:var(--navy);background:#1A3A5C0A;width:110px">D2 dep graph<br>cache</div>
  </div>
  <div class="harr">→<div class="lbl">validated<br>DAG</div></div>
  <div class="pcol">
    <div class="proc" style="color:var(--org);border-color:var(--org);background:#CA6F1E0D">3<br>Enforce<br>Policy</div>
    <div class="darr">↕<div style="font-size:9px">D3·policy</div></div>
    <div class="dstore" style="color:var(--org);border-color:var(--org);background:#CA6F1E0A;width:110px">D3 policy<br>rules</div>
  </div>
  <div class="harr">→<div class="lbl">policy-OK<br>DAG</div></div>
  <div class="pcol">
    <div class="proc" style="color:var(--teal);border-color:var(--teal);background:#0E66550D">4<br>Emit<br>Binary<br>Plan</div>
    <div class="darr">↕<div style="font-size:9px">D4·CGM2PLAN</div></div>
    <div class="dstore" style="color:var(--teal);border-color:var(--teal);background:#0E66550A;width:110px">D4 CGM2PLAN<br>file</div>
  </div>
  <div class="harr">→<div class="lbl">plan<br>path</div></div>
  <div class="pcol">
    <div class="proc" style="color:var(--green);border-color:var(--green);background:#1E84490D">5<br>Execute<br>Plan<br>Steps</div>
    <div class="darr">↕<div style="font-size:9px">D5·staging</div></div>
    <div class="dstore" style="color:var(--green);border-color:var(--green);background:#1E84490A;width:110px">D5 staging<br>rootfs</div>
  </div>
</div>
<div style="margin-top:18px;display:flex;justify-content:center;gap:24px">
  <div class="note gold" style="font-size:11px">FNV-1a cache hit → skip processes 2–4</div>
  <div class="note teal" style="font-size:11px">Package Author → provides TOML to D1</div>
  <div class="note green" style="font-size:11px">Build Operator → invokes process 1 and reads D5</div>
</div>
"""))

# ══════════════════════════════════════════════════════════════════════════════
# fig6_5  Use Case Build
# ══════════════════════════════════════════════════════════════════════════════
def usecase_html(title, system_title, system_color, actor1, actor1_color, ucs1, actor2, actor2_color, ucs2, includes=None):
    def actor_svg(name, color):
        return f"""<svg width="70" height="110" viewBox="0 0 70 110">
  <circle cx="35" cy="18" r="14" fill="{color}22" stroke="{color}" stroke-width="2.5"/>
  <line x1="35" y1="32" x2="35" y2="68" stroke="{color}" stroke-width="2.5"/>
  <line x1="14" y1="50" x2="56" y2="50" stroke="{color}" stroke-width="2.5"/>
  <line x1="35" y1="68" x2="18" y2="95" stroke="{color}" stroke-width="2.5"/>
  <line x1="35" y1="68" x2="52" y2="95" stroke="{color}" stroke-width="2.5"/>
  <text x="35" y="110" text-anchor="middle" font-size="11" font-weight="bold" fill="{color}" font-family="Segoe UI,sans-serif">{name}</text>
</svg>"""
    def uc_box(txt, color):
        return f'<div style="border:2px solid {color};border-radius:40px;padding:9px 18px;font-size:11.5px;font-weight:600;color:{color};background:{color}12;text-align:center;margin:5px 0;min-width:220px">{txt}</div>'
    ucs1_html = "".join(uc_box(u, actor1_color) for u in ucs1)
    ucs2_html = "".join(uc_box(u, actor2_color) for u in ucs2)
    return page(title, f"""
<div style="display:flex;gap:0;align-items:stretch;justify-content:center">
  <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;padding:0 20px">
    {actor_svg(actor1, actor1_color)}
  </div>
  <div style="border:2.5px solid {system_color};border-radius:12px;padding:20px 30px;flex:1;max-width:860px">
    <div style="text-align:center;font-size:13px;font-weight:700;color:{system_color};margin-bottom:16px">{system_title}</div>
    <div style="display:flex;gap:30px;justify-content:space-around">
      <div style="display:flex;flex-direction:column">{ucs1_html}</div>
      <div style="display:flex;flex-direction:column">{ucs2_html}</div>
    </div>
  </div>
  <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;padding:0 20px">
    {actor_svg(actor2, actor2_color)}
  </div>
</div>""")

write("fig6_5.html", usecase_html(
    "Figure 6.5 — Use Case Diagram: Build Subsystem",
    "Build Subsystem", "#1A3A5C",
    "Package\nAuthor", "#C0392B",
    ["Write Package Metadata (TOML)","Define Build Steps","Define Installer Steps","Declare Dependencies"],
    "Build\nOperator", "#0E6655",
    ["Invoke cogman-planner","Invoke cogman-executor","Inspect Plan Cache","Verify Build Output"],
))

write("fig6_6.html", usecase_html(
    "Figure 6.6 — Use Case Diagram: Runtime Supervisor",
    "Runtime Supervisor (cogman-supervisor)", "#0E6655",
    "Runtime\nOperator", "#1E8449",
    ["List Services (cogman-ctl list)","Start Service (cogman-ctl start)","Stop Service (cogman-ctl stop)","Query Status (cogman-ctl status)"],
    "Linux\nKernel", "#5D6D7E",
    ["Reap Orphan Processes","Handle SIGCHLD (self-pipe)","Mount Virtual Filesystems","System Shutdown (SIGTERM)"],
))

# ══════════════════════════════════════════════════════════════════════════════
# fig6_7  Class Diagram – planner
# ══════════════════════════════════════════════════════════════════════════════
def cls(name, attrs, methods, color, w=230):
    attr_rows = "".join(f'<tr><td style="padding:3px 10px;font-size:10.5px;color:var(--blk);font-family:monospace">{a}</td></tr>' for a in attrs)
    meth_rows = "".join(f'<tr><td style="padding:3px 10px;font-size:10px;color:var(--gray);font-style:italic;font-family:monospace">{m}</td></tr>' for m in methods)
    sep = f'<tr><td style="border-top:1px dashed {color};padding:0"></td></tr>' if methods else ""
    return f"""<table style="border:2.5px solid {color};border-radius:8px;border-collapse:separate;border-spacing:0;min-width:{w}px;background:#fff">
  <tr><td style="background:{color}22;padding:8px 10px;font-size:12px;font-weight:700;color:{color};text-align:center;border-radius:5px 5px 0 0">{name}</td></tr>
  <tr><td style="border-top:2px solid {color};padding:0"></td></tr>
  {attr_rows}{sep}{meth_rows}
</table>"""

write("fig6_7.html", page("Figure 6.7 — Class Diagram: cogman-planner (Rust)", f"""
<div style="display:flex;flex-direction:column;gap:20px">
  <!-- row 1 -->
  <div style="display:flex;gap:16px;align-items:flex-start;justify-content:center">
    {cls("Cli",["cmd: Command"],["+run() → Result&lt;(),Error&gt;"],"#C0392B",190)}
    <div style="font-size:20px;color:var(--gray);align-self:center;padding:0 4px">→</div>
    {cls("Command",["Build { meta: PathBuf, out: PathBuf }","Install { meta: PathBuf }","Deploy  { plan: PathBuf }"],[],"#C0392B",280)}
    <div style="font-size:20px;color:var(--gray);align-self:center;padding:0 4px">→</div>
    {cls("PackageMetadata",["identity: Identity","builder:  Builder","installer: Installer","policy:   Policy","depends:  Vec&lt;String&gt;"],["+validate() → Result","+load(path) → Result"],"#1A3A5C",260)}
    <div style="font-size:20px;color:var(--gray);align-self:center;padding:0 4px">→</div>
    {cls("Identity",["name:     String","version:  String","category: String","source:   String"],[],"#1A3A5C",220)}
  </div>
  <!-- row 2 -->
  <div style="display:flex;gap:16px;align-items:flex-start;justify-content:center">
    {cls("RecursiveLoader",["visited:  HashSet&lt;String&gt;","base_dir: PathBuf"],["+load(pkg) → PackageMetadata","+load_all() → Vec&lt;PackageMetadata&gt;"],"#0E6655",280)}
    <div style="font-size:20px;color:var(--gray);align-self:center;padding:0 4px">→</div>
    {cls("DependencyGraph",["nodes: HashMap&lt;String,Node&gt;","edges: Vec&lt;(String,String)&gt;"],["+add_node(name: &amp;str)","+add_edge(a,b: &amp;str)","+topo_sort() → Vec&lt;String&gt;","+has_cycle() → bool"],"#0E6655",280)}
    <div style="font-size:20px;color:var(--gray);align-self:center;padding:0 4px">→</div>
    {cls("PlanWriter",["steps:  Vec&lt;PlanStep&gt;","strtab: Vec&lt;u8&gt;","cache:  FnvHashMap&lt;u64,PathBuf&gt;"],["+add_step(s: PlanStep)","+emit(path: &amp;Path) → Result"],"#1E8449",280)}
  </div>
  <!-- row 3 -->
  <div style="display:flex;gap:16px;align-items:flex-start;justify-content:center">
    {cls("Policy",["allow_write:   Vec&lt;PathBuf&gt;","allow_network: bool","allow_exec:    Vec&lt;String&gt;"],["+check_path(p) → bool"],"#CA6F1E",240)}
    <div style="font-size:20px;color:var(--gray);align-self:center;padding:0 4px">→</div>
    {cls("PlanStep",["op:          OpCode","fail_policy: FailPolicy","cmd_off:     u32","workdir_off: u32","env_off:     u32"],[],"#1E8449",240)}
    <div style="font-size:20px;color:var(--gray);align-self:center;padding:0 4px">→</div>
    {cls("OpCode",["OP_EXEC    = 0","OP_MKDIR   = 1","OP_COPY    = 2","OP_CHMOD   = 3","OP_SYMLINK = 4"],[],"#1E8449",200)}
  </div>
</div>"""))

write("fig6_8.html", page("Figure 6.8 — Class Diagram: cogman-supervisor (C11)", f"""
<div style="display:flex;flex-direction:column;gap:20px">
  <div style="display:flex;gap:16px;align-items:flex-start;justify-content:center">
    {cls("Supervisor [singleton]",["svc_table[64]: Service","svc_count:     int","sigchld_pipe:  int[2]","ctl_fd:        int","running:       bool"],["+init()","+run_loop()","+drain_sigchld()","+reap_children()","+shutdown()"],"#0E6655",260)}
    <div style="font-size:20px;color:var(--gray);align-self:center;padding:0 4px">→ owns 0..*</div>
    {cls("Service",["name[64]:       char","command[256]:   char","type:           SvcType","restart:        SvcRestart","state:          SvcState","pid:            pid_t","restart_count:  int","deps[8][64]:    char"],["+start(sup: *Supervisor)","+stop()","+on_exit(status: int)"],"#1A3A5C",280)}
    <div style="font-size:20px;color:var(--gray);align-self:center;padding:0 4px">→ parsed by</div>
    {cls("ServiceFileParser",["path[256]: char"],["+parse(path) → Service","+parse_all(dir) → int"],"#5D6D7E",240)}
  </div>
  <div style="display:flex;gap:16px;align-items:flex-start;justify-content:center">
    {cls("SvcType [enum]",["PROCESS = 0","ONESHOT  = 1","FORKING  = 2"],[],"#0E6655",180)}
    {cls("SvcState [enum]",["STOPPED","STARTING","RUNNING","RESTARTING","FAILED","DONE"],[],"#CA6F1E",170)}
    {cls("SvcRestart [enum]",["NEVER      = 0","ON_FAILURE = 1","ALWAYS     = 2"],[],"#1E8449",190)}
    {cls("CtlServer",["sock_fd:        int","sock_path[128]: char"],["+ctl_init(path: char*)","+ctl_accept(sup: *Supervisor)","+cmd_list/start/stop(fd)"],"#6C3483",260)}
  </div>
</div>"""))

print("Batch 1 done.")
