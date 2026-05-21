"""Batch 3: fig7_4 through fig8_1 + extras"""
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
<h1 style="font-size:17px;font-weight:700;color:#1A3A5C;text-align:center;margin-bottom:22px">{title}</h1>
{body}
</div></body></html>"""

# ══════════════════════════════════════════════════════════════════════════════
# fig7_4  Path Traversal Guard
# ══════════════════════════════════════════════════════════════════════════════
write("fig7_4.html", page("Figure 7.4 — Path Traversal Guard Logic  (copy_recursive)", """
<div style="display:flex;gap:30px;align-items:flex-start;justify-content:center">

<!-- FLOWCHART SVG -->
<svg width="520" height="780" xmlns="http://www.w3.org/2000/svg" style="background:#F8F9FA;border:1px solid #dee2e6;border-radius:10px;flex-shrink:0">
<defs>
  <marker id="a" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#1C2833"/></marker>
  <marker id="ar" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#922B21"/></marker>
  <marker id="ag" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#1E8449"/></marker>
  <marker id="ao" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#9A7D0A"/></marker>
</defs>
<!-- start -->
<circle cx="260" cy="30" r="18" fill="#1C2833"/>
<!-- copy_recursive call -->
<rect x="100" y="62" width="320" height="44" rx="8" fill="#0E665518" stroke="#0E6655" stroke-width="2.5"/>
<text x="260" y="89" text-anchor="middle" font-size="12" fill="#0E6655" font-weight="700" font-family="Segoe UI,sans-serif">copy_recursive(src, dst)</text>
<!-- tokenize -->
<rect x="85" y="126" width="350" height="44" rx="8" fill="#1A3A5C18" stroke="#1A3A5C" stroke-width="2.5"/>
<text x="260" y="148" text-anchor="middle" font-size="12" fill="#1A3A5C" font-weight="700" font-family="Segoe UI,sans-serif">tokenize(dst) → components[]</text>
<text x="260" y="162" text-anchor="middle" font-size="10" fill="#1A3A5C" font-family="Segoe UI,sans-serif">split on '/' separator</text>
<!-- loop: more components? -->
<polygon points="260,200 390,232 260,264 130,232" fill="#9A7D0A18" stroke="#9A7D0A" stroke-width="2.5"/>
<text x="260" y="228" text-anchor="middle" font-size="11" fill="#9A7D0A" font-weight="700" font-family="Segoe UI,sans-serif">more components?</text>
<text x="260" y="244" text-anchor="middle" font-size="9.5" fill="#9A7D0A" font-family="Segoe UI,sans-serif">for each component</text>
<!-- ".." check -->
<polygon points="260,288 390,320 260,352 130,320" fill="#922B2118" stroke="#922B21" stroke-width="2.5"/>
<text x="260" y="316" text-anchor="middle" font-size="11" fill="#922B21" font-weight="700" font-family="Segoe UI,sans-serif">component == ".." ?</text>
<text x="260" y="331" text-anchor="middle" font-size="9.5" fill="#922B21" font-family="Segoe UI,sans-serif">bare traversal check</text>
<!-- null byte check -->
<polygon points="260,372 390,404 260,436 130,404" fill="#922B2118" stroke="#922B21" stroke-width="2.5"/>
<text x="260" y="400" text-anchor="middle" font-size="11" fill="#922B21" font-weight="700" font-family="Segoe UI,sans-serif">contains '\0' byte?</text>
<text x="260" y="415" text-anchor="middle" font-size="9.5" fill="#922B21" font-family="Segoe UI,sans-serif">null-byte injection</text>
<!-- component ok -->
<rect x="130" y="456" width="260" height="40" rx="8" fill="#1E844918" stroke="#1E8449" stroke-width="2.5"/>
<text x="260" y="481" text-anchor="middle" font-size="12" fill="#1E8449" font-weight="700" font-family="Segoe UI,sans-serif">component is clean → continue</text>
<!-- proceed copy -->
<rect x="115" y="640" width="290" height="44" rx="8" fill="#1E844918" stroke="#1E8449" stroke-width="2.5"/>
<text x="260" y="662" text-anchor="middle" font-size="12" fill="#1E8449" font-weight="700" font-family="Segoe UI,sans-serif">all components OK</text>
<text x="260" y="677" text-anchor="middle" font-size="11" fill="#1E8449" font-family="Segoe UI,sans-serif">open / sendfile copy → proceed</text>
<!-- end ok -->
<circle cx="260" cy="740" r="14" fill="#1E8449"/>
<circle cx="260" cy="740" r="20" fill="none" stroke="#1E8449" stroke-width="2"/>
<!-- error boxes -->
<rect x="20" y="296" width="80" height="48" rx="6" fill="#922B2118" stroke="#922B21" stroke-width="2.5"/>
<text x="60" y="316" text-anchor="middle" font-size="10" fill="#922B21" font-weight="700" font-family="Segoe UI,sans-serif">ERR_</text>
<text x="60" y="330" text-anchor="middle" font-size="10" fill="#922B21" font-weight="700" font-family="Segoe UI,sans-serif">TRAVERSAL</text>
<text x="60" y="344" text-anchor="middle" font-size="9"   fill="#922B21" font-family="Segoe UI,sans-serif">exit(2)</text>

<rect x="20" y="380" width="80" height="48" rx="6" fill="#922B2118" stroke="#922B21" stroke-width="2.5"/>
<text x="60" y="400" text-anchor="middle" font-size="10" fill="#922B21" font-weight="700" font-family="Segoe UI,sans-serif">ERR_</text>
<text x="60" y="414" text-anchor="middle" font-size="10" fill="#922B21" font-weight="700" font-family="Segoe UI,sans-serif">BADPATH</text>
<text x="60" y="428" text-anchor="middle" font-size="9"   fill="#922B21" font-family="Segoe UI,sans-serif">exit(2)</text>

<!-- ARROWS spine -->
<line x1="260" y1="48" x2="260" y2="62" stroke="#1C2833" stroke-width="2" marker-end="url(#a)"/>
<line x1="260" y1="106" x2="260" y2="126" stroke="#1C2833" stroke-width="2" marker-end="url(#a)"/>
<line x1="260" y1="170" x2="260" y2="200" stroke="#1C2833" stroke-width="2" marker-end="url(#a)"/>
<line x1="260" y1="264" x2="260" y2="288" stroke="#1C2833" stroke-width="2" marker-end="url(#a)"/>
<line x1="260" y1="352" x2="260" y2="372" stroke="#1C2833" stroke-width="2" marker-end="url(#a)"/>
<line x1="260" y1="436" x2="260" y2="456" stroke="#1C2833" stroke-width="2" marker-end="url(#a)"/>
<line x1="260" y1="496" x2="260" y2="640" stroke="#1C2833" stroke-width="1.5" stroke-dasharray="5,3"/>
<!-- loop back from ok to loop -->
<path d="M260,640 L430,640 L430,232" fill="none" stroke="#9A7D0A" stroke-width="1.8" stroke-dasharray="6,3" marker-end="url(#ao)"/>
<text x="436" y="440" font-size="10" fill="#9A7D0A" font-family="Segoe UI,sans-serif" font-style="italic">next component</text>
<line x1="260" y1="684" x2="260" y2="720" stroke="#1E8449" stroke-width="2" marker-end="url(#ag)"/>
<!-- NO done from loop -->
<line x1="390" y1="232" x2="470" y2="232" stroke="#1E8449" stroke-width="2"/>
<line x1="470" y1="232" x2="470" y2="655" stroke="#1E8449" stroke-width="2"/>
<line x1="470" y1="655" x2="405" y2="655" stroke="#1E8449" stroke-width="2" marker-end="url(#ag)"/>
<text x="474" y="228" font-size="10" fill="#1E8449" font-family="Segoe UI,sans-serif">NO (done)</text>
<!-- YES ".." -->
<line x1="130" y1="320" x2="100" y2="320" stroke="#922B21" stroke-width="2" marker-end="url(#ar)"/>
<text x="105" y="312" font-size="9.5" fill="#922B21" font-family="Segoe UI,sans-serif">YES</text>
<!-- YES null -->
<line x1="130" y1="404" x2="100" y2="404" stroke="#922B21" stroke-width="2" marker-end="url(#ar)"/>
<text x="105" y="396" font-size="9.5" fill="#922B21" font-family="Segoe UI,sans-serif">YES</text>
<!-- NO ".." -->
<text x="265" y="368" font-size="10" fill="#1E8449" font-family="Segoe UI,sans-serif">NO</text>
<text x="265" y="452" font-size="10" fill="#1E8449" font-family="Segoe UI,sans-serif">NO</text>
</svg>

