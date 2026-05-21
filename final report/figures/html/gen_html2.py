"""Batch 2: sequence diagrams, component, dep graphs, flowcharts, state machine, protocol figs, rootfs, boot, DWM, terminal"""
import os
DIR = os.path.dirname(os.path.abspath(__file__))

def write(name, content):
    with open(os.path.join(DIR, name), 'w') as f:
        f.write(content)
    print(f"  wrote {name}")

CSS = '<link rel="stylesheet" href="common.css">'

def page(title, body, w=1400):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">{CSS}</head>
<body style="background:#F8F9FA"><div style="padding:28px 36px;min-width:{w}px">
<h1 style="font-size:17px;font-weight:700;color:#1A3A5C;text-align:center;margin-bottom:24px">{title}</h1>
{body}
</div></body></html>"""

# ══════════════════════════════════════════════════════════════════════════════
# Sequence diagram helper
# ══════════════════════════════════════════════════════════════════════════════
def seq_diagram(lifelines, messages):
    """
    lifelines: list of (name, color_hex)
    messages:  list of (from_idx, to_idx, label, is_return=False)
               from_idx==to_idx means self-note
    """
    n = len(lifelines)
    col_w = 200
    total_w = n * col_w + 40
    msg_h = 44
    header_h = 56
    total_h = header_h + len(messages) * msg_h + 40

    # header boxes
    headers = ""
    for i, (name, color) in enumerate(lifelines):
        x = 20 + i * col_w + col_w//2
        headers += f"""<rect x="{20 + i*col_w + 10}" y="10" width="{col_w-20}" height="42"
  rx="6" fill="{color}22" stroke="{color}" stroke-width="2.5"/>
