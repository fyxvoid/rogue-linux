#!/bin/bash
# Render all HTML figures to PNG with Chromium headless
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
OUT="$DIR/.."

render() {
  local html="$1" png="$2" w="${3:-1500}" h="${4:-900}"
  chromium --headless=old \
    --screenshot="$OUT/$png" \
    --window-size="${w},${h}" \
    --hide-scrollbars \
    --force-device-scale-factor=2 \
    "file://$DIR/$html" 2>/dev/null
  echo "  saved $png"
}

echo "Rendering all figures..."

render fig1_1.html  fig1_1_build_pipeline.png  1520 320
render fig1_2.html  fig1_2_runtime_arch.png    1520 820
render fig6_3.html  fig6_3_dfd_level0.png      1200 780
render fig6_4.html  fig6_4_dfd_level1.png      1520 820
render fig6_5.html  fig6_5_usecase_build.png   1400 820
render fig6_6.html  fig6_6_usecase_runtime.png 1400 820
render fig6_7.html  fig6_7_class_planner.png   1600 900
render fig6_8.html  fig6_8_class_supervisor.png 1600 820
render fig6_9.html  fig6_9_seq_build.png       1520 960
render fig6_10.html fig6_10_seq_start.png      1620 960
render fig6_11.html fig6_11_component.png      1520 860
render fig7_1.html  fig7_1_dep_graph.png       1300 820
render fig7_2.html  fig7_2_topo_sort.png       1400 780
render fig7_3.html  fig7_3_executor_loop.png   1000 1100
render fig7_4.html  fig7_4_path_guard.png      1300 860
render fig7_5.html  fig7_5_sigchld.png         1500 740
render fig7_6.html  fig7_6_state_machine.png   1500 840
render fig7_7.html  fig7_7_ctl_protocol.png    1400 820
render fig7_8.html  fig7_8_messenger.png       1500 820
render fig7_9.html  fig7_9_rootfs_layout.png   1400 860
render fig8_1.html  fig8_1_boot_sequence.png   1520 820
render extra_dwm.html   extra_dwm_ui.png       1920 1080
render extra_terminal.html extra_terminal.png  1200 860

echo "Done — all figures in $OUT"