<!-- RIGHT: examples table -->
<div style="flex:1">
  <div style="font-size:13px;font-weight:700;color:#1A3A5C;margin-bottom:14px">Example paths and outcomes</div>
  <table style="border-collapse:collapse;width:100%;font-size:12px;font-family:monospace">
    <tr style="background:#1A3A5C15">
      <th style="padding:9px 12px;text-align:left;color:#1A3A5C;font-size:11px;border-bottom:2px solid #1A3A5C">Path</th>
      <th style="padding:9px 12px;text-align:left;color:#1A3A5C;font-size:11px;border-bottom:2px solid #1A3A5C">Result</th>
      <th style="padding:9px 12px;text-align:left;color:#1A3A5C;font-size:11px;border-bottom:2px solid #1A3A5C">Reason</th>
    </tr>
    <tr><td style="padding:9px 12px;color:#922B21">../etc/passwd</td><td style="padding:9px 12px;color:#922B21;font-weight:700">BLOCKED</td><td style="padding:9px 12px;color:#5D6D7E;font-size:11px">bare ".." component</td></tr>
    <tr style="background:#F0F0F0"><td style="padding:9px 12px;color:#1E8449">/tmp/staging/foo</td><td style="padding:9px 12px;color:#1E8449;font-weight:700">ALLOWED</td><td style="padding:9px 12px;color:#5D6D7E;font-size:11px">clean path, no ".."</td></tr>
    <tr><td style="padding:9px 12px;color:#922B21">/tmp/build/../shadow</td><td style="padding:9px 12px;color:#922B21;font-weight:700">BLOCKED</td><td style="padding:9px 12px;color:#5D6D7E;font-size:11px">".." mid-path traversal</td></tr>
    <tr style="background:#F0F0F0"><td style="padding:9px 12px;color:#1E8449">/tmp/staging/lib/foo.so</td><td style="padding:9px 12px;color:#1E8449;font-weight:700">ALLOWED</td><td style="padding:9px 12px;color:#5D6D7E;font-size:11px">nested path, no traversal</td></tr>
    <tr><td style="padding:9px 12px;color:#922B21">file&#92;x00name</td><td style="padding:9px 12px;color:#922B21;font-weight:700">BLOCKED</td><td style="padding:9px 12px;color:#5D6D7E;font-size:11px">embedded null byte</td></tr>
    <tr style="background:#F0F0F0"><td style="padding:9px 12px;color:#1E8449">/usr/bin/cogman-ctl</td><td style="padding:9px 12px;color:#1E8449;font-weight:700">ALLOWED</td><td style="padding:9px 12px;color:#5D6D7E;font-size:11px">standard install path</td></tr>
  </table>
  <div style="margin-top:20px;border:1.5px solid #CA6F1E;border-radius:8px;padding:12px 16px;background:#CA6F1E0D">
    <div style="font-size:12px;font-weight:700;color:#CA6F1E;margin-bottom:6px">Security invariant</div>
    <div style="font-size:11.5px;color:#5D6D7E;line-height:1.6">The guard iterates every path component <em>before</em> any filesystem call. It does not rely on <code>realpath()</code> or <code>chroot()</code> — it rejects any path containing a bare <code>..</code> token unconditionally, regardless of whether the resolved path would actually escape the staging root.</div>
  </div>
</div>
</div>
""", w=1100))

# ══════════════════════════════════════════════════════════════════════════════
# fig7_5  SIGCHLD Self-Pipe
# ══════════════════════════════════════════════════════════════════════════════
write("fig7_5.html", page("Figure 7.5 — cogman-supervisor: SIGCHLD Self-Pipe Pattern", """
<div style="display:flex;flex-direction:column;gap:0">

<!-- Swim lane: Kernel -->
<div style="border:2px solid #5D6D7E;border-radius:10px 10px 0 0;background:#5D6D7E0A;padding:14px 20px;border-bottom:none">
  <div style="font-size:11.5px;font-weight:700;color:#5D6D7E;margin-bottom:10px">Linux Kernel  /  Signal Delivery</div>
  <div style="display:flex;align-items:center;gap:16px">
    <div style="border:2px solid #5D6D7E;border-radius:8px;padding:10px 16px;background:#5D6D7E15;font-size:12px;font-weight:700;color:#5D6D7E">child process exits</div>
    <div style="font-size:22px;color:#5D6D7E">→</div>
    <div style="font-size:12px;color:#5D6D7E">kernel delivers SIGCHLD to PID 1</div>
    <div style="font-size:22px;color:#5D6D7E">→</div>
    <div style="font-size:12px;color:#5D6D7E">registered handler fires</div>
  </div>
</div>

<!-- Swim lane: Handler -->
<div style="border:2px solid #CA6F1E;border-left:2px solid #CA6F1E;border-right:2px solid #CA6F1E;background:#CA6F1E0A;padding:14px 20px;border-bottom:none">
  <div style="font-size:11.5px;font-weight:700;color:#CA6F1E;margin-bottom:10px">SIGCHLD Handler  (async · only async-signal-safe functions allowed)</div>
  <div style="display:flex;align-items:center;gap:16px">
    <div style="border:2px solid #CA6F1E;border-radius:8px;padding:10px 16px;background:#CA6F1E15;font-size:11.5px;font-weight:700;color:#CA6F1E">sigaction(SIGCHLD, handler, SA_RESTART)</div>
    <div style="font-size:22px;color:#CA6F1E">→</div>
    <div style="border:2px solid #CA6F1E;border-radius:8px;padding:10px 16px;background:#CA6F1E15;font-size:11.5px;font-weight:700;color:#CA6F1E">write(pipe_w, "\x01", 1)<br><small style="font-weight:400;font-size:10px">async-signal-safe ✓</small></div>
    <div style="font-size:22px;color:#CA6F1E">→</div>
    <div style="border:1.5px dashed #CA6F1E;border-radius:8px;padding:10px 16px;background:#CA6F1E0D;font-size:11.5px;color:#CA6F1E">pipe [ pipe_r ←——— pipe_w ]</div>
  </div>
</div>

<!-- Swim lane: Main Loop -->
<div style="border:2px solid #0E6655;border-radius:0 0 10px 10px;background:#0E66550A;padding:14px 20px">
  <div style="font-size:11.5px;font-weight:700;color:#0E6655;margin-bottom:10px">Main Loop  (select() · 100 ms timeout)</div>
  <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap">
    <div style="border:2px solid #0E6655;border-radius:8px;padding:10px 16px;background:#0E665515;font-size:11.5px;font-weight:700;color:#0E6655">select(pipe_r, ctl_fd,<br>timeout=100ms)</div>
    <div style="font-size:22px;color:#0E6655">→ pipe_r readable →</div>
    <div style="border:2px solid #0E6655;border-radius:8px;padding:10px 16px;background:#0E665515;font-size:11.5px;font-weight:700;color:#0E6655">read(pipe_r, buf, 1)<br><small style="font-weight:400;font-size:10px">drain byte</small></div>
    <div style="font-size:22px;color:#0E6655">→</div>
    <div style="border:2px solid #0E6655;border-radius:8px;padding:10px 16px;background:#0E665515;font-size:11.5px;font-weight:700;color:#0E6655">waitpid(-1, WNOHANG)<br><small style="font-weight:400;font-size:10px">reap all dead children</small></div>
    <div style="font-size:22px;color:#0E6655">→</div>
    <div style="border:2px solid #1E8449;border-radius:8px;padding:10px 16px;background:#1E844915;font-size:11.5px;font-weight:700;color:#1E8449">update service<br>state table</div>
  </div>
</div>

<div style="margin-top:16px;border:1.5px solid #9A7D0A;border-radius:8px;padding:12px 18px;background:#9A7D0A0D;font-size:11.5px;color:#5D6D7E;line-height:1.7">
  <strong style="color:#9A7D0A">Key invariant:</strong>
  <code style="color:#1A3A5C">write()</code> is async-signal-safe (POSIX).
  <code style="color:#C0392B">waitpid()</code> is <em>not</em> called from the signal handler — avoids reentrancy and interrupted-syscall issues.
  <code style="color:#0E6655">select()</code> wakes immediately when <code>pipe_r</code> becomes readable, so child reaping happens within the same main-loop tick.
</div>
"""))

# ══════════════════════════════════════════════════════════════════════════════
# fig7_6  State Machine
# ══════════════════════════════════════════════════════════════════════════════
write("fig7_6.html", page("Figure 7.6 — Service Lifecycle State Machine", """
<div style="display:flex;justify-content:center">
<svg width="1100" height="720" xmlns="http://www.w3.org/2000/svg" style="background:#F8F9FA;border:1px solid #dee2e6;border-radius:10px">
<defs>
  <marker id="a" markerWidth="9" markerHeight="7" refX="9" refY="3.5" orient="auto"><polygon points="0 0,9 3.5,0 7" fill="#5D6D7E"/></marker>
  <marker id="an" markerWidth="9" markerHeight="7" refX="9" refY="3.5" orient="auto"><polygon points="0 0,9 3.5,0 7" fill="#1A3A5C"/></marker>
  <marker id="ag" markerWidth="9" markerHeight="7" refX="9" refY="3.5" orient="auto"><polygon points="0 0,9 3.5,0 7" fill="#1E8449"/></marker>
  <marker id="ao" markerWidth="9" markerHeight="7" refX="9" refY="3.5" orient="auto"><polygon points="0 0,9 3.5,0 7" fill="#CA6F1E"/></marker>
  <marker id="ar" markerWidth="9" markerHeight="7" refX="9" refY="3.5" orient="auto"><polygon points="0 0,9 3.5,0 7" fill="#922B21"/></marker>
  <marker id="ap" markerWidth="9" markerHeight="7" refX="9" refY="3.5" orient="auto"><polygon points="0 0,9 3.5,0 7" fill="#6C3483"/></marker>