<text x="{x}" y="35" text-anchor="middle" font-size="11.5" font-weight="700"
  fill="{color}" font-family="Segoe UI,sans-serif">{name}</text>"""

    # lifeline dashes
    lifelines_svg = ""
    for i, (name, color) in enumerate(lifelines):
        x = 20 + i * col_w + col_w//2
        lifelines_svg += f'<line x1="{x}" y1="52" x2="{x}" y2="{total_h-10}" stroke="{color}" stroke-width="1.2" stroke-dasharray="6,4" opacity="0.6"/>'

    # messages
    msgs_svg = ""
    for mi, msg in enumerate(messages):
        fi, ti, label = msg[0], msg[1], msg[2]
        is_ret = msg[3] if len(msg) > 3 else False
        y = header_h + mi * msg_h + msg_h//2

        x1 = 20 + fi * col_w + col_w//2
        x2 = 20 + ti * col_w + col_w//2

        if fi == ti:
            # self note
            msgs_svg += f'<text x="{x1+12}" y="{y+4}" font-size="10" fill="#5D6D7E" font-family="Segoe UI,sans-serif" font-style="italic">{label}</text>'
            continue

        color = "#5D6D7E" if not is_ret else "#9A7D0A"
        dash = "6,3" if is_ret else "none"
        mid_x = (x1 + x2) // 2

        # line
        msgs_svg += f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{color}" stroke-width="1.8" stroke-dasharray="{dash}"/>'

        # arrowhead
        if x2 > x1:
            msgs_svg += f'<polygon points="{x2},{y} {x2-10},{y-5} {x2-10},{y+5}" fill="{color}"/>'
        else:
            msgs_svg += f'<polygon points="{x2},{y} {x2+10},{y-5} {x2+10},{y+5}" fill="{color}"/>'

        # label above line
        msgs_svg += f'<rect x="{mid_x - len(label)*3}" y="{y-18}" width="{len(label)*6+10}" height="16" fill="#F8F9FA" opacity="0.9"/>'
        msgs_svg += f'<text x="{mid_x}" y="{y-5}" text-anchor="middle" font-size="10" fill="{color}" font-family="Segoe UI,sans-serif">{label}</text>'

    svg = f"""<svg width="{total_w}" height="{total_h}" xmlns="http://www.w3.org/2000/svg"
  style="font-family:Segoe UI,sans-serif;background:#F8F9FA;border:1px solid #dee2e6;border-radius:8px">
{headers}{lifelines_svg}{msgs_svg}
</svg>"""
    return svg

write("fig6_9.html", page("Figure 6.9 — Sequence Diagram: Package Build Flow",
    seq_diagram(
        [("Operator", "#0E6655"), ("cogman-planner", "#C0392B"),
         ("MetadataLoader", "#1A3A5C"), ("DependencyGraph", "#1A3A5C"), ("PlanWriter", "#1E8449")],
        [
            (0,1,"invoke cogman-planner(meta.toml, out.bin)"),
            (1,2,"load(path='meta.toml')"),
            (2,1,"return PackageMetadata",True),
            (1,2,"load_dep('libssl')"),
            (2,1,"return PackageMetadata(libssl)",True),
            (1,3,"build_graph(all_meta[])"),
            (3,1,"return sorted_packages[]",True),
            (1,3,"topo_sort()"),
            (3,1,"return ordered_list[]",True),
            (1,4,"emit_plan(ordered_list)"),
            (4,4,"check FNV-1a cache"),
            (4,1,"return plan_path",True),
            (1,0,"exit 0 — plan written",True),
        ]
    ), w=1200))

write("fig6_10.html", page("Figure 6.10 — Sequence Diagram: Service Start Flow",
    seq_diagram(
        [("cogman-ctl", "#1E8449"), ("cogman-supervisor", "#0E6655"),
         ("SvcFile Parser", "#1A3A5C"), ("Linux Kernel", "#5D6D7E"),
         ("Service Process", "#C0392B"), ("SIGCHLD Pipe", "#CA6F1E")],
        [
            (0,1,'connect /run/cogman-supervisor.sock'),
            (0,1,'send "start heartbeat\\n"'),
            (1,2,"parse_all(/etc/cogman/services/)"),
            (2,1,"return Service{heartbeat,...}",True),
            (1,1,"check_deps(heartbeat) → OK"),
            (1,3,"fork()"),
            (3,1,"return child_pid=42",True),
            (3,4,'exec("/usr/bin/heartbeat")'),
            (1,1,"set state=STARTING, pid=42"),
            (4,5,"process runs → SIGCHLD"),
            (5,5,"write(pipe_w, 1)  async-signal-safe"),
            (5,1,"pipe_r readable",True),
            (1,1,"waitpid(42,WNOHANG) → set RUNNING"),
            (1,0,'send "OK pid=42\\n"',True),
        ]
    ), w=1400))

# ══════════════════════════════════════════════════════════════════════════════
# fig6_11  Component Diagram
# ══════════════════════════════════════════════════════════════════════════════
write("fig6_11.html", page("Figure 6.11 — Component Diagram", """
<div style="display:flex;gap:24px;align-items:stretch">

  <!-- HOST ENV -->
  <div style="border:2.5px dashed #C0392B;border-radius:12px;padding:18px 20px;min-width:280px">
    <div style="font-size:12px;font-weight:700;color:#C0392B;margin-bottom:14px;text-align:center">Host Build Environment</div>
    <div style="display:flex;flex-direction:column;gap:12px;align-items:center">
      <div style="border:2.5px solid #C0392B;border-radius:8px;padding:12px 16px;background:#C0392B0D;text-align:center;width:220px">
        <div style="font-size:12px;font-weight:700;color:#C0392B">⚙ cogman-planner</div>
        <div style="font-size:10.5px;color:#5D6D7E">Rust · ~1200 LOC</div>
      </div>
      <div style="font-size:18px;color:#9A7D0A">↓ emits</div>
      <div style="border:2.5px solid #9A7D0A;border-radius:8px;padding:10px 16px;background:#9A7D0A0D;text-align:center;width:220px">
        <div style="font-size:12px;font-weight:700;color:#9A7D0A">📄 CGM2PLAN .bin</div>
        <div style="font-size:10.5px;color:#5D6D7E">64-byte hdr + step[]</div>
      </div>
      <div style="font-size:18px;color:#0E6655">↓ reads</div>
      <div style="border:2.5px solid #0E6655;border-radius:8px;padding:12px 16px;background:#0E66550D;text-align:center;width:220px">
        <div style="font-size:12px;font-weight:700;color:#0E6655">⚙ cogman-executor</div>
        <div style="font-size:10.5px;color:#5D6D7E">C11 · ~1144 LOC</div>
      </div>
    </div>
    <div style="text-align:center;margin-top:16px;font-size:22px;color:#9A7D0A">⟶ deploy rootfs ⟶</div>
  </div>

  <!-- TARGET ROOTFS -->
  <div style="border:2.5px dashed #0E6655;border-radius:12px;padding:18px 20px;flex:1">
    <div style="font-size:12px;font-weight:700;color:#0E6655;margin-bottom:14px;text-align:center">Target Rootfs (/)</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
      <div style="border:2.5px solid #0E6655;border-radius:8px;padding:12px;background:#0E66550D">
        <div style="font-size:12px;font-weight:700;color:#0E6655">⚙ cogman-supervisor</div>
        <div style="font-size:10.5px;color:#5D6D7E">PID 1 · C11 · 1561 LOC<br>/sbin/init → symlink</div>
        <div style="margin-top:8px;font-size:10px;color:#0E6655">Provides: fork/exec services<br>Listens: /run/cogman-supervisor.sock</div>
      </div>
      <div style="border:2.5px solid #C0392B;border-radius:8px;padding:12px;background:#C0392B0D">
        <div style="font-size:12px;font-weight:700;color:#C0392B">▶ Service Processes</div>
        <div style="font-size:10.5px;color:#5D6D7E">heartbeat, hello,<br>ctl-probe, shutdown</div>
        <div style="margin-top:8px;font-size:10px;color:#C0392B">Spawned by: cogman-supervisor<br>Sends: SIGCHLD on exit</div>
      </div>
      <div style="border:2.5px solid #1E8449;border-radius:8px;padding:12px;background:#1E84490D">
        <div style="font-size:12px;font-weight:700;color:#1E8449">⚙ cogman-ctl</div>
        <div style="font-size:10.5px;color:#5D6D7E">client · C11 · 142 LOC</div>
        <div style="margin-top:8px;font-size:10px;color:#1E8449">Connects to: supervisor.sock<br>Commands: list start stop status</div>
      </div>
      <div style="border:2.5px solid #6C3483;border-radius:8px;padding:12px;background:#6C34830D">
        <div style="font-size:12px;font-weight:700;color:#6C3483">⚙ messenger broker</div>
        <div style="font-size:10.5px;color:#5D6D7E">IPC · TLV protocol · :7201</div>
        <div style="margin-top:8px;font-size:10px;color:#6C3483">Header: COG1 magic + msg_type<br>Payload: 0–N bytes</div>
      </div>
      <div style="border:2.5px solid #1A3A5C;border-radius:8px;padding:10px 12px;background:#1A3A5C0D">
        <div style="font-size:11.5px;font-weight:700;color:#1A3A5C">📁 /etc/cogman/services/</div>
        <div style="font-size:10px;color:#5D6D7E">*.service  (INI format)<br>4 verification services</div>
      </div>
      <div style="border:2.5px solid #5D6D7E;border-radius:8px;padding:10px 12px;background:#5D6D7E0D">
        <div style="font-size:11.5px;font-weight:700;color:#5D6D7E">📁 Virtual Filesystems</div>
        <div style="font-size:10px;color:#5D6D7E">/proc  /sys  /dev  /run<br>mounted by PID 1 on boot</div>
      </div>
    </div>
  </div>
