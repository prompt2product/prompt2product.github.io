#!/bin/bash
# Video preprocessing script for BrickMatic robot videos.
# This script will:
# 1. Speed up videos by 10x
# 2. Compress them for web viewing (reduce size)
# 3. Optimize for web streaming

# Set paths
INPUT_DIR="/home/philip/Code/prompt2product.github.io/robot_videos"
OUTPUT_DIR="/home/philip/Code/prompt2product.github.io/videos/brickmatic"

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "🎬 Processing BrickMatic robot videos for web viewing..."
echo "Input directory: $INPUT_DIR"
echo "Output directory: $OUTPUT_DIR"
echo "============================================================"

# Function to process a single video
process_video() {
    input_file="$1"
    filename=$(basename "$input_file" .mp4)
    output_file="$OUTPUT_DIR/brickmatic_${filename}_10x_compressed.mp4"
    
    echo "Processing: $filename"
    echo "  Input size: $(du -h "$input_file" | cut -f1)"
    
    # Process video with ffmpeg:
    # - Speed up 10x: setpts=0.1*PTS (video) 
    # - Compress: scale to max 720p, reduce bitrate
    # - Web optimization: fast start, H.264 baseline profile
    ffmpeg -i "$input_file" \
           -vf "setpts=0.1*PTS,scale='min(1280,iw)':'min(720,ih)':force_original_aspect_ratio=decrease" \
           -c:v libx264 -profile:v baseline -level 3.0 \
           -crf 28 \
           -preset fast \
           -movflags +faststart \
           -an \
           -y \
           "$output_file" \
           2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo "  ✅ Output size: $(du -h "$output_file" | cut -f1)"
        echo "  📁 Saved to: brickmatic_${filename}_10x_compressed.mp4"
    else
        echo "  ❌ Failed to process $filename"
    fi
    echo
}

# Process all MP4 files
for video_file in "$INPUT_DIR"/*.mp4; do
    if [ -f "$video_file" ]; then
        process_video "$video_file"
    fi
done

echo "🎉 Video processing complete!"
echo "📊 Summary:"
echo "Input directory total size: $(du -sh "$INPUT_DIR" | cut -f1)"
echo "Output directory total size: $(du -sh "$OUTPUT_DIR" 2>/dev/null | cut -f1 || echo '0B')"
echo "📂 Processed videos are in: $OUTPUT_DIR"