</defs>

<!-- Initial pseudo state -->
<circle cx="130" cy="56" r="16" fill="#1C2833"/>
<line x1="130" y1="72" x2="130" y2="120" stroke="#1C2833" stroke-width="2" marker-end="url(#a)"/>

<!-- State circles (r=62) -->
<!-- STOPPED -->
<circle cx="130" cy="182" r="62" fill="#5D6D7E18" stroke="#5D6D7E" stroke-width="3"/>
<text x="130" y="178" text-anchor="middle" font-size="13" font-weight="700" fill="#5D6D7E" font-family="Segoe UI,sans-serif">STOPPED</text>
<text x="130" y="196" text-anchor="middle" font-size="10" fill="#5D6D7E" font-family="Segoe UI,sans-serif">initial state</text>

<!-- STARTING -->
<circle cx="450" cy="182" r="62" fill="#1A3A5C18" stroke="#1A3A5C" stroke-width="3"/>
<text x="450" y="178" text-anchor="middle" font-size="13" font-weight="700" fill="#1A3A5C" font-family="Segoe UI,sans-serif">STARTING</text>
<text x="450" y="196" text-anchor="middle" font-size="10" fill="#1A3A5C" font-family="Segoe UI,sans-serif">fork() called</text>

<!-- RUNNING -->
<circle cx="800" cy="182" r="62" fill="#1E844918" stroke="#1E8449" stroke-width="3"/>
<text x="800" y="178" text-anchor="middle" font-size="13" font-weight="700" fill="#1E8449" font-family="Segoe UI,sans-serif">RUNNING</text>
<text x="800" y="196" text-anchor="middle" font-size="10" fill="#1E8449" font-family="Segoe UI,sans-serif">exec() confirmed</text>

<!-- RESTARTING -->
<circle cx="800" cy="490" r="62" fill="#CA6F1E18" stroke="#CA6F1E" stroke-width="3"/>
<text x="800" y="486" text-anchor="middle" font-size="13" font-weight="700" fill="#CA6F1E" font-family="Segoe UI,sans-serif">RESTARTING</text>
<text x="800" y="504" text-anchor="middle" font-size="10" fill="#CA6F1E" font-family="Segoe UI,sans-serif">waiting restart_at</text>

<!-- FAILED -->
<circle cx="130" cy="490" r="62" fill="#922B2118" stroke="#922B21" stroke-width="3"/>
<text x="130" y="486" text-anchor="middle" font-size="13" font-weight="700" fill="#922B21" font-family="Segoe UI,sans-serif">FAILED</text>
<text x="130" y="504" text-anchor="middle" font-size="10" fill="#922B21" font-family="Segoe UI,sans-serif">restart=never</text>

<!-- DONE (double circle) -->
<circle cx="450" cy="640" r="62" fill="#6C348318" stroke="#6C3483" stroke-width="3"/>
<circle cx="450" cy="640" r="72" fill="none" stroke="#6C3483" stroke-width="2" stroke-dasharray="6,3"/>
<text x="450" y="636" text-anchor="middle" font-size="13" font-weight="700" fill="#6C3483" font-family="Segoe UI,sans-serif">DONE</text>
<text x="450" y="654" text-anchor="middle" font-size="10" fill="#6C3483" font-family="Segoe UI,sans-serif">terminal state</text>

<!-- ── TRANSITIONS ── -->
<!-- STOPPED → STARTING -->
<line x1="192" y1="182" x2="388" y2="182" stroke="#1A3A5C" stroke-width="2" marker-end="url(#an)"/>
<text x="290" y="170" text-anchor="middle" font-size="10" fill="#1A3A5C" font-family="Segoe UI,sans-serif">cmd_start() · deps satisfied</text>

<!-- STARTING → RUNNING -->
<line x1="512" y1="182" x2="738" y2="182" stroke="#1E8449" stroke-width="2" marker-end="url(#ag)"/>
<text x="625" y="170" text-anchor="middle" font-size="10" fill="#1E8449" font-family="Segoe UI,sans-serif">exec() OK · PID live</text>

<!-- RUNNING → RESTARTING -->
<line x1="800" y1="244" x2="800" y2="428" stroke="#CA6F1E" stroke-width="2" marker-end="url(#ao)"/>
<text x="820" y="340" font-size="10" fill="#CA6F1E" font-family="Segoe UI,sans-serif">SIGCHLD · exit</text>
<text x="820" y="354" font-size="10" fill="#CA6F1E" font-family="Segoe UI,sans-serif">restart=always</text>

<!-- RESTARTING → STARTING -->
<path d="M738,490 Q580,490 450,244" fill="none" stroke="#CA6F1E" stroke-width="2" marker-end="url(#ao)" stroke-dasharray="7,3"/>
<text x="555" y="420" text-anchor="middle" font-size="10" fill="#CA6F1E" font-family="Segoe UI,sans-serif">restart_at deadline passed</text>

<!-- RUNNING → FAILED -->
<path d="M750,230 Q450,360 192,460" fill="none" stroke="#922B21" stroke-width="2" marker-end="url(#ar)"/>
<text x="440" y="322" text-anchor="middle" font-size="10" fill="#922B21" font-family="Segoe UI,sans-serif">exit≠0 · restart=never</text>

<!-- STARTING → FAILED -->
<path d="M400,232 Q260,360 192,452" fill="none" stroke="#922B21" stroke-width="2" marker-end="url(#ar)" stroke-dasharray="6,3"/>
<text x="280" y="335" text-anchor="middle" font-size="10" fill="#922B21" font-family="Segoe UI,sans-serif">exec() failed</text>

<!-- FAILED → STOPPED -->
<line x1="130" y1="428" x2="130" y2="244" stroke="#5D6D7E" stroke-width="2" marker-end="url(#a)" stroke-dasharray="5,3"/>
<text x="108" y="338" text-anchor="middle" font-size="10" fill="#5D6D7E" font-family="Segoe UI,sans-serif" transform="rotate(-90,108,338)">cmd_reset()</text>

<!-- RUNNING → DONE -->
<path d="M768,234 Q600,400 510,580" fill="none" stroke="#6C3483" stroke-width="2" marker-end="url(#ap)"/>
<text x="690" y="418" text-anchor="middle" font-size="10" fill="#6C3483" font-family="Segoe UI,sans-serif">exit=0 · oneshot</text>

<!-- STARTING → DONE -->
<line x1="450" y1="244" x2="450" y2="568" stroke="#6C3483" stroke-width="2" marker-end="url(#ap)"/>
<text x="468" y="406" font-size="10" fill="#6C3483" font-family="Segoe UI,sans-serif">oneshot exits 0</text>

<!-- RUNNING → STOPPED (cmd_stop) -->
<path d="M760,144 Q450,60 192,144" fill="none" stroke="#5D6D7E" stroke-width="1.8" marker-end="url(#a)" stroke-dasharray="5,3"/>
<text x="455" y="80" text-anchor="middle" font-size="10" fill="#5D6D7E" font-family="Segoe UI,sans-serif">cmd_stop() · SIGTERM + SIGKILL</text>
</svg>
</div>
"""))

# ══════════════════════════════════════════════════════════════════════════════
# fig7_7  Unix Socket Protocol
# ══════════════════════════════════════════════════════════════════════════════
write("fig7_7.html", page("Figure 7.7 — cogman-ctl Unix Domain Socket Protocol", """
<div style="display:flex;gap:24px;align-items:flex-start">

<!-- Left: protocol exchange -->
<div style="flex:1">
<div style="display:flex;gap:0;align-items:stretch;margin-bottom:16px">
  <div style="border:2.5px solid #1E8449;border-radius:8px;padding:14px 18px;background:#1E84490D;font-size:12.5px;font-weight:700;color:#1E8449;text-align:center;min-width:180px">cogman-ctl<br><small style="font-weight:400;font-size:10.5px;color:#5D6D7E">client</small></div>
  <div style="flex:1;border-top:2px solid #6C3483;border-bottom:2px solid #6C3483;background:#6C34830A;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:8px;font-size:10.5px;color:#6C3483;font-weight:600">/run/cogman-supervisor.sock<br>AF_UNIX · SOCK_STREAM · chmod 0666</div>
  <div style="border:2.5px solid #0E6655;border-radius:8px;padding:14px 18px;background:#0E66550D;font-size:12.5px;font-weight:700;color:#0E6655;text-align:center;min-width:180px">cogman-supervisor<br><small style="font-weight:400;font-size:10.5px;color:#5D6D7E">server (PID 1)</small></div>
</div>