</div>
"""))

# ══════════════════════════════════════════════════════════════════════════════
# fig7_1  Dependency Graph
# ══════════════════════════════════════════════════════════════════════════════
write("fig7_1.html", page("Figure 7.1 — cogman-planner: Dependency Graph Resolution", """
<svg width="1100" height="680" xmlns="http://www.w3.org/2000/svg"
  style="background:#F8F9FA;border:1px solid #dee2e6;border-radius:10px">
<defs>
  <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
    <polygon points="0 0, 8 3, 0 6" fill="#5D6D7E"/>
  </marker>
</defs>
<!-- Layer labels -->
<text x="20" y="85"  font-size="11" fill="#5D6D7E" font-style="italic" font-family="Segoe UI,sans-serif">Root package</text>
<text x="20" y="235" font-size="11" fill="#5D6D7E" font-style="italic" font-family="Segoe UI,sans-serif">Direct deps</text>
<text x="20" y="415" font-size="11" fill="#5D6D7E" font-style="italic" font-family="Segoe UI,sans-serif">Transitive deps</text>
<text x="20" y="575" font-size="11" fill="#5D6D7E" font-style="italic" font-family="Segoe UI,sans-serif">Base layer</text>

<!-- Nodes -->
<!-- busybox (root) -->
<circle cx="550" cy="70"  r="58" fill="#C0392B18" stroke="#C0392B" stroke-width="2.5"/>
<text x="550" y="66"  text-anchor="middle" font-size="12" font-weight="700" fill="#C0392B" font-family="Segoe UI,sans-serif">busybox</text>
<text x="550" y="83"  text-anchor="middle" font-size="10" fill="#C0392B" font-family="Segoe UI,sans-serif">root package</text>

<!-- direct deps -->
<circle cx="220" cy="230" r="58" fill="#0E665518" stroke="#0E6655" stroke-width="2.5"/>
<text x="220" y="226" text-anchor="middle" font-size="11.5" font-weight="700" fill="#0E6655" font-family="Segoe UI,sans-serif">cogman-sup</text>
<text x="220" y="244" text-anchor="middle" font-size="9.5" fill="#0E6655" font-family="Segoe UI,sans-serif">PID 1 supervisor</text>

<circle cx="550" cy="230" r="58" fill="#0E665518" stroke="#0E6655" stroke-width="2.5"/>
<text x="550" y="226" text-anchor="middle" font-size="11.5" font-weight="700" fill="#0E6655" font-family="Segoe UI,sans-serif">cogman-exec</text>
<text x="550" y="244" text-anchor="middle" font-size="9.5" fill="#0E6655" font-family="Segoe UI,sans-serif">plan executor</text>

<circle cx="880" cy="230" r="58" fill="#0E665518" stroke="#0E6655" stroke-width="2.5"/>
<text x="880" y="226" text-anchor="middle" font-size="11.5" font-weight="700" fill="#0E6655" font-family="Segoe UI,sans-serif">cogman-plan</text>
<text x="880" y="244" text-anchor="middle" font-size="9.5" fill="#0E6655" font-family="Segoe UI,sans-serif">planner (Rust)</text>

