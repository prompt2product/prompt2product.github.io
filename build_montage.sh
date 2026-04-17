#!/bin/bash
# Build a 3x2 grid montage of robot assembly videos for the website hero.
# Inputs: 6 blurred 1280x720@30fps clips. Output: 1920x720 @ ~30s, web-optimized.

set -euo pipefail

SRC="/home/philip/Code/prompt2product.github.io/videos/brickmatic/blurred"
OUT="/home/philip/Code/prompt2product.github.io/videos/brickmatic/montage_hero.mp4"
DUR=30
START=2

ffmpeg -y \
  -ss $START -t $DUR -i "$SRC/brickmatic_elongated_guitar_gen3_10x_compressed_blurred.mp4" \
  -ss $START -t $DUR -i "$SRC/brickmatic_vessel_gen3_10x_compressed_blurred.mp4" \
  -ss $START -t $DUR -i "$SRC/brickmatic_sofa_gen3_10x_compressed_blurred.mp4" \
  -ss $START -t $DUR -i "$SRC/brickmatic_chair1_gen3_10x_compressed_blurred.mp4" \
  -ss $START -t $DUR -i "$SRC/brickmatic_fish_10x_compressed_blurred.mp4" \
  -ss $START -t $DUR -i "$SRC/brickmatic_faucet_gen3_10x_compressed_blurred.mp4" \
  -filter_complex "\
    [0:v]scale=640:360:force_original_aspect_ratio=increase,crop=640:360,setsar=1[v0]; \
    [1:v]scale=640:360:force_original_aspect_ratio=increase,crop=640:360,setsar=1[v1]; \
    [2:v]scale=640:360:force_original_aspect_ratio=increase,crop=640:360,setsar=1[v2]; \
    [3:v]scale=640:360:force_original_aspect_ratio=increase,crop=640:360,setsar=1[v3]; \
    [4:v]scale=640:360:force_original_aspect_ratio=increase,crop=640:360,setsar=1[v4]; \
    [5:v]scale=640:360:force_original_aspect_ratio=increase,crop=640:360,setsar=1[v5]; \
    [v0][v1][v2][v3][v4][v5]xstack=inputs=6:layout=0_0|w0_0|w0+w1_0|0_h0|w0_h0|w0+w1_h0[grid]" \
  -map "[grid]" \
  -c:v libx264 -profile:v main -level 4.0 -crf 26 -preset medium \
  -pix_fmt yuv420p -movflags +faststart -r 30 -an \
  "$OUT"

echo "Wrote: $OUT ($(du -h "$OUT" | cut -f1))"