<table style="width:100%;border-collapse:collapse;font-size:12px">
  <tr style="background:#1A3A5C12">
    <th style="padding:8px 12px;text-align:left;color:#1A3A5C;border-bottom:2px solid #1A3A5C;font-size:11px">Step</th>
    <th style="padding:8px 12px;text-align:left;color:#1A3A5C;border-bottom:2px solid #1A3A5C;font-size:11px">Direction</th>
    <th style="padding:8px 12px;text-align:left;color:#1A3A5C;border-bottom:2px solid #1A3A5C;font-size:11px">Data</th>
  </tr>
  <tr><td style="padding:9px 12px;color:#1E8449;font-weight:700">1</td><td style="padding:9px 12px;color:#1E8449">client → server</td><td style="padding:9px 12px;font-family:monospace;color:#1C2833">connect()</td></tr>
  <tr style="background:#F8F8F8"><td style="padding:9px 12px;color:#1E8449;font-weight:700">2</td><td style="padding:9px 12px;color:#1E8449">client → server</td><td style="padding:9px 12px;font-family:monospace;color:#1C2833">"list\n"  <em style="font-size:10px;color:#5D6D7E">(newline-terminated command)</em></td></tr>
  <tr><td style="padding:9px 12px;color:#0E6655;font-weight:700">3</td><td style="padding:9px 12px;color:#0E6655">server → client</td><td style="padding:9px 12px;font-family:monospace;color:#1C2833">"heartbeat RUNNING pid=42\nhello DONE\n...\nOK\n"</td></tr>
  <tr style="background:#F8F8F8"><td style="padding:9px 12px;color:#1E8449;font-weight:700">4</td><td style="padding:9px 12px;color:#1E8449">client → server</td><td style="padding:9px 12px;font-family:monospace;color:#1C2833">close()</td></tr>
</table>
</div>

<!-- Right: two info boxes -->
<div style="min-width:340px;display:flex;flex-direction:column;gap:14px">
  <div style="border:1.5px solid #1E8449;border-radius:8px;padding:14px;background:#1E84490D">
    <div style="font-size:12.5px;font-weight:700;color:#1E8449;margin-bottom:10px">Client commands</div>
    <table style="font-size:11px;font-family:monospace;border-collapse:collapse;width:100%">
      <tr><td style="padding:4px 0;color:#1E8449;font-weight:700">list</td><td style="padding:4px 8px;color:#5D6D7E">print all services + state</td></tr>
      <tr><td style="padding:4px 0;color:#1E8449;font-weight:700">status &lt;name&gt;</td><td style="padding:4px 8px;color:#5D6D7E">detailed info for one service</td></tr>
      <tr><td style="padding:4px 0;color:#1E8449;font-weight:700">start  &lt;name&gt;</td><td style="padding:4px 8px;color:#5D6D7E">start a STOPPED service</td></tr>
      <tr><td style="padding:4px 0;color:#1E8449;font-weight:700">stop   &lt;name&gt;</td><td style="padding:4px 8px;color:#5D6D7E">SIGTERM then SIGKILL</td></tr>
      <tr><td style="padding:4px 0;color:#1E8449;font-weight:700">restart &lt;name&gt;</td><td style="padding:4px 8px;color:#5D6D7E">stop then start</td></tr>
    </table>
  </div>
  <div style="border:1.5px solid #0E6655;border-radius:8px;padding:14px;background:#0E66550D">
    <div style="font-size:12.5px;font-weight:700;color:#0E6655;margin-bottom:10px">Server socket settings</div>
    <div style="font-size:11px;color:#5D6D7E;line-height:1.8">
      • <code>SO_RCVTIMEO = 2 s</code><br>
      • Non-blocking accept (one per loop tick)<br>
      • <code>chmod 0666</code> (operator readable)<br>
      • One connection handled per 100 ms tick<br>
      • Bind: <code>/run/cogman-supervisor.sock</code>
    </div>
  </div>
</div>
</div>
"""))

# ══════════════════════════════════════════════════════════════════════════════
# fig7_8  Messenger IPC
# ══════════════════════════════════════════════════════════════════════════════
write("fig7_8.html", page("Figure 7.8 — Messenger IPC Protocol: Fixed Header + Variable Payload", """
<div style="display:flex;flex-direction:column;gap:20px">

<!-- Header diagram -->
<div>
  <div style="font-size:13px;font-weight:700;color:#6C3483;margin-bottom:10px">16-byte Fixed Header</div>
  <div style="display:flex;gap:0;align-items:stretch;font-size:12px;font-family:monospace">
    <div style="border:2.5px solid #6C3483;border-radius:6px 0 0 6px;padding:12px 16px;background:#6C34830D;text-align:center;min-width:140px">
      <div style="font-weight:700;color:#6C3483">magic[4]</div>
      <div style="font-size:10px;color:#5D6D7E">0x434F4731</div>
      <div style="font-size:10px;color:#5D6D7E">"COG1"</div>
      <div style="font-size:9px;color:#9A9A9A;margin-top:4px">bytes 0–3</div>
    </div>
    <div style="border:2.5px solid #1A3A5C;border-left:none;padding:12px 16px;background:#1A3A5C0D;text-align:center;min-width:100px">
      <div style="font-weight:700;color:#1A3A5C">version</div>
      <div style="font-size:10px;color:#5D6D7E">u16 = 1</div>
      <div style="font-size:9px;color:#9A9A9A;margin-top:4px">bytes 4–5</div>
    </div>
    <div style="border:2.5px solid #1A3A5C;border-left:none;padding:12px 16px;background:#1A3A5C0D;text-align:center;min-width:110px">
      <div style="font-weight:700;color:#1A3A5C">msg_type</div>
      <div style="font-size:10px;color:#5D6D7E">u16</div>
      <div style="font-size:9px;color:#9A9A9A;margin-top:4px">bytes 6–7</div>
    </div>
    <div style="border:2.5px solid #0E6655;border-left:none;padding:12px 16px;background:#0E66550D;text-align:center;min-width:130px">
      <div style="font-weight:700;color:#0E6655">payload_len</div>
      <div style="font-size:10px;color:#5D6D7E">u32</div>
      <div style="font-size:9px;color:#9A9A9A;margin-top:4px">bytes 8–11</div>
    </div>
    <div style="border:2.5px solid #0E6655;border-left:none;border-radius:0 6px 6px 0;padding:12px 16px;background:#0E66550D;text-align:center;min-width:120px">
      <div style="font-weight:700;color:#0E6655">src_pid</div>
      <div style="font-size:10px;color:#5D6D7E">u32</div>
      <div style="font-size:9px;color:#9A9A9A;margin-top:4px">bytes 12–15</div>
    </div>
    <div style="margin-left:8px;border:2.5px dashed #1E8449;border-radius:6px;padding:12px 16px;background:#1E84490D;text-align:center;flex:1">
      <div style="font-weight:700;color:#1E8449">Variable Payload</div>
      <div style="font-size:10px;color:#5D6D7E">0 … payload_len bytes</div>
      <div style="font-size:9px;color:#9A9A9A;margin-top:4px">bytes 16 … 16+N</div>
    </div>
  </div>
</div>

<!-- Two columns: types + topology -->
<div style="display:flex;gap:20px">
  <div style="flex:1;border:1.5px solid #1A3A5C;border-radius:8px;padding:16px;background:#1A3A5C0A">
    <div style="font-size:13px;font-weight:700;color:#1A3A5C;margin-bottom:12px">Message Types  (msg_type field)</div>
    <table style="width:100%;font-size:11.5px;border-collapse:collapse">
      <tr style="border-bottom:1px solid #dee2e6"><td style="padding:7px 6px;font-family:monospace;color:#6C3483;font-weight:700">0</td><td style="padding:7px 6px;font-family:monospace;color:#1C2833">MSG_HEARTBEAT</td><td style="padding:7px 6px;color:#5D6D7E">Keepalive ping</td></tr>
      <tr style="border-bottom:1px solid #dee2e6"><td style="padding:7px 6px;font-family:monospace;color:#6C3483;font-weight:700">1</td><td style="padding:7px 6px;font-family:monospace;color:#1C2833">MSG_HUD_ALERT</td><td style="padding:7px 6px;color:#5D6D7E">Status alert to terminal</td></tr>
      <tr style="border-bottom:1px solid #dee2e6"><td style="padding:7px 6px;font-family:monospace;color:#6C3483;font-weight:700">2</td><td style="padding:7px 6px;font-family:monospace;color:#1C2833">MSG_POLICY_REQ</td><td style="padding:7px 6px;color:#5D6D7E">Policy enforcement check</td></tr>
      <tr style="border-bottom:1px solid #dee2e6"><td style="padding:7px 6px;font-family:monospace;color:#6C3483;font-weight:700">3</td><td style="padding:7px 6px;font-family:monospace;color:#1C2833">MSG_DATA_XFER</td><td style="padding:7px 6px;color:#5D6D7E">Binary data transfer</td></tr>
      <tr><td style="padding:7px 6px;font-family:monospace;color:#6C3483;font-weight:700">4</td><td style="padding:7px 6px;font-family:monospace;color:#1C2833">MSG_LOG_INFO</td><td style="padding:7px 6px;color:#5D6D7E">Structured log record</td></tr>
    </table>
  </div>
  <div style="flex:1;border:1.5px solid #6C3483;border-radius:8px;padding:16px;background:#6C34830A">
    <div style="font-size:13px;font-weight:700;color:#6C3483;margin-bottom:12px">Broker Topology</div>
    <div style="text-align:center;margin-bottom:10px">
      <div style="display:inline-block;border:2.5px solid #6C3483;border-radius:8px;padding:10px 20px;background:#6C348318;font-size:12px;font-weight:700;color:#6C3483">messenger broker<br><small style="font-weight:400;font-size:10px">TCP :7201</small></div>
    </div>
    <div style="display:flex;gap:10px;justify-content:center">
      <div style="border:2px solid #0E6655;border-radius:6px;padding:8px 10px;background:#0E66550D;font-size:11px;font-weight:700;color:#0E6655;text-align:center">cogman-sup<br><small style="font-weight:400">publisher</small></div>
      <div style="border:2px solid #C0392B;border-radius:6px;padding:8px 10px;background:#C0392B0D;font-size:11px;font-weight:700;color:#C0392B;text-align:center">cogman-exec<br><small style="font-weight:400">publisher</small></div>
      <div style="border:2px solid #1E8449;border-radius:6px;padding:8px 10px;background:#1E84490D;font-size:11px;font-weight:700;color:#1E8449;text-align:center">log-collector<br><small style="font-weight:400">subscriber</small></div>
    </div>
    <div style="text-align:center;font-size:11px;color:#5D6D7E;margin-top:8px">All components ⇄ broker via TCP TLV messages</div>
  </div>