<!-- transitive deps -->
<circle cx="180" cy="410" r="52" fill="#1A3A5C18" stroke="#1A3A5C" stroke-width="2.5"/>
<text x="180" y="407" text-anchor="middle" font-size="11" font-weight="700" fill="#1A3A5C" font-family="Segoe UI,sans-serif">musl-libc</text>
<text x="180" y="422" text-anchor="middle" font-size="9" fill="#1A3A5C" font-family="Segoe UI,sans-serif">C std library</text>

<circle cx="420" cy="410" r="52" fill="#1A3A5C18" stroke="#1A3A5C" stroke-width="2.5"/>
<text x="420" y="407" text-anchor="middle" font-size="11" font-weight="700" fill="#1A3A5C" font-family="Segoe UI,sans-serif">linux-hdr</text>
<text x="420" y="422" text-anchor="middle" font-size="9" fill="#1A3A5C" font-family="Segoe UI,sans-serif">kernel headers</text>

<circle cx="660" cy="410" r="52" fill="#1A3A5C18" stroke="#1A3A5C" stroke-width="2.5"/>
<text x="660" y="407" text-anchor="middle" font-size="11" font-weight="700" fill="#1A3A5C" font-family="Segoe UI,sans-serif">busybox-sh</text>
<text x="660" y="422" text-anchor="middle" font-size="9" fill="#1A3A5C" font-family="Segoe UI,sans-serif">shell scripts</text>

<circle cx="900" cy="410" r="52" fill="#1A3A5C18" stroke="#1A3A5C" stroke-width="2.5"/>
<text x="900" y="407" text-anchor="middle" font-size="11" font-weight="700" fill="#1A3A5C" font-family="Segoe UI,sans-serif">gcc-runtime</text>
<text x="900" y="422" text-anchor="middle" font-size="9" fill="#1A3A5C" font-family="Segoe UI,sans-serif">C++ runtime</text>

<!-- base -->
<circle cx="550" cy="570" r="52" fill="#5D6D7E18" stroke="#5D6D7E" stroke-width="2.5"/>
<text x="550" y="567" text-anchor="middle" font-size="12" font-weight="700" fill="#5D6D7E" font-family="Segoe UI,sans-serif">kernel</text>
<text x="550" y="582" text-anchor="middle" font-size="9" fill="#5D6D7E" font-family="Segoe UI,sans-serif">base layer</text>

<!-- Edges (with arrows at destination) -->
<line x1="503" y1="116" x2="254" y2="182" stroke="#5D6D7E" stroke-width="1.5" marker-end="url(#arr)"/>
<line x1="550" y1="128" x2="550" y2="172" stroke="#5D6D7E" stroke-width="1.5" marker-end="url(#arr)"/>
<line x1="597" y1="116" x2="846" y2="182" stroke="#5D6D7E" stroke-width="1.5" marker-end="url(#arr)"/>

<line x1="190" y1="284" x2="185" y2="358" stroke="#5D6D7E" stroke-width="1.5" marker-end="url(#arr)"/>
<line x1="245" y1="278" x2="400" y2="362" stroke="#5D6D7E" stroke-width="1.5" marker-end="url(#arr)"/>
<line x1="520" y1="283" x2="232" y2="366" stroke="#5D6D7E" stroke-width="1.5" marker-end="url(#arr)"/>
<line x1="550" y1="288" x2="420" y2="358" stroke="#5D6D7E" stroke-width="1.5" marker-end="url(#arr)"/>
<line x1="580" y1="283" x2="648" y2="358" stroke="#5D6D7E" stroke-width="1.5" marker-end="url(#arr)"/>
<line x1="850" y1="278" x2="680" y2="362" stroke="#5D6D7E" stroke-width="1.5" marker-end="url(#arr)"/>
<line x1="880" y1="288" x2="895" y2="358" stroke="#5D6D7E" stroke-width="1.5" marker-end="url(#arr)"/>

<line x1="175" y1="462" x2="520" y2="520" stroke="#5D6D7E" stroke-width="1.5" marker-end="url(#arr)"/>
<line x1="415" y1="462" x2="530" y2="520" stroke="#5D6D7E" stroke-width="1.5" marker-end="url(#arr)"/>
<line x1="655" y1="462" x2="570" y2="520" stroke="#5D6D7E" stroke-width="1.5" marker-end="url(#arr)"/>
<line x1="895" y1="462" x2="580" y2="522" stroke="#5D6D7E" stroke-width="1.5" marker-end="url(#arr)"/>

<!-- FNV annotation -->
<rect x="830" y="20" width="230" height="60" rx="8" fill="#9A7D0A12" stroke="#9A7D0A" stroke-width="1.5"/>
<text x="945" y="44" text-anchor="middle" font-size="11" font-weight="700" fill="#9A7D0A" font-family="Segoe UI,sans-serif">FNV-1a hash per metadata</text>
<text x="945" y="60" text-anchor="middle" font-size="10" fill="#9A7D0A" font-family="Segoe UI,sans-serif">file → plan cache key</text>
</svg>
"""))

# ══════════════════════════════════════════════════════════════════════════════
# fig7_2  Topo Sort
# ══════════════════════════════════════════════════════════════════════════════
write("fig7_2.html", page("Figure 7.2 — Dependency Topological Sort  (Kahn's Algorithm)", """
<div style="display:flex;gap:30px;align-items:flex-start;justify-content:center">

