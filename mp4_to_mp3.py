#!/usr/bin/env python3

"""
Batch convert all .mp4 files in a folder to .mp3 and save into a download folder.

Default behavior writes output into a "download" directory inside the input folder.
You can override the output directory with --output.

Requires ffmpeg installed on the system.
macOS: brew install ffmpeg
Ubuntu/Debian: sudo apt-get install ffmpeg
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple
import shutil


def is_ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def convert_single_mp4_to_mp3(
    input_file: Path,
    output_file: Path,
    overwrite: bool = False,
    bitrate: str = "192k",
    vbr_quality: Optional[int] = None,
) -> Tuple[bool, str]:
    """Convert a single MP4 file to MP3 using ffmpeg.

    Returns (success, message).
    """
    if not input_file.exists():
        return False, f"Input file not found: {input_file}"

    if output_file.exists() and not overwrite:
        return True, f"Skipped (exists): {output_file}"

    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Build ffmpeg command
    # -vn: disable video
    # -acodec libmp3lame: encode audio to mp3
    # Use VBR if vbr_quality is provided (0=best ~245kbps, 2≈190kbps default), else CBR bitrate
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y" if overwrite else "-n",
        "-i",
        str(input_file),
        "-vn",
        "-acodec",
        "libmp3lame",
    ]
    if vbr_quality is not None:
        # Clamp to [0,9]
        q = max(0, min(9, int(vbr_quality)))
        cmd += ["-q:a", str(q)]
    else:
        cmd += ["-b:a", str(bitrate)]
    cmd += [str(output_file)]

    try:
        completed = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if completed.returncode == 0:
            return True, f"Converted: {input_file.name} -> {output_file.name}"
        # If -n (no overwrite) causes non-zero, treat as skip when file exists
        if "File '\"" in completed.stderr and "already exists" in completed.stderr:
            return True, f"Skipped (exists): {output_file}"
        return False, f"ffmpeg failed for {input_file.name}: {completed.stderr.strip()}"
    except FileNotFoundError:
        return False, "ffmpeg not found. Please install ffmpeg and try again."


def convert_mp4s_to_mp3s(
    input_dir: Path,
    output_dir: Optional[Path] = None,
    overwrite: bool = False,
    bitrate: str = "192k",
    vbr_quality: Optional[int] = None,
) -> Tuple[List[Path], List[Tuple[Path, str]]]:
    """Convert all .mp4 files under input_dir to .mp3 into output_dir.

    Returns (successful_outputs, failures_with_reason).
    """
    if not input_dir.exists() or not input_dir.is_dir():
        raise ValueError(f"Input directory not found or not a directory: {input_dir}")

    if output_dir is None:
        output_dir = input_dir / "download"

    mp4_files = [p for p in input_dir.iterdir() if p.is_file() and p.suffix.lower() == ".mp4"]

    successes: List[Path] = []
    failures: List[Tuple[Path, str]] = []

    for src in mp4_files:
        dst = output_dir / (src.stem + ".mp3")
        ok, msg = convert_single_mp4_to_mp3(
            src,
            dst,
            overwrite=overwrite,
            bitrate=bitrate,
            vbr_quality=vbr_quality,
        )
        print(msg)
        if ok:
            # Only count as success if file exists at the end
            if dst.exists():
                successes.append(dst)
            else:
                # Treat as failure if ffmpeg reported success but file missing
                failures.append((src, "Output file missing after conversion"))
        else:
            failures.append((src, msg))

    return successes, failures


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Batch convert all .mp4 files in a folder to .mp3 and save into a download folder."
        )
    )
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Path to the folder containing .mp4 files",
    )
    parser.add_argument(
        "--output",
        "-o",
        required=False,
        help="Output folder for .mp3 files (default: <input>/download)",
    )
    parser.add_argument(
        "--bitrate",
        "-b",
        default="192k",
        help="CBR 音频码率，如 128k, 192k, 256k (默认: 192k)。若指定 --vbr，将忽略此项",
    )
    parser.add_argument(
        "--vbr",
        type=int,
        default=None,
        help="使用 VBR 质量 (0-9，0最好体积最大，2常用≈190kbps)。设置后将忽略 --bitrate",
    )
    parser.add_argument(
        "--overwrite",
        "-y",
        action="store_true",
        help="Overwrite existing .mp3 files if they already exist",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    if not is_ffmpeg_available():
        print("❌ ffmpeg 未安装。请先安装 ffmpeg 后再运行。")
        print("macOS: brew install ffmpeg")
        print("Ubuntu/Debian: sudo apt-get install ffmpeg")
        return 2

    args = parse_args(argv)
    input_dir = Path(args.input).expanduser().resolve()
    output_dir = (
        Path(args.output).expanduser().resolve() if args.output else (input_dir / "download")
    )

    try:
        successes, failures = convert_mp4s_to_mp3s(
            input_dir=input_dir,
            output_dir=output_dir,
            overwrite=args.overwrite,
            bitrate=str(args.bitrate),
            vbr_quality=args.vbr,
        )
    except ValueError as e:
        print(f"❌ {e}")
        return 1

    print("")
    print(f"✅ 成功转换: {len(successes)} 个文件 → {output_dir}")
    if failures:
        print(f"⚠️ 失败/跳过: {len(failures)} 个文件")
        for src, reason in failures[:10]:
            print(f" - {src.name}: {reason}")
        if len(failures) > 10:
            print(f" ... 以及另外 {len(failures) - 10} 个")

    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())