</div>
</div>
"""))

# ══════════════════════════════════════════════════════════════════════════════
# fig7_9  Rootfs Layout
# ══════════════════════════════════════════════════════════════════════════════
write("fig7_9.html", page("Figure 7.9 — Minimal Rootfs Directory Layout  (6.3 MB total)", """
<div style="display:flex;gap:24px">
<!-- Tree -->
<div style="flex:1;font-family:monospace;font-size:12.5px;line-height:1.9;border:1.5px solid #dee2e6;border-radius:8px;padding:16px 20px;background:#fff">
<span style="font-size:15px;font-weight:700;color:#1C2833">/</span>
<div style="margin-left:14px">
  <div><span style="color:#0E6655;font-weight:700">├─ sbin/</span></div>
  <div style="margin-left:22px"><span style="color:#0E6655">└─ init</span> <span style="color:#5D6D7E;font-size:11px">→ symlink to cogman-supervisor</span></div>
  <div><span style="color:#1A3A5C;font-weight:700">├─ bin/</span></div>
  <div style="margin-left:22px"><span style="color:#1A3A5C">├─ sh</span> <span style="color:#5D6D7E;font-size:11px">→ symlink to /bin/busybox</span></div>
  <div style="margin-left:22px"><span style="color:#1A3A5C">└─ busybox</span> <span style="color:#5D6D7E;font-size:11px">1.1 MB · multi-call binary</span></div>
  <div><span style="color:#1A3A5C;font-weight:700">├─ usr/bin/</span></div>
  <div style="margin-left:22px"><span style="color:#0E6655">├─ cogman-supervisor</span> <span style="color:#5D6D7E;font-size:11px">312 KB · PID 1</span></div>
  <div style="margin-left:22px"><span style="color:#0E6655">├─ cogman-executor</span> <span style="color:#5D6D7E;font-size:11px">180 KB</span></div>
  <div style="margin-left:22px"><span style="color:#C0392B">├─ cogman-planner</span> <span style="color:#5D6D7E;font-size:11px">1.4 MB (Rust)</span></div>
  <div style="margin-left:22px"><span style="color:#1E8449">└─ cogman-ctl</span> <span style="color:#5D6D7E;font-size:11px">45 KB</span></div>
  <div><span style="color:#6C3483;font-weight:700">├─ etc/cogman/services/</span></div>
  <div style="margin-left:22px"><span style="color:#1E8449">├─ hello.service</span> <span style="color:#5D6D7E;font-size:11px">oneshot · no deps</span></div>
  <div style="margin-left:22px"><span style="color:#1E8449">├─ heartbeat.service</span> <span style="color:#5D6D7E;font-size:11px">process · restart=always</span></div>
  <div style="margin-left:22px"><span style="color:#1E8449">├─ ctl-probe.service</span> <span style="color:#5D6D7E;font-size:11px">oneshot · after=heartbeat</span></div>
  <div style="margin-left:22px"><span style="color:#1E8449">└─ shutdown.service</span> <span style="color:#5D6D7E;font-size:11px">oneshot · last</span></div>
  <div><span style="color:#5D6D7E;font-weight:700">├─ proc/</span> <span style="color:#5D6D7E;font-size:11px">← procfs mount</span></div>
  <div><span style="color:#5D6D7E;font-weight:700">├─ sys/</span>  <span style="color:#5D6D7E;font-size:11px">← sysfs mount</span></div>
  <div><span style="color:#5D6D7E;font-weight:700">├─ dev/</span>  <span style="color:#5D6D7E;font-size:11px">← devtmpfs mount</span></div>
  <div><span style="color:#CA6F1E;font-weight:700">├─ run/</span>  <span style="color:#5D6D7E;font-size:11px">← tmpfs mount</span></div>
  <div style="margin-left:22px"><span style="color:#CA6F1E">└─ cogman-supervisor.sock</span> <span style="color:#5D6D7E;font-size:11px">AF_UNIX control socket</span></div>
  <div><span style="color:#9A7D0A;font-weight:700">├─ lib/</span></div>
  <div style="margin-left:22px"><span style="color:#9A7D0A">└─ libc.so</span> <span style="color:#5D6D7E;font-size:11px">→ musl-libc · 90 KB</span></div>
  <div><span style="color:#5D6D7E;font-weight:700">└─ tmp/</span></div>
</div>
</div>

<!-- Right: size panel + boot note -->
<div style="min-width:320px;display:flex;flex-direction:column;gap:14px">
  <div style="border:1.5px solid #1A3A5C;border-radius:8px;padding:14px;background:#fff">
    <div style="font-size:13px;font-weight:700;color:#1A3A5C;margin-bottom:12px">Binary Sizes  (stripped ELF)</div>
    <table style="width:100%;font-size:12px;border-collapse:collapse">
      <tr><td style="padding:6px 0;color:#C0392B;font-weight:600">cogman-planner</td><td style="padding:6px 0;text-align:right;color:#C0392B;font-weight:700">1.40 MB</td></tr>
      <tr style="border-top:1px solid #eee"><td style="padding:6px 0;color:#1A3A5C;font-weight:600">busybox</td><td style="padding:6px 0;text-align:right;color:#1A3A5C;font-weight:700">1.10 MB</td></tr>
      <tr style="border-top:1px solid #eee"><td style="padding:6px 0;color:#0E6655;font-weight:600">cogman-supervisor</td><td style="padding:6px 0;text-align:right;color:#0E6655;font-weight:700">312 KB</td></tr>
      <tr style="border-top:1px solid #eee"><td style="padding:6px 0;color:#0E6655;font-weight:600">cogman-executor</td><td style="padding:6px 0;text-align:right;color:#0E6655;font-weight:700">180 KB</td></tr>
      <tr style="border-top:1px solid #eee"><td style="padding:6px 0;color:#1E8449;font-weight:600">cogman-ctl</td><td style="padding:6px 0;text-align:right;color:#1E8449;font-weight:700">45 KB</td></tr>
      <tr style="border-top:1px solid #eee"><td style="padding:6px 0;color:#9A7D0A;font-weight:600">musl-libc</td><td style="padding:6px 0;text-align:right;color:#9A7D0A;font-weight:700">90 KB</td></tr>
      <tr style="border-top:1px solid #eee"><td style="padding:6px 0;color:#6C3483;font-weight:600">service files (×4)</td><td style="padding:6px 0;text-align:right;color:#6C3483;font-weight:700">&lt;1 KB</td></tr>
      <tr style="border-top:2px solid #1A3A5C"><td style="padding:8px 0;color:#1C2833;font-weight:700;font-size:13px">Total rootfs</td><td style="padding:8px 0;text-align:right;color:#1C2833;font-weight:700;font-size:13px">6.30 MB</td></tr>
    </table>
  </div>
  <div style="border:1.5px solid #0E6655;border-radius:8px;padding:14px;background:#0E66550A;font-size:11.5px;color:#5D6D7E;line-height:1.7">
    <strong style="color:#0E6655">Boot sequence:</strong><br>
    kernel → <code>execve(/sbin/init)</code><br>
    → cogman-supervisor (PID 1)<br>
    → mount {proc, sys, dev, run}<br>
    → parse /etc/cogman/services/<br>
    → start 4 verification services<br>
    → all PASS → enter main loop
  </div>
</div>
</div>
"""))

# ══════════════════════════════════════════════════════════════════════════════
# fig8_1  Boot Sequence
# ══════════════════════════════════════════════════════════════════════════════
write("fig8_1.html", page("Figure 8.1 — Service Boot Sequence on Minimal Rootfs  (QEMU Verified)", """
<div style="display:flex;gap:22px">