<!-- LEFT: input DAG -->
<div style="border:2px dashed #1A3A5C;border-radius:12px;padding:20px;min-width:400px">
<div style="font-size:13px;font-weight:700;color:#1A3A5C;text-align:center;margin-bottom:14px">Input DAG  (package dependencies)</div>
<svg width="360" height="440" xmlns="http://www.w3.org/2000/svg">
<defs>
  <marker id="a2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
    <polygon points="0 0,8 3,0 6" fill="#5D6D7E"/>
  </marker>
</defs>
<!-- nodes -->
<circle cx="80"  cy="60"  r="48" fill="#5D6D7E18" stroke="#5D6D7E" stroke-width="2.5"/>
<text x="80"  y="56"  text-anchor="middle" font-size="11" font-weight="700" fill="#5D6D7E" font-family="Segoe UI,sans-serif">kernel</text>
<text x="80"  y="71"  text-anchor="middle" font-size="9.5" fill="#5D6D7E" font-family="Segoe UI,sans-serif">in=0</text>

<circle cx="200" cy="60"  r="48" fill="#5D6D7E18" stroke="#5D6D7E" stroke-width="2.5"/>
<text x="200" y="56"  text-anchor="middle" font-size="11" font-weight="700" fill="#5D6D7E" font-family="Segoe UI,sans-serif">linux-hdr</text>
<text x="200" y="71"  text-anchor="middle" font-size="9.5" fill="#5D6D7E" font-family="Segoe UI,sans-serif">in=0</text>

<circle cx="310" cy="60"  r="40" fill="#5D6D7E18" stroke="#5D6D7E" stroke-width="2.5"/>
<text x="310" y="56"  text-anchor="middle" font-size="10.5" font-weight="700" fill="#5D6D7E" font-family="Segoe UI,sans-serif">gcc-rt</text>
<text x="310" y="71"  text-anchor="middle" font-size="9" fill="#5D6D7E" font-family="Segoe UI,sans-serif">in=0</text>

<circle cx="130" cy="220" r="50" fill="#1A3A5C18" stroke="#1A3A5C" stroke-width="2.5"/>
<text x="130" y="216" text-anchor="middle" font-size="11" font-weight="700" fill="#1A3A5C" font-family="Segoe UI,sans-serif">musl-libc</text>
<text x="130" y="231" text-anchor="middle" font-size="9.5" fill="#1A3A5C" font-family="Segoe UI,sans-serif">in=2</text>

<circle cx="270" cy="220" r="48" fill="#C0392B18" stroke="#C0392B" stroke-width="2.5"/>
<text x="270" y="216" text-anchor="middle" font-size="11" font-weight="700" fill="#C0392B" font-family="Segoe UI,sans-serif">busybox</text>
<text x="270" y="231" text-anchor="middle" font-size="9.5" fill="#C0392B" font-family="Segoe UI,sans-serif">in=2</text>

<circle cx="180" cy="380" r="54" fill="#0E665518" stroke="#0E6655" stroke-width="2.5"/>
<text x="180" y="376" text-anchor="middle" font-size="11" font-weight="700" fill="#0E6655" font-family="Segoe UI,sans-serif">cogman-sup</text>
<text x="180" y="391" text-anchor="middle" font-size="9.5" fill="#0E6655" font-family="Segoe UI,sans-serif">in=2</text>

<!-- edges -->
<line x1="100" y1="104" x2="120" y2="168" stroke="#5D6D7E" stroke-width="1.5" marker-end="url(#a2)"/>
<line x1="180" y1="102" x2="155" y2="170" stroke="#5D6D7E" stroke-width="1.5" marker-end="url(#a2)"/>
<line x1="210" y1="105" x2="252" y2="172" stroke="#5D6D7E" stroke-width="1.5" marker-end="url(#a2)"/>
<line x1="290" y1="96"  x2="285" y2="172" stroke="#5D6D7E" stroke-width="1.5" marker-end="url(#a2)"/>
<line x1="140" y1="268" x2="162" y2="326" stroke="#5D6D7E" stroke-width="1.5" marker-end="url(#a2)"/>
<line x1="250" y1="264" x2="202" y2="326" stroke="#5D6D7E" stroke-width="1.5" marker-end="url(#a2)"/>
</svg>
</div>

<!-- ARROW -->
<div style="font-size:36px;color:#1C2833;align-self:center;padding:20px;font-weight:300">⟹</div>
<div style="align-self:center;font-size:12px;color:#5D6D7E;text-align:center">Kahn's<br>topo-sort</div>
<div style="font-size:36px;color:#1C2833;align-self:center;padding:20px;font-weight:300">⟹</div>

