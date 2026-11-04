#!/usr/bin/env bash
# Encode rendered frames into the two episode recordings (6 fps, libx264).
set -euo pipefail
RUN_DIR="$1"
ffmpeg -y -framerate 6 -i "$RUN_DIR/frames_vertical/%06d.png" \
  -c:v libx264 -pix_fmt yuv420p -crf 20 \
  "$RUN_DIR/day_zero_vertical.mp4"
ffmpeg -y -framerate 6 -i "$RUN_DIR/frames_landscape/%06d.png" \
  -c:v libx264 -pix_fmt yuv420p -crf 20 \
  "$RUN_DIR/day_zero_landscape.mp4"
echo "wrote $RUN_DIR/day_zero_vertical.mp4 and day_zero_landscape.mp4"