<!-- Timeline -->
<div style="flex:1">
<div style="font-size:12px;color:#5D6D7E;margin-bottom:8px;font-style:italic">Boot timeline  (QEMU x86_64 · -m 128M · single serial console)</div>
<svg width="900" height="380" xmlns="http://www.w3.org/2000/svg" style="background:#fff;border:1px solid #dee2e6;border-radius:8px">
<defs>
  <marker id="ta" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#1C2833"/></marker>
</defs>
<!-- timeline bar -->
<line x1="30" y1="200" x2="870" y2="200" stroke="#1C2833" stroke-width="3" marker-end="url(#ta)"/>
<text x="880" y="204" font-size="11" fill="#5D6D7E" font-family="Segoe UI,sans-serif">time</text>

<!-- Events: (x, label lines, y_box, color) alternating above/below -->
<g font-family="Segoe UI,sans-serif">
<!-- Kernel -->
<line x1="60"  y1="200" x2="60"  y2="110" stroke="#5D6D7E" stroke-width="1.5" stroke-dasharray="4,3"/>
<circle cx="60" cy="200" r="8" fill="#5D6D7E"/>
<rect x="10"  y="68" width="100" height="42" rx="6" fill="#5D6D7E18" stroke="#5D6D7E" stroke-width="2"/>
<text x="60"  y="84"  text-anchor="middle" font-size="10.5" font-weight="700" fill="#5D6D7E">Kernel boots</text>
<text x="60"  y="100" text-anchor="middle" font-size="9.5"  fill="#5D6D7E">0 ms</text>

<!-- execve init -->
<line x1="170" y1="200" x2="170" y2="290" stroke="#0E6655" stroke-width="1.5" stroke-dasharray="4,3"/>
<circle cx="170" cy="200" r="8" fill="#0E6655"/>
<rect x="110" y="270" width="120" height="42" rx="6" fill="#0E665518" stroke="#0E6655" stroke-width="2"/>
<text x="170" y="286" text-anchor="middle" font-size="10.5" font-weight="700" fill="#0E6655">execve /sbin/init</text>
<text x="170" y="302" text-anchor="middle" font-size="9.5"  fill="#0E6655">~50 ms · PID 1</text>

<!-- mount vfs -->
<line x1="290" y1="200" x2="290" y2="110" stroke="#1A3A5C" stroke-width="1.5" stroke-dasharray="4,3"/>
<circle cx="290" cy="200" r="8" fill="#1A3A5C"/>
<rect x="230" y="68" width="120" height="42" rx="6" fill="#1A3A5C18" stroke="#1A3A5C" stroke-width="2"/>
<text x="290" y="84"  text-anchor="middle" font-size="10.5" font-weight="700" fill="#1A3A5C">mount vfs</text>
<text x="290" y="100" text-anchor="middle" font-size="9.5"  fill="#1A3A5C">proc·sys·dev·run</text>

<!-- parse services -->
<line x1="410" y1="200" x2="410" y2="290" stroke="#6C3483" stroke-width="1.5" stroke-dasharray="4,3"/>
<circle cx="410" cy="200" r="8" fill="#6C3483"/>
<rect x="348" y="270" width="125" height="42" rx="6" fill="#6C348318" stroke="#6C3483" stroke-width="2"/>
<text x="410" y="286" text-anchor="middle" font-size="10.5" font-weight="700" fill="#6C3483">parse services</text>
<text x="410" y="302" text-anchor="middle" font-size="9.5"  fill="#6C3483">4 files loaded</text>

<!-- hello DONE -->
<line x1="510" y1="200" x2="510" y2="110" stroke="#1E8449" stroke-width="1.5" stroke-dasharray="4,3"/>
<circle cx="510" cy="200" r="8" fill="#1E8449"/>
<rect x="450" y="68" width="120" height="42" rx="6" fill="#1E844918" stroke="#1E8449" stroke-width="2"/>
<text x="510" y="84"  text-anchor="middle" font-size="10.5" font-weight="700" fill="#1E8449">hello: DONE</text>
<text x="510" y="100" text-anchor="middle" font-size="9.5"  fill="#1E8449">exit=0 ✓</text>

<!-- heartbeat RUNNING -->
<line x1="620" y1="200" x2="620" y2="290" stroke="#0E6655" stroke-width="1.5" stroke-dasharray="4,3"/>
<circle cx="620" cy="200" r="8" fill="#0E6655"/>
<rect x="555" y="270" width="130" height="42" rx="6" fill="#0E665518" stroke="#0E6655" stroke-width="2"/>
<text x="620" y="286" text-anchor="middle" font-size="10.5" font-weight="700" fill="#0E6655">heartbeat: RUNNING</text>
<text x="620" y="302" text-anchor="middle" font-size="9.5"  fill="#0E6655">pid=42 ✓</text>

<!-- ctl-probe + shutdown -->
<line x1="730" y1="200" x2="730" y2="110" stroke="#1A3A5C" stroke-width="1.5" stroke-dasharray="4,3"/>
<circle cx="730" cy="200" r="8" fill="#1A3A5C"/>
<rect x="670" y="68" width="120" height="42" rx="6" fill="#1A3A5C18" stroke="#1A3A5C" stroke-width="2"/>
<text x="730" y="84"  text-anchor="middle" font-size="10.5" font-weight="700" fill="#1A3A5C">ctl-probe: DONE</text>
<text x="730" y="100" text-anchor="middle" font-size="9.5"  fill="#1A3A5C">exit=0 ✓</text>

<!-- ALL PASS -->
<line x1="830" y1="200" x2="830" y2="290" stroke="#1E8449" stroke-width="2" stroke-dasharray="4,3"/>
<circle cx="830" cy="200" r="10" fill="#1E8449" stroke="#fff" stroke-width="2"/>
<rect x="765" y="270" width="110" height="48" rx="6" fill="#1E844930" stroke="#1E8449" stroke-width="2.5"/>
<text x="820" y="289" text-anchor="middle" font-size="11" font-weight="700" fill="#1E8449">ALL STAGES</text>
<text x="820" y="306" text-anchor="middle" font-size="11" font-weight="700" fill="#1E8449">PASS ✓</text>

<!-- time labels -->
<text x="60"  y="220" text-anchor="middle" font-size="9" fill="#aaa">0</text>
<text x="170" y="220" text-anchor="middle" font-size="9" fill="#aaa">50ms</text>
<text x="290" y="220" text-anchor="middle" font-size="9" fill="#aaa">80ms</text>
<text x="410" y="220" text-anchor="middle" font-size="9" fill="#aaa">90ms</text>
<text x="510" y="220" text-anchor="middle" font-size="9" fill="#aaa">110ms</text>
<text x="620" y="220" text-anchor="middle" font-size="9" fill="#aaa">130ms</text>
<text x="730" y="220" text-anchor="middle" font-size="9" fill="#aaa">150ms</text>
<text x="830" y="220" text-anchor="middle" font-size="9" fill="#aaa">~1.8s</text>

<!-- Phase brackets -->
<line x1="30"  y1="340" x2="380" y2="340" stroke="#5D6D7E" stroke-width="2"/>
<line x1="30"  y1="335" x2="30"  y2="345" stroke="#5D6D7E" stroke-width="2"/>
<line x1="380" y1="335" x2="380" y2="345" stroke="#5D6D7E" stroke-width="2"/>
<text x="205" y="358" text-anchor="middle" font-size="10.5" fill="#5D6D7E" font-weight="600">Kernel init</text>

<line x1="385" y1="340" x2="780" y2="340" stroke="#1E8449" stroke-width="2"/>
<line x1="385" y1="335" x2="385" y2="345" stroke="#1E8449" stroke-width="2"/>
<line x1="780" y1="335" x2="780" y2="345" stroke="#1E8449" stroke-width="2"/>
<text x="582" y="358" text-anchor="middle" font-size="10.5" fill="#1E8449" font-weight="600">Service startup &amp; verification</text>

<line x1="785" y1="340" x2="860" y2="340" stroke="#0E6655" stroke-width="2"/>
<line x1="785" y1="335" x2="785" y2="345" stroke="#0E6655" stroke-width="2"/>
<line x1="860" y1="335" x2="860" y2="345" stroke="#0E6655" stroke-width="2"/>
<text x="822" y="358" text-anchor="middle" font-size="9" fill="#0E6655" font-weight="600">Main loop</text>
</g>
</svg>

<!-- QEMU command -->
<div style="margin-top:10px;border:1.5px solid #5D6D7E;border-radius:6px;padding:10px 14px;background:#5D6D7E0D;font-family:monospace;font-size:11px;color:#1C2833">
qemu-system-x86_64 -kernel /boot/vmlinuz -drive file=rootfs.img,format=raw -append "console=ttyS0 root=/dev/sda rw init=/sbin/init quiet" -nographic -m 128M -serial mon:stdio
</div>
</div>