<!-- RIGHT: sorted output -->
<div style="border:2px dashed #1E8449;border-radius:12px;padding:20px;min-width:380px">
<div style="font-size:13px;font-weight:700;color:#1E8449;text-align:center;margin-bottom:14px">Build Order  (topological sort)</div>
<div style="display:flex;flex-direction:column;gap:8px">
  <div style="border:2px solid #5D6D7E;border-radius:8px;padding:10px 14px;background:#5D6D7E0D;display:flex;align-items:center;gap:12px">
    <span style="font-size:14px;font-weight:700;color:#5D6D7E;min-width:24px">1.</span>
    <div><div style="font-size:12px;font-weight:700;color:#5D6D7E">kernel</div><div style="font-size:10px;color:#8a9aaa">in-degree = 0 → enqueue first</div></div>
  </div>
  <div style="border:2px solid #5D6D7E;border-radius:8px;padding:10px 14px;background:#5D6D7E0D;display:flex;align-items:center;gap:12px">
    <span style="font-size:14px;font-weight:700;color:#5D6D7E;min-width:24px">2.</span>
    <div><div style="font-size:12px;font-weight:700;color:#5D6D7E">linux-hdr</div><div style="font-size:10px;color:#8a9aaa">in-degree = 0 → enqueue first</div></div>
  </div>
  <div style="border:2px solid #5D6D7E;border-radius:8px;padding:10px 14px;background:#5D6D7E0D;display:flex;align-items:center;gap:12px">
    <span style="font-size:14px;font-weight:700;color:#5D6D7E;min-width:24px">3.</span>
    <div><div style="font-size:12px;font-weight:700;color:#5D6D7E">gcc-rt</div><div style="font-size:10px;color:#8a9aaa">in-degree = 0 → enqueue first</div></div>
  </div>
  <div style="border:2px solid #1A3A5C;border-radius:8px;padding:10px 14px;background:#1A3A5C0D;display:flex;align-items:center;gap:12px">
    <span style="font-size:14px;font-weight:700;color:#1A3A5C;min-width:24px">4.</span>
    <div><div style="font-size:12px;font-weight:700;color:#1A3A5C">musl-libc</div><div style="font-size:10px;color:#8a9aaa">in-degree 2→0 after kernel+linux-hdr processed</div></div>
  </div>
  <div style="border:2px solid #C0392B;border-radius:8px;padding:10px 14px;background:#C0392B0D;display:flex;align-items:center;gap:12px">
    <span style="font-size:14px;font-weight:700;color:#C0392B;min-width:24px">5.</span>
    <div><div style="font-size:12px;font-weight:700;color:#C0392B">busybox</div><div style="font-size:10px;color:#8a9aaa">in-degree 2→0 after linux-hdr+gcc-rt processed</div></div>
  </div>
  <div style="border:2px solid #0E6655;border-radius:8px;padding:10px 14px;background:#0E66550D;display:flex;align-items:center;gap:12px">
    <span style="font-size:14px;font-weight:700;color:#0E6655;min-width:24px">6.</span>
    <div><div style="font-size:12px;font-weight:700;color:#0E6655">cogman-supervisor</div><div style="font-size:10px;color:#8a9aaa">in-degree 2→0 after musl-libc+busybox processed</div></div>
  </div>
</div>
</div>
</div>
"""))

# ══════════════════════════════════════════════════════════════════════════════
# fig7_3  Executor Loop Flowchart (SVG)
# ══════════════════════════════════════════════════════════════════════════════
write("fig7_3.html", page("Figure 7.3 — cogman-executor: Step Execution Loop", """
<div style="display:flex;justify-content:center">
<svg width="780" height="1000" xmlns="http://www.w3.org/2000/svg" style="background:#F8F9FA;border:1px solid #dee2e6;border-radius:10px">
<defs>
  <marker id="a" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#1C2833"/></marker>
  <marker id="ag" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#1E8449"/></marker>
  <marker id="ar" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#922B21"/></marker>
  <marker id="ao" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#9A7D0A"/></marker>
</defs>

