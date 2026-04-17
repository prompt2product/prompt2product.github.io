#!/usr/bin/env python3
"""Batch face anonymization for Brickmatic videos using deface's CenterFace model."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Iterable, List, Optional, Tuple

import imageio
from deface.deface import CenterFace, video_detect


VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Detect faces with CenterFace (via deface) and anonymize them in video files."
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="videos/brickmatic",
        help="Input video file or directory (default: videos/brickmatic)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory to write anonymized videos. Defaults to <input>/blurred.",
    )
    parser.add_argument(
        "--suffix",
        type=str,
        default="_blurred",
        help="Suffix added before extension when writing outputs alongside the source (default: _blurred).",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.2,
        help="CenterFace detection threshold (lower catches more faces, default: 0.2).",
    )
    parser.add_argument(
        "--mask-scale",
        type=float,
        default=1.3,
        help="Scale factor for anonymization masks (default: 1.3).",
    )
    parser.add_argument(
        "--replacewith",
        choices=["blur", "solid", "none", "img", "mosaic"],
        default="blur",
        help="Anonymization mode (default: blur).",
    )
    parser.add_argument(
        "--replace-img",
        type=str,
        default="replace_img.png",
        help="Path to replacement image when --replacewith img is used.",
    )
    parser.add_argument(
        "--mosaic-size",
        type=int,
        default=20,
        help="Pixel size for mosaic anonymization (default: 20).",
    )
    parser.add_argument(
        "--keep-audio",
        action="store_true",
        help="Copy the original audio track into the anonymized video.",
    )
    parser.add_argument(
        "--ffmpeg-config",
        type=str,
        default='{"codec": "libx264"}',
        help="JSON dict with additional FFMPEG writer options (default: '{\"codec\": \"libx264\"}').",
    )
    parser.add_argument(
        "--backend",
        choices=["auto", "onnxrt", "opencv"],
        default="auto",
        help="Execution backend for CenterFace (default: auto).",
    )
    parser.add_argument(
        "--execution-provider",
        type=str,
        default=None,
        help="Override ONNX Runtime execution provider (if backend=onnxrt).",
    )
    parser.add_argument(
        "--scale",
        type=str,
        default=None,
        help="Inference resolution bound as WxH (e.g. 640x360) to speed up processing.",
    )
    parser.add_argument(
        "--use-boxes",
        action="store_true",
        help="Use rectangular masks instead of ellipses.",
    )
    parser.add_argument(
        "--draw-scores",
        action="store_true",
        help="Overlay detection confidence scores on the output video.",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Open a live preview window while processing (can slow things down).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing outputs instead of skipping them.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging for troubleshooting.",
    )
    return parser.parse_args()


def iter_videos(directory: Path) -> Iterable[Path]:
    for path in sorted(directory.rglob("*")):
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS:
            yield path


def collect_videos(path: Path) -> List[Path]:
    if path.is_dir():
        return list(iter_videos(path))
    if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS:
        return [path]
    return []


def prepare_output_dir(input_path: Path, args: argparse.Namespace) -> Path:
    if args.output_dir:
        return Path(args.output_dir).expanduser().resolve()
    base = input_path if input_path.is_dir() else input_path.parent
    return base / "blurred"


def prepare_output_path(video_path: Path, output_dir: Path, suffix: str) -> Path:
    filename = (
        f"{video_path.stem}{suffix}{video_path.suffix}"
        if suffix
        else video_path.name
    )
    return output_dir / filename


def parse_scale(scale: Optional[str]) -> Optional[Tuple[int, int]]:
    if not scale:
        return None
    try:
        width_str, height_str = scale.lower().split("x")
        return int(width_str), int(height_str)
    except Exception as exc:
        raise ValueError(f"Invalid scale format '{scale}'. Expected WxH like 640x360.") from exc


def parse_ffmpeg_config(raw: str) -> dict:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON for --ffmpeg-config: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("--ffmpeg-config must decode to a JSON object.")
    return data


def load_replace_image(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"Replacement image '{path}' not found.")
    return imageio.imread(path)


def process_video(
    video_path: Path,
    output_path: Path,
    centerface: CenterFace,
    args: argparse.Namespace,
    ffmpeg_config: dict,
    replace_image,
    nested: bool,
) -> bool:
    if output_path.exists():
        if not args.overwrite:
            logging.info("Skipping %s (exists)", output_path)
            return True
        output_path.unlink()

    output_path.parent.mkdir(parents=True, exist_ok=True)

    logging.info("Anonymizing %s -> %s", video_path, output_path)

    try:
        video_detect(
            ipath=str(video_path),
            opath=str(output_path),
            centerface=centerface,
            threshold=args.threshold,
            enable_preview=args.preview,
            cam=False,
            nested=nested,
            replacewith=args.replacewith,
            mask_scale=args.mask_scale,
            ellipse=not args.use_boxes,
            draw_scores=args.draw_scores,
            ffmpeg_config=ffmpeg_config,
            replaceimg=replace_image,
            keep_audio=args.keep_audio,
            mosaicsize=args.mosaic_size,
        )
    except Exception:
        logging.exception("Failed to anonymize %s", video_path)
        return False

    return True


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(message)s",
    )

    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        logging.error("Input path %s does not exist", input_path)
        return 1

    output_dir = prepare_output_dir(input_path, args).resolve()

    try:
        ffmpeg_config = parse_ffmpeg_config(args.ffmpeg_config)
    except ValueError as exc:
        logging.error(exc)
        return 1

    try:
        in_shape = parse_scale(args.scale)
    except ValueError as exc:
        logging.error(exc)
        return 1

    replace_image = None
    if args.replacewith == "img":
        try:
            replace_image = load_replace_image(Path(args.replace_img).expanduser())
        except FileNotFoundError as exc:
            logging.error(exc)
            return 1

    try:
        centerface = CenterFace(
            in_shape=in_shape,
            backend=args.backend,
            override_execution_provider=args.execution_provider,
        )
    except Exception:
        logging.exception("Failed to initialize CenterFace model")
        return 1

    videos = collect_videos(input_path)
    if not videos:
        logging.warning("No supported videos found in %s", input_path)
        return 0

    multi_file = len(videos) > 1
    success = True
    for video_path in videos:
        output_path = prepare_output_path(video_path, output_dir, args.suffix)
        ok = process_video(
            video_path=video_path,
            output_path=output_path,
            centerface=centerface,
            args=args,
            ffmpeg_config=ffmpeg_config,
            replace_image=replace_image,
            nested=multi_file,
        )
        success = success and ok

    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