<!-- Performance panel -->
<div style="min-width:300px;border:2px solid #1E8449;border-radius:10px;padding:18px;background:#1E84490A">
  <div style="font-size:13px;font-weight:700;color:#1E8449;margin-bottom:14px">Performance vs Python reference</div>
  <table style="width:100%;font-size:12px;border-collapse:collapse">
    <tr style="border-bottom:1px solid #dee2e6"><th style="padding:7px 0;text-align:left;color:#1A3A5C;font-size:11px">Metric</th><th style="padding:7px 0;text-align:right;color:#1A3A5C;font-size:11px">Ours</th><th style="padding:7px 0;text-align:right;color:#1A3A5C;font-size:11px">Ref</th><th style="padding:7px 0;text-align:right;color:#1A3A5C;font-size:11px">Gain</th></tr>
    <tr style="border-bottom:1px solid #eee"><td style="padding:8px 0">Plan resolution</td><td style="padding:8px 0;text-align:right;color:#1E8449;font-weight:700">8 ms</td><td style="padding:8px 0;text-align:right;color:#922B21">450 ms</td><td style="padding:8px 0;text-align:right;color:#1E8449;font-weight:700">56×</td></tr>
    <tr style="border-bottom:1px solid #eee"><td style="padding:8px 0">Peak memory</td><td style="padding:8px 0;text-align:right;color:#1E8449;font-weight:700">4 MB</td><td style="padding:8px 0;text-align:right;color:#922B21">85 MB</td><td style="padding:8px 0;text-align:right;color:#1E8449;font-weight:700">21×</td></tr>
    <tr style="border-bottom:1px solid #eee"><td style="padding:8px 0">Per-step overhead</td><td style="padding:8px 0;text-align:right;color:#1E8449;font-weight:700">0.2 ms</td><td style="padding:8px 0;text-align:right;color:#922B21">10 ms</td><td style="padding:8px 0;text-align:right;color:#1E8449;font-weight:700">50×</td></tr>
    <tr><td style="padding:8px 0">Rootfs size</td><td style="padding:8px 0;text-align:right;color:#1E8449;font-weight:700">6.3 MB</td><td style="padding:8px 0;text-align:right;color:#5D6D7E">N/A</td><td style="padding:8px 0;text-align:right;color:#1E8449;font-weight:700">—</td></tr>
  </table>
