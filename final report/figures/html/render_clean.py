"""
Render every HTML figure to a clean, tightly-cropped PNG.
Steps per figure:
  1. Chromium headless screenshot at 2× scale, large viewport (never clips)
  2. PIL auto-detects the actual content bounding box
  3. Crop to content + 48 px uniform padding
  4. Save final PNG to figures/
"""
import os, subprocess, sys
from PIL import Image, ImageChops

HTML_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR  = os.path.join(HTML_DIR, "..")
TMP_DIR  = "/tmp/fig_renders"
os.makedirs(TMP_DIR, exist_ok=True)

PAD = 48          # pixels of clean border around content (at 2× scale = 24 pt)
BG  = (248, 249, 250)   # #F8F9FA

figures = [
    # (html_file, output_png,                   win_w, win_h)
    ("fig1_1.html",  "fig1_1_build_pipeline.png",   2000, 800),
    ("fig1_2.html",  "fig1_2_runtime_arch.png",     2000, 1400),
    ("fig6_3.html",  "fig6_3_dfd_level0.png",       1600, 1200),
    ("fig6_4.html",  "fig6_4_dfd_level1.png",       2000, 1400),
    ("fig6_5.html",  "fig6_5_usecase_build.png",    1800, 1400),
    ("fig6_6.html",  "fig6_6_usecase_runtime.png",  1800, 1400),
    ("fig6_7.html",  "fig6_7_class_planner.png",    2000, 1400),
    ("fig6_8.html",  "fig6_8_class_supervisor.png", 2000, 1400),
    ("fig6_9.html",  "fig6_9_seq_build.png",        1600, 1400),
    ("fig6_10.html", "fig6_10_seq_start.png",       1800, 1400),
    ("fig6_11.html", "fig6_11_component.png",       2000, 1400),
    ("fig7_1.html",  "fig7_1_dep_graph.png",        1700, 1200),
    ("fig7_2.html",  "fig7_2_topo_sort.png",        1900, 1200),
    ("fig7_3.html",  "fig7_3_executor_loop.png",    1200, 2400),
    ("fig7_4.html",  "fig7_4_path_guard.png",       1700, 1400),
    ("fig7_5.html",  "fig7_5_sigchld.png",          1900, 1000),
    ("fig7_6.html",  "fig7_6_state_machine.png",    1700, 1200),
    ("fig7_7.html",  "fig7_7_ctl_protocol.png",     1800, 1200),
    ("fig7_8.html",  "fig7_8_messenger.png",        1900, 1200),
    ("fig7_9.html",  "fig7_9_rootfs_layout.png",    1800, 1200),
    ("fig8_1.html",  "fig8_1_boot_sequence.png",    2000, 1200),
    ("extra_dwm.html",      "extra_dwm_ui.png",      1920, 1080),
    ("extra_terminal.html", "extra_terminal.png",    1200, 1400),
]

def render_and_crop(html_file, out_png, win_w, win_h):
    html_path = os.path.join(HTML_DIR, html_file)
    tmp_png   = os.path.join(TMP_DIR, out_png)
    final_png = os.path.join(OUT_DIR, out_png)

    # ── 1. render ────────────────────────────────────────────────────────────
    cmd = [
        "chromium", "--headless=old",
        f"--screenshot={tmp_png}",
        f"--window-size={win_w},{win_h}",
        "--hide-scrollbars",
        "--force-device-scale-factor=2",
        "--disable-gpu",
        "--no-sandbox",
        f"file://{html_path}",
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=30)
    if not os.path.exists(tmp_png):
        print(f"  ERROR rendering {html_file}: {result.stderr[:200]}")
        return False

    # ── 2. auto-crop to content ───────────────────────────────────────────
    img = Image.open(tmp_png).convert("RGB")
    bg  = Image.new("RGB", img.size, BG)
    diff = ImageChops.difference(img, bg)

    # slight blur to ignore 1-px antialiasing artefacts on the bg
    from PIL import ImageFilter
    diff_b = diff.filter(ImageFilter.MaxFilter(3))
    bbox = diff_b.getbbox()

    if bbox is None:
        print(f"  WARN {html_file}: image appears blank, saving as-is")
        img.save(final_png, "PNG", optimize=True)
        return True

    x1, y1, x2, y2 = bbox
    W, H = img.size

    # add uniform padding, clamped to image bounds
    x1 = max(0,  x1 - PAD)
    y1 = max(0,  y1 - PAD)
    x2 = min(W,  x2 + PAD)
    y2 = min(H,  y2 + PAD)

    cropped = img.crop((x1, y1, x2, y2))

    # ── 3. save ───────────────────────────────────────────────────────────
    cropped.save(final_png, "PNG", optimize=True)
    cw, ch = cropped.size
    print(f"  ✓  {out_png:<42} {cw}×{ch} px")
    return True

print("Rendering and cropping all figures …\n")
ok = 0
for args in figures:
    if render_and_crop(*args):
        ok += 1

print(f"\nDone — {ok}/{len(figures)} figures rendered cleanly.")
print(f"Output: {os.path.abspath(OUT_DIR)}")
