#!/bin/bash
# Build a 3x2 grid montage of robot assembly videos for the website hero.
# Each cell is overlaid with its prompt / "Pre-designed X" label via drawtext.
# Inputs: 6 blurred 1280x720@30fps clips. Output: 1920x720 @ ~30s, web-optimized.

set -euo pipefail

SRC="/home/philip/Code/prompt2product.github.io/videos/brickmatic/blurred"
OUT="/home/philip/Code/prompt2product.github.io/videos/brickmatic/montage_hero.mp4"
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
DUR=30
START=2

# drawtext styling shared by all cells: centered near the bottom, white text on a
# semi-transparent black pill so it's readable over any background.
DT_COMMON="fontfile=${FONT}:fontcolor=white:fontsize=22:box=1:boxcolor=black@0.55:boxborderw=10:x=(w-text_w)/2:y=h-text_h-18"

ffmpeg -y \
  -ss $START -t $DUR -i "$SRC/brickmatic_elongated_guitar_gen3_10x_compressed_blurred.mp4" \
  -ss $START -t $DUR -i "$SRC/brickmatic_vessel_gen3_10x_compressed_blurred.mp4" \
  -ss $START -t $DUR -i "$SRC/brickmatic_sofa_gen3_10x_compressed_blurred.mp4" \
  -ss $START -t $DUR -i "$SRC/brickmatic_chair1_gen3_10x_compressed_blurred.mp4" \
  -ss $START -t $DUR -i "$SRC/brickmatic_fish_10x_compressed_blurred.mp4" \
  -ss $START -t $DUR -i "$SRC/brickmatic_faucet_gen3_10x_compressed_blurred.mp4" \
  -filter_complex "\
    [0:v]scale=640:360:force_original_aspect_ratio=increase,crop=640:360,setsar=1,drawtext=${DT_COMMON}:text='\"A guitar with elongated neck\"'[v0]; \
    [1:v]scale=640:360:force_original_aspect_ratio=increase,crop=640:360,setsar=1,drawtext=${DT_COMMON}:text='\"A streamlined vessel\"'[v1]; \
    [2:v]scale=640:360:force_original_aspect_ratio=increase,crop=640:360,setsar=1,drawtext=${DT_COMMON}:text='\"A soft leather sofa\"'[v2]; \
    [3:v]scale=640:360:force_original_aspect_ratio=increase,crop=640:360,setsar=1,drawtext=${DT_COMMON}:text='Pre-designed Chair'[v3]; \
    [4:v]scale=640:360:force_original_aspect_ratio=increase,crop=640:360,setsar=1,drawtext=${DT_COMMON}:text='Pre-designed Fish'[v4]; \
    [5:v]scale=640:360:force_original_aspect_ratio=increase,crop=640:360,setsar=1,drawtext=${DT_COMMON}:text='Pre-designed Faucet'[v5]; \
    [v0][v1][v2][v3][v4][v5]xstack=inputs=6:layout=0_0|w0_0|w0+w1_0|0_h0|w0_h0|w0+w1_h0[grid]" \
  -map "[grid]" \
  -c:v libx264 -profile:v main -level 4.0 -crf 26 -preset medium \
  -pix_fmt yuv420p -movflags +faststart -r 30 -an \
  "$OUT"

echo "Wrote: $OUT ($(du -h "$OUT" | cut -f1))"