</div>
</div>
"""))

# ══════════════════════════════════════════════════════════════════════════════
# extra_dwm.html  — DWM UI mockup
# ══════════════════════════════════════════════════════════════════════════════
write("extra_dwm.html", """<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { background:#1a1a2e; font-family: 'Courier New', monospace; color:#e2e8f0; width:1920px; height:1080px; overflow:hidden; }
#bar { background:#16213e; height:26px; display:flex; align-items:center; border-bottom:1.5px solid #4ecca3; padding:0 6px; gap:0; position:fixed; top:0; left:0; right:0; z-index:100; }
.tag { width:24px; height:22px; display:flex; align-items:center; justify-content:center; font-size:12px; color:#8888aa; cursor:pointer; border-radius:3px; }
.tag.active { color:#4ecca3; background:#0f3460; font-weight:700; }
#layout-sym { color:#4ecca3; font-size:12px; font-weight:700; padding:0 10px; border-left:1px solid #4ecca350; border-right:1px solid #4ecca350; margin:0 4px; }
#win-title { flex:1; text-align:center; font-size:12px; color:#e2e8f0; }
#status { font-size:11px; color:#a0aec0; padding-right:8px; white-space:nowrap; }
#windows { display:flex; gap:2px; position:absolute; top:28px; left:0; right:0; bottom:0; }
.win { background:#0d1117; border:1.5px solid #30363d; display:flex; flex-direction:column; }
.win.focused { border-color:#4ecca3; }
.titlebar { background:#161b22; height:26px; display:flex; align-items:center; padding:0 10px; gap:0; border-bottom:1px solid #30363d; flex-shrink:0; }
.btn { width:13px; height:13px; border-radius:50%; margin-right:6px; }
.btn.r { background:#ff5f57; } .btn.y { background:#febc2e; } .btn.g { background:#28c840; }
.win-name { flex:1; text-align:center; font-size:11px; color:#8b949e; }
.term { flex:1; padding:10px 14px; font-size:11.5px; line-height:1.7; overflow:hidden; font-family:'Courier New',monospace; }
</style></head><body>
<div id="bar">
  <div class="tag active">1</div>
  <div class="tag">2</div><div class="tag">3</div><div class="tag">4</div>
  <div class="tag">5</div><div class="tag">6</div><div class="tag">7</div>
  <div class="tag">8</div><div class="tag">9</div>
  <div id="layout-sym">[]=</div>
  <div id="win-title">cogman-supervisor — Rogue Linux  [RUNNING · 4 services]</div>
  <div id="status">CPU 0.1%  MEM 4.2MB  [heartbeat ✓] [ctl-probe ✓]  2025-05-20 14:32:18</div>
</div>
<div id="windows">
  <!-- LEFT window: supervisor log -->
  <div class="win focused" style="width:58%">
    <div class="titlebar">
      <div class="btn r"></div><div class="btn y"></div><div class="btn g"></div>
      <div class="win-name">st — void@rogue-linux: ~  [cogman-supervisor PID=1]</div>
    </div>
    <div class="term">
<span style="color:#4ecca3">cogman-supervisor v0.9.0 starting (PID 1)</span><br>
<span style="color:#8888aa">→ mounting /proc      [procfs]</span><br>
<span style="color:#8888aa">→ mounting /sys       [sysfs]</span><br>
<span style="color:#8888aa">→ mounting /dev       [devtmpfs]</span><br>
<span style="color:#8888aa">→ mounting /run       [tmpfs]</span><br>
<span style="color:#4ecca3">→ loading services from /etc/cogman/services/</span><br>
<span style="color:#a0aec0">&nbsp;&nbsp;found: hello.service       [oneshot]</span><br>
<span style="color:#a0aec0">&nbsp;&nbsp;found: heartbeat.service   [process, restart=always]</span><br>
<span style="color:#a0aec0">&nbsp;&nbsp;found: ctl-probe.service   [oneshot, after=heartbeat]</span><br>
<span style="color:#a0aec0">&nbsp;&nbsp;found: shutdown.service    [oneshot]</span><br>
<span style="color:#4ecca3">→ dependency graph resolved — 4 services</span><br>
<span style="color:#e2e8f0">&nbsp;&nbsp;starting: hello.service</span><br>
<span style="color:#28c840">&nbsp;&nbsp;✓ hello.service       DONE  (exit=0, elapsed=2ms)</span><br>
<span style="color:#e2e8f0">&nbsp;&nbsp;starting: heartbeat.service</span><br>
<span style="color:#28c840">&nbsp;&nbsp;✓ heartbeat.service   RUNNING  (pid=42)</span><br>
<span style="color:#e2e8f0">&nbsp;&nbsp;starting: ctl-probe.service</span><br>
<span style="color:#28c840">&nbsp;&nbsp;✓ ctl-probe.service   DONE  (exit=0)</span><br>
<span style="color:#28c840">&nbsp;&nbsp;✓ shutdown.service    DONE  (exit=0)</span><br>
<span style="color:#4ecca3">→ all 4 verification stages passed ✓</span><br>
<span style="color:#8888aa">──────────────────────────────────────────────────────</span><br>
<span style="color:#e2e8f0">supervisor entering main loop (100ms poll)</span><br>
<span style="color:#a0aec0">&nbsp;&nbsp;select(pipe_r=3, ctl_fd=4, timeout=100ms)</span><br>
<span style="color:#a0aec0">&nbsp;&nbsp;[heartbeat] pid=42  state=RUNNING  restarts=0</span><br>
<span style="color:#a0aec0">&nbsp;&nbsp;[heartbeat] pid=42  state=RUNNING  restarts=0</span><br>
<span style="color:#febc2e">&nbsp;&nbsp;[heartbeat] SIGCHLD received  pid=42 exit=0</span><br>
<span style="color:#febc2e">&nbsp;&nbsp;[heartbeat] restart=always → RESTARTING (delay=500ms)</span><br>
<span style="color:#28c840">&nbsp;&nbsp;[heartbeat] restarted  new_pid=43  restarts=1</span><br>
<span style="color:#a0aec0">&nbsp;&nbsp;[heartbeat] pid=43  state=RUNNING  restarts=1</span><br>
<span style="color:#a0aec0">&nbsp;&nbsp;[heartbeat] pid=43  state=RUNNING  restarts=1</span><br>
<span style="color:#4ecca3">$</span><span style="display:inline-block;width:8px;height:14px;background:#4ecca3;vertical-align:-2px"></span>
    </div>
  </div>

  <!-- RIGHT window: cogman-ctl -->
  <div class="win" style="flex:1">
    <div class="titlebar">
      <div class="btn r"></div><div class="btn y"></div><div class="btn g"></div>
      <div class="win-name">st — void@rogue-linux: ~  [cogman-ctl]</div>
    </div>
    <div class="term">
<span style="color:#a0aec0">void@rogue-linux:~$ </span><span style="color:#e2e8f0">cogman-ctl list</span><br>
<br>
<span style="color:#4ecca3">NAME               STATE       PID    RESTARTS</span><br>
<span style="color:#4ecca3">─────────────────────────────────────────────</span><br>
<span style="color:#28c840">heartbeat          RUNNING     43     1</span><br>
<span style="color:#a0aec0">hello              DONE        —      0</span><br>
<span style="color:#a0aec0">ctl-probe          DONE        —      0</span><br>
<span style="color:#a0aec0">shutdown           DONE        —      0</span><br>
<br>
<span style="color:#a0aec0">void@rogue-linux:~$ </span><span style="color:#e2e8f0">cogman-ctl status heartbeat</span><br>
<br>
<span style="color:#4ecca3">Service:     heartbeat</span><br>
<span style="color:#a0aec0">State:       RUNNING</span><br>
<span style="color:#a0aec0">PID:         43</span><br>
<span style="color:#a0aec0">Command:     /usr/bin/heartbeat</span><br>
<span style="color:#a0aec0">Type:        process</span><br>
<span style="color:#a0aec0">Restart:     always</span><br>
<span style="color:#a0aec0">Restarts:    1</span><br>
<span style="color:#a0aec0">Started:     2025-05-20 14:32:01</span><br>
<br>
<span style="color:#a0aec0">void@rogue-linux:~$ </span><span style="color:#e2e8f0">free -h</span><br>
<span style="color:#4ecca3">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;total&nbsp;&nbsp;&nbsp;used&nbsp;&nbsp;&nbsp;free</span><br>
<span style="color:#a0aec0">Mem:&nbsp;&nbsp;&nbsp;&nbsp;128Mi&nbsp;&nbsp;&nbsp;4.2Mi&nbsp;&nbsp;123Mi</span><br>
<br>
<span style="color:#a0aec0">void@rogue-linux:~$ </span><span style="color:#e2e8f0">ps aux</span><br>
<span style="color:#4ecca3">PID&nbsp;&nbsp;COMM&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;RSS</span><br>
<span style="color:#a0aec0">&nbsp;&nbsp;1&nbsp;&nbsp;cogman-supervisor&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;312K</span><br>
<span style="color:#a0aec0">&nbsp;&nbsp;43 heartbeat&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;148K</span><br>
<br>
<span style="color:#a0aec0">void@rogue-linux:~$ </span><span style="display:inline-block;width:8px;height:14px;background:#4ecca3;vertical-align:-2px"></span>
    </div>
  </div>
</div>
</body></html>
""")

# ══════════════════════════════════════════════════════════════════════════════
# extra_terminal.html — standalone terminal
# ══════════════════════════════════════════════════════════════════════════════
write("extra_terminal.html", """<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { background:#1a1a2e; font-family:'Courier New',monospace; width:1200px; }
.terminal { background:#0d1117; border:2px solid #30363d; border-radius:10px; overflow:hidden; margin:16px; }
.titlebar { background:#161b22; height:32px; display:flex; align-items:center; padding:0 14px; border-bottom:1px solid #30363d; }
.btn { width:13px; height:13px; border-radius:50%; margin-right:7px; }
.btn.r{background:#ff5f57;} .btn.y{background:#febc2e;} .btn.g{background:#28c840;}
.wname { flex:1; text-align:center; font-size:12px; color:#8b949e; }
.body { padding:14px 18px; font-size:12.5px; line-height:1.75; color:#e2e8f0; }
.p { color:#4ecca3; } .s { color:#e2e8f0; } .g { color:#28c840; }
.d { color:#a0aec0; } .w { color:#febc2e; } .e { color:#ff5f57; }
.dim { color:#8888aa; }
</style></head><body>
<div class="terminal">
<div class="titlebar">
  <div class="btn r"></div><div class="btn y"></div><div class="btn g"></div>
  <div class="wname">st — void@rogue-linux: ~</div>
</div>
<div class="body">
<span class="p">void@rogue-linux:~$ </span><span class="s">uname -a</span><br>
<span class="d">Linux rogue-linux 6.1.0 #1 SMP x86_64 GNU/Linux</span><br>
<br>
<span class="p">void@rogue-linux:~$ </span><span class="s">cogman-planner --meta packages/cogman.toml --out /tmp/cogman.bin</span><br>
<br>
<span class="g">&nbsp;&nbsp;✓&nbsp;&nbsp;cogman  v0.9.0</span><br>
<span class="d">&nbsp;&nbsp;→&nbsp;&nbsp;loading metadata &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;packages/cogman.toml</span><br>
<span class="d">&nbsp;&nbsp;→&nbsp;&nbsp;validating schema &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;OK</span><br>
<span class="d">&nbsp;&nbsp;→&nbsp;&nbsp;resolving dependencies &nbsp;musl-libc → linux-headers → kernel</span><br>
<span class="d">&nbsp;&nbsp;→&nbsp;&nbsp;topological sort &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;6 packages in order</span><br>
<span class="d">&nbsp;&nbsp;→&nbsp;&nbsp;enforcing policy &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;allow_write=[/tmp,/usr]  ✓</span><br>
<span class="d">&nbsp;&nbsp;→&nbsp;&nbsp;checking FNV-1a cache &nbsp;&nbsp;hash=0xdeadbeef  (cache miss)</span><br>
<span class="g">&nbsp;&nbsp;✓&nbsp;&nbsp;plan written &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;/tmp/cogman.bin  (2048 bytes · 14 steps)</span><br>
<span class="d">&nbsp;&nbsp;→&nbsp;&nbsp;elapsed: 8 ms &nbsp;&nbsp;peak_mem: 4.1 MB</span><br>
<br>
<span class="p">void@rogue-linux:~$ </span><span class="s">cogman-executor /tmp/cogman.bin</span><br>
<br>
<span class="d">&nbsp;&nbsp;→&nbsp;&nbsp;mmap /tmp/cogman.bin &nbsp;&nbsp;&nbsp;(PROT_READ · MAP_PRIVATE)</span><br>
<span class="d">&nbsp;&nbsp;→&nbsp;&nbsp;magic=CGM2PLAN &nbsp;version=1 &nbsp;steps=14</span><br>
<span class="d">&nbsp;&nbsp;step &nbsp;1/14 &nbsp;OP_MKDIR &nbsp;&nbsp;/tmp/staging/usr/bin</span><br>
<span class="d">&nbsp;&nbsp;step &nbsp;2/14 &nbsp;OP_MKDIR &nbsp;&nbsp;/tmp/staging/etc/cogman/services</span><br>
<span class="d">&nbsp;&nbsp;step &nbsp;3/14 &nbsp;OP_EXEC &nbsp;&nbsp;&nbsp;./configure --prefix=/usr</span><br>
<span class="d">&nbsp;&nbsp;step &nbsp;4/14 &nbsp;OP_EXEC &nbsp;&nbsp;&nbsp;make -j$(nproc)</span><br>
<span class="d">&nbsp;&nbsp;step &nbsp;5/14 &nbsp;OP_EXEC &nbsp;&nbsp;&nbsp;make install DESTDIR=/tmp/staging</span><br>
<span class="d">&nbsp;&nbsp;step &nbsp;6/14 &nbsp;OP_COPY &nbsp;&nbsp;&nbsp;cogman-supervisor → /tmp/staging/usr/bin/</span><br>
<span class="d">&nbsp;&nbsp;step &nbsp;7/14 &nbsp;OP_COPY &nbsp;&nbsp;&nbsp;cogman-executor &nbsp;&nbsp;→ /tmp/staging/usr/bin/</span><br>
<span class="d">&nbsp;&nbsp;step &nbsp;8/14 &nbsp;OP_SYMLINK /tmp/staging/sbin/init → cogman-supervisor</span><br>
<span class="d">&nbsp;&nbsp;step &nbsp;9/14 &nbsp;OP_CHMOD &nbsp;&nbsp;/tmp/staging/usr/bin/cogman-supervisor 0755</span><br>
<span class="g">&nbsp;&nbsp;step 10/14 &nbsp;OP_COPY &nbsp;&nbsp;&nbsp;hello.service → /tmp/staging/etc/cogman/services/</span><br>
<span class="g">&nbsp;&nbsp;step 11/14 &nbsp;OP_COPY &nbsp;&nbsp;&nbsp;heartbeat.service → /tmp/staging/etc/cogman/services/</span><br>
<span class="g">&nbsp;&nbsp;step 12/14 &nbsp;OP_COPY &nbsp;&nbsp;&nbsp;ctl-probe.service → /tmp/staging/etc/cogman/services/</span><br>
<span class="g">&nbsp;&nbsp;step 13/14 &nbsp;OP_COPY &nbsp;&nbsp;&nbsp;shutdown.service  → /tmp/staging/etc/cogman/services/</span><br>
<span class="g">&nbsp;&nbsp;step 14/14 &nbsp;OP_EXEC &nbsp;&nbsp;&nbsp;mksquashfs /tmp/staging rootfs.sqsh</span><br>
<br>
<span class="g">&nbsp;&nbsp;✓&nbsp;&nbsp;all 14 steps completed &nbsp;exit=0</span><br>
<br>
<span class="p">void@rogue-linux:~$ </span><span class="s">ls -lh rootfs.sqsh</span><br>
<span class="s">-rw-r--r-- 1 void void 6.3M May 20 14:32 rootfs.sqsh</span><br>
<br>
<span class="p">void@rogue-linux:~$ </span><span style="display:inline-block;width:9px;height:15px;background:#4ecca3;vertical-align:-3px"></span>
</div>
</div>
</body></html>
""")

print("Batch 3 done.")
