#!/usr/bin/env python3
"""
generate_video_index.py
Generate a JSON manifest of video files in a directory. Uses ffprobe (if available) to read duration.

Usage:
  python scripts/generate_video_index.py "path/to/videos"

Produces: index.json inside the provided directory with entries:
  [{"filename":..., "relpath":..., "mtime":..., "start_iso":..., "duration":...}, ...]

If ffprobe is not available, duration will be null and mtime will be used as a fallback start time.
"""
import sys
import json
from pathlib import Path
import subprocess
import shutil
import argparse
import datetime


def get_duration_seconds(path: Path, ffprobe_cmd: str | None):
    """Return duration in seconds using ffprobe, or None if not available.

    ffprobe_cmd may be an absolute path to ffprobe or the command name found on PATH.
    If ffprobe_cmd is None the function will return None.
    """
    if not ffprobe_cmd:
        return None
    try:
        cmd = [ffprobe_cmd, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        out = res.stdout.strip()
        if not out:
            return None
        return float(out)
    except Exception:
        return None


def generate_index(videos_dir: Path, ffprobe_cmd: str | None = None):
    # Index MP4 files as the source of truth (converted from MOVs)
    # This ensures we're using the browser-compatible encoded files
    files = sorted([p for p in videos_dir.iterdir() if p.is_file() and p.suffix.lower() == '.mp4'])
    items = []
    for p in files:
        # Try to get original MOV timestamp if it exists, otherwise use MP4 timestamp
        mov_file = p.with_suffix('.MOV')
        if mov_file.exists():
            # Use original MOV file timestamp for accurate timeline positioning
            mtime = mov_file.stat().st_mtime
            print(f"Using original MOV timestamp for {p.name}: {mov_file.name}")
        else:
            # Fallback to MP4 timestamp if MOV doesn't exist
            mtime = p.stat().st_mtime
            print(f"Using MP4 timestamp for {p.name} (no MOV found)")
        
        start_iso = datetime.datetime.fromtimestamp(mtime).isoformat()
        duration = get_duration_seconds(p, ffprobe_cmd)
        items.append({
            'filename': p.name,
            'relpath': p.name,
            'mtime': mtime,
            'start_iso': start_iso,
            'duration': duration
        })
    out = {'generated_at': datetime.datetime.utcnow().isoformat()+'Z', 'videos': items}
    target = videos_dir / 'index.json'
    with target.open('w', encoding='utf-8') as f:
        json.dump(out, f, indent=2)
    print(f'Wrote {target} with {len(items)} entries')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate video index (probe MP4 durations using ffprobe).')
    parser.add_argument('videos_dir', help='Path to the videos directory')
    parser.add_argument('--ffprobe', help='Path to ffprobe executable (optional). If omitted, the script will try to find ffprobe on PATH.')
    args = parser.parse_args()
    videos_dir = Path(args.videos_dir)
    if not videos_dir.exists() or not videos_dir.is_dir():
        print('Directory not found:', videos_dir)
        sys.exit(1)

    ffprobe_cmd = None
    if args.ffprobe:
        ffprobe_cmd = args.ffprobe
    else:
        # try to find ffprobe on PATH
        ffprobe_cmd = shutil.which('ffprobe')

    if not ffprobe_cmd:
        print('Warning: ffprobe not found on PATH and --ffprobe not provided. Durations will be left null.')
    else:
        print(f'Using ffprobe: {ffprobe_cmd}')

    generate_index(videos_dir, ffprobe_cmd=ffprobe_cmd)