<!-- helpers: cx=390 -->
<!-- START -->
<circle cx="390" cy="38" r="18" fill="#1C2833"/>
<!-- open -->
<rect x="255" y="74" width="270" height="44" rx="8" fill="#0E665518" stroke="#0E6655" stroke-width="2.5"/>
<text x="390" y="101" text-anchor="middle" font-size="12" fill="#0E6655" font-weight="700" font-family="Segoe UI,sans-serif">open(plan_path, O_RDONLY)</text>
<!-- mmap -->
<rect x="245" y="138" width="290" height="44" rx="8" fill="#1A3A5C18" stroke="#1A3A5C" stroke-width="2.5"/>
<text x="390" y="165" text-anchor="middle" font-size="12" fill="#1A3A5C" font-weight="700" font-family="Segoe UI,sans-serif">mmap(file, PROT_READ)</text>
<!-- validate header diamond -->
<polygon points="390,212 520,248 390,284 260,248" fill="#1A3A5C18" stroke="#1A3A5C" stroke-width="2.5"/>
<text x="390" y="244" text-anchor="middle" font-size="11" fill="#1A3A5C" font-weight="700" font-family="Segoe UI,sans-serif">magic=CGM2PLAN?</text>
<text x="390" y="260" text-anchor="middle" font-size="10" fill="#1A3A5C" font-family="Segoe UI,sans-serif">version==1?</text>
<!-- i=0 -->
<rect x="300" y="304" width="180" height="40" rx="8" fill="#5D6D7E18" stroke="#5D6D7E" stroke-width="2"/>
<text x="390" y="329" text-anchor="middle" font-size="12" fill="#5D6D7E" font-weight="700" font-family="Segoe UI,sans-serif">i = 0</text>
<!-- loop check diamond -->
<polygon points="390,368 530,404 390,440 250,404" fill="#9A7D0A18" stroke="#9A7D0A" stroke-width="2.5"/>
<text x="390" y="400" text-anchor="middle" font-size="11" fill="#9A7D0A" font-weight="700" font-family="Segoe UI,sans-serif">i &lt; step_count ?</text>
<text x="390" y="415" text-anchor="middle" font-size="9.5" fill="#9A7D0A" font-family="Segoe UI,sans-serif">(loop condition)</text>
<!-- load step -->
<rect x="255" y="460" width="270" height="40" rx="8" fill="#0E665518" stroke="#0E6655" stroke-width="2.5"/>
<text x="390" y="485" text-anchor="middle" font-size="12" fill="#0E6655" font-weight="700" font-family="Segoe UI,sans-serif">load steps[i] via mmap offset</text>
<!-- dispatch diamond -->
<polygon points="390,524 520,556 390,588 260,556" fill="#1A3A5C18" stroke="#1A3A5C" stroke-width="2.5"/>
<text x="390" y="552" text-anchor="middle" font-size="11" fill="#1A3A5C" font-weight="700" font-family="Segoe UI,sans-serif">steps[i].op ?</text>

<!-- three dispatch boxes -->
<rect x="40"  y="624" width="180" height="50" rx="8" fill="#C0392B18" stroke="#C0392B" stroke-width="2.5"/>
<text x="130" y="646" text-anchor="middle" font-size="11" fill="#C0392B" font-weight="700" font-family="Segoe UI,sans-serif">OP_EXEC</text>
<text x="130" y="663" text-anchor="middle" font-size="9.5" fill="#C0392B" font-family="Segoe UI,sans-serif">fork+exec /bin/sh -c</text>

<rect x="300" y="624" width="180" height="50" rx="8" fill="#0E665518" stroke="#0E6655" stroke-width="2.5"/>
<text x="390" y="646" text-anchor="middle" font-size="11" fill="#0E6655" font-weight="700" font-family="Segoe UI,sans-serif">OP_MKDIR</text>
<text x="390" y="663" text-anchor="middle" font-size="9.5" fill="#0E6655" font-family="Segoe UI,sans-serif">recursive mkdir_p()</text>

<rect x="560" y="624" width="180" height="50" rx="8" fill="#1A3A5C18" stroke="#1A3A5C" stroke-width="2.5"/>
<text x="650" y="646" text-anchor="middle" font-size="11" fill="#1A3A5C" font-weight="700" font-family="Segoe UI,sans-serif">OP_COPY</text>
<text x="650" y="663" text-anchor="middle" font-size="9.5" fill="#1A3A5C" font-family="Segoe UI,sans-serif">copy_recursive()+guard</text>

<!-- fail policy diamond -->
<polygon points="390,724 530,756 390,788 250,756" fill="#922B2118" stroke="#922B21" stroke-width="2.5"/>
<text x="390" y="752" text-anchor="middle" font-size="11" fill="#922B21" font-weight="700" font-family="Segoe UI,sans-serif">ABORT &amp;&amp; rc ≠ 0 ?</text>
<text x="390" y="768" text-anchor="middle" font-size="9.5" fill="#922B21" font-family="Segoe UI,sans-serif">fail_policy check</text>

<!-- i++ -->
<rect x="300" y="816" width="180" height="40" rx="8" fill="#5D6D7E18" stroke="#5D6D7E" stroke-width="2"/>
<text x="390" y="841" text-anchor="middle" font-size="12" fill="#5D6D7E" font-weight="700" font-family="Segoe UI,sans-serif">i = i + 1</text>

<!-- exit error -->
<rect x="595" y="730" width="160" height="50" rx="8" fill="#922B2118" stroke="#922B21" stroke-width="2.5"/>
<text x="675" y="752" text-anchor="middle" font-size="11" fill="#922B21" font-weight="700" font-family="Segoe UI,sans-serif">munmap()</text>
<text x="675" y="768" text-anchor="middle" font-size="11" fill="#922B21" font-weight="700" font-family="Segoe UI,sans-serif">exit(2) ABORT</text>

