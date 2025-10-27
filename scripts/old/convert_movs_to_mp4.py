#!/usr/bin/env python3
"""Batch convert .MOV files to .mp4 (H.264 + AAC) when a sibling .mp4 doesn't exist.

Usage:
  python scripts/convert_movs_to_mp4.py --root "concert/concerts"

Default root is `concert/concerts`.
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def find_ffmpeg():
    ffmpeg = shutil.which('ffmpeg')
    if ffmpeg:
        return ffmpeg
    # common WinGet extraction path pattern
    user = os.environ.get('USERPROFILE') or os.path.expanduser('~')
    search_root = os.path.join(user, 'AppData', 'Local', 'Microsoft', 'WinGet', 'Packages')
    if os.path.isdir(search_root):
        for d in os.listdir(search_root):
            if 'ffmpeg' in d.lower() or 'gyan.ffmpeg' in d.lower():
                candidate = os.path.join(search_root, d)
                for root, dirs, files in os.walk(candidate):
                    for fname in files:
                        if fname.lower() == 'ffmpeg.exe':
                            return os.path.join(root, fname)
    return None


def convert_file(ffmpeg, src: Path, dst: Path, preset='fast', crf='22'):
    # Force 8-bit encoding for Firefox compatibility by using profile:v baseline or main
    # and pix_fmt yuv420p to ensure 8-bit color depth instead of 10-bit
    cmd = [
        ffmpeg, '-y', '-i', str(src), 
        '-c:v', 'libx264', 
        '-preset', preset, 
        '-crf', crf,
        '-profile:v', 'high',  # Force High profile (not High 10)
        '-pix_fmt', 'yuv420p',  # Force 8-bit color (YUV 4:2:0)
        '-level', '4.0',  # Force level 4.0 for better compatibility
        '-c:a', 'aac', 
        '-b:a', '128k', 
        str(dst)
    ]
    print(f'Converting: {src} -> {dst}')
    print(f'Command: {" ".join(cmd)}')
    try:
        proc = subprocess.run(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True, 
            timeout=600,  # Reduced timeout to 10 minutes per file
            check=False  # Don't raise exception on non-zero exit
        )
        if proc.stdout:
            print(f'ffmpeg output: {proc.stdout[:500]}...' if len(proc.stdout) > 500 else f'ffmpeg output: {proc.stdout}')
        
        success = proc.returncode == 0
        print(f'Conversion {"SUCCESS" if success else "FAILED"} for {src.name} (exit code: {proc.returncode})')
        return success
    except subprocess.TimeoutExpired:
        print(f'Conversion timed out for {src}')
        return False
    except Exception as e:
        print(f'Conversion error for {src}: {e}')
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', '-r', default='concert/concerts', help='Root folder to scan for MOVs')
    parser.add_argument('--dry-run', action='store_true', help="Don't run ffmpeg, only show what would be converted")
    parser.add_argument('--preset', default='fast')
    parser.add_argument('--crf', default='22')
    args = parser.parse_args()

    root = Path(args.root)
    if not root.exists():
        print('Root path does not exist:', root)
        sys.exit(2)

    ffmpeg = None if args.dry_run else find_ffmpeg()
    if not args.dry_run and not ffmpeg:
        print('ffmpeg not found in PATH or common locations. Install ffmpeg or add to PATH.')
        sys.exit(3)

    movs = list(root.rglob('*.MOV')) + list(root.rglob('*.mov'))
    print(f'Found {len(movs)} MOV files under {root}')

    to_convert = []
    for m in movs:
        mp4 = m.with_suffix('.mp4')
        if mp4.exists():
            print('Skipping (mp4 exists):', m)
            continue
        to_convert.append((m, mp4))

    print(f'{len(to_convert)} files to convert')
    if len(to_convert) == 0:
        print('No files to convert. Exiting.')
        return

    success = []
    failed = []
    for i, (src, dst) in enumerate(to_convert, 1):
        print(f'\n=== Processing {i}/{len(to_convert)}: {src.name} ===')
        if args.dry_run:
            print('Would convert:', src, '->', dst)
            success.append((src, dst))
            continue

        ok = convert_file(ffmpeg, src, dst, preset=args.preset, crf=args.crf)
        if ok:
            success.append((src, dst))
            print(f'✓ Successfully converted {src.name}')
        else:
            failed.append((src, dst))
            print(f'✗ Failed to convert {src.name}')

    print(f'\n{"="*50}')
    print('CONVERSION COMPLETE')
    print(f'{"="*50}')
    print(f'Total files processed: {len(to_convert)}')
    print(f'Successful: {len(success)}')
    print(f'Failed: {len(failed)}')
    
    if failed:
        print('\nFailed files:')
        for s, d in failed:
            print(f'  - {s.name}')
    
    print('\nScript finished. Exiting.')
    sys.exit(0 if len(failed) == 0 else 1)


if __name__ == '__main__':
    main()