<!-- exit ok -->
<rect x="595" y="388" width="160" height="44" rx="8" fill="#1E844918" stroke="#1E8449" stroke-width="2.5"/>
<text x="675" y="406" text-anchor="middle" font-size="11" fill="#1E8449" font-weight="700" font-family="Segoe UI,sans-serif">munmap()</text>
<text x="675" y="422" text-anchor="middle" font-size="11" fill="#1E8449" font-weight="700" font-family="Segoe UI,sans-serif">exit(0)  ✓</text>

<!-- END circles -->
<circle cx="675" cy="478" r="16" fill="#1E8449" opacity="0.7"/>
<circle cx="675" cy="478" r="22" fill="none" stroke="#1E8449" stroke-width="2"/>

<circle cx="675" cy="820" r="16" fill="#922B21" opacity="0.7"/>
<circle cx="675" cy="820" r="22" fill="none" stroke="#922B21" stroke-width="2"/>

<!-- ARROWS -->
<line x1="390" y1="56" x2="390" y2="74" stroke="#1C2833" stroke-width="2" marker-end="url(#a)"/>
<line x1="390" y1="118" x2="390" y2="138" stroke="#1C2833" stroke-width="2" marker-end="url(#a)"/>
<line x1="390" y1="182" x2="390" y2="212" stroke="#1C2833" stroke-width="2" marker-end="url(#a)"/>
<line x1="390" y1="284" x2="390" y2="304" stroke="#1C2833" stroke-width="2" marker-end="url(#a)"/>
<line x1="390" y1="344" x2="390" y2="368" stroke="#1C2833" stroke-width="2" marker-end="url(#a)"/>
<line x1="390" y1="440" x2="390" y2="460" stroke="#1C2833" stroke-width="2" marker-end="url(#a)"/>
<line x1="390" y1="500" x2="390" y2="524" stroke="#1C2833" stroke-width="2" marker-end="url(#a)"/>

<!-- dispatch fan -->
<line x1="390" y1="588" x2="130" y2="624" stroke="#1C2833" stroke-width="1.8" marker-end="url(#a)"/>
<line x1="390" y1="588" x2="390" y2="624" stroke="#1C2833" stroke-width="1.8" marker-end="url(#a)"/>
<line x1="390" y1="588" x2="650" y2="624" stroke="#1C2833" stroke-width="1.8" marker-end="url(#a)"/>
<text x="140" y="618" font-size="9.5" fill="#1A3A5C" font-family="Segoe UI,sans-serif">OP_EXEC</text>
<text x="360" y="618" font-size="9.5" fill="#1A3A5C" font-family="Segoe UI,sans-serif">OP_MKDIR</text>
<text x="615" y="618" font-size="9.5" fill="#1A3A5C" font-family="Segoe UI,sans-serif">OP_COPY</text>

<!-- converge to fail check -->
<line x1="130" y1="674" x2="260" y2="756" stroke="#5D6D7E" stroke-width="1.5" marker-end="url(#a)"/>
<line x1="390" y1="674" x2="390" y2="724" stroke="#5D6D7E" stroke-width="1.5" marker-end="url(#a)"/>
<line x1="650" y1="674" x2="520" y2="756" stroke="#5D6D7E" stroke-width="1.5" marker-end="url(#a)"/>

<line x1="390" y1="788" x2="390" y2="816" stroke="#1C2833" stroke-width="2" marker-end="url(#a)"/>
<!-- NO label -->
<text x="396" y="810" font-size="10" fill="#1E8449" font-family="Segoe UI,sans-serif">NO</text>

<!-- YES → abort -->
<line x1="530" y1="756" x2="595" y2="756" stroke="#922B21" stroke-width="2" marker-end="url(#ar)"/>
<text x="540" y="748" font-size="10" fill="#922B21" font-family="Segoe UI,sans-serif">YES</text>
<line x1="675" y1="780" x2="675" y2="798" stroke="#922B21" stroke-width="1.5" marker-end="url(#ar)"/>

<!-- loop-back: i++ → loop check -->
<path d="M390,856 L390,920 L180,920 L180,404" fill="none" stroke="#9A7D0A" stroke-width="2" stroke-dasharray="6,3" marker-end="url(#ao)"/>
<text x="150" y="893" font-size="10" fill="#9A7D0A" font-family="Segoe UI,sans-serif" font-style="italic">loop back</text>

<!-- i≥count → done -->
<line x1="530" y1="404" x2="595" y2="404" stroke="#1E8449" stroke-width="2" marker-end="url(#ag)"/>
<text x="536" y="396" font-size="9.5" fill="#1E8449" font-family="Segoe UI,sans-serif">NO (done)</text>
<line x1="675" y1="432" x2="675" y2="456" stroke="#1E8449" stroke-width="1.5" marker-end="url(#ag)"/>

<!-- invalid → exit -->
<text x="530" y="244" font-size="10" fill="#922B21" font-family="Segoe UI,sans-serif">NO → exit(2)</text>
</svg>
</div>
""", w=900))

print("Batch 2 part A done.")
