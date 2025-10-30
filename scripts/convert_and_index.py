#!/usr/bin/env python3
"""
Convert MOV files to MP4 (preserving timestamps) and generate video index.

This script supports both single-user and multi-user concert structures:

SINGLE USER STRUCTURE:
  concert/concerts/Concert Name/videos/
  ├── video1.mov → video1.mp4
  ├── video2.mov → video2.mp4
  ├── index.json (generated)
  └── processed/ (MOVs moved here)

MULTI-USER STRUCTURE:
  concert/concerts/Concert Name/
  ├── manifest.json (master manifest, generated)
  └── videos/
      ├── pelham/
      │   ├── video1.mov → video1.mp4
      │   ├── index.json (generated)
      │   └── processed/ (user's MOVs moved here)
      ├── sophia/
      │   ├── video2.mov → video2.mp4
      │   ├── index.json (generated)
      │   └── processed/ (user's MOVs moved here)
      └── ethan/
          ├── video3.mov → video3.mp4
          ├── index.json (generated)
          └── processed/ (user's MOVs moved here)

This script:
1. Converts .MOV files to .mp4 with Firefox-compatible encoding
2. Preserves original MOV timestamps on the MP4 files
3. Generates individual index.json files for each user/directory
4. Generates master manifest.json for multi-user concerts
5. Optionally moves MOV files to user-specific processed/ folders

Usage Examples:
  # Process all concerts (convert + index + cleanup)
  python scripts/convert_and_index.py --root "concert/concerts" --move-processed

  # Process specific concert (works with both single and multi-user)
  python scripts/convert_and_index.py --root "concert/concerts/9-19-25 Chris Stussy Chicago at Radius/videos" --move-processed

  # Process specific user within a concert
  python scripts/convert_and_index.py --root "concert/concerts/9-19-25 Chris Stussy Chicago at Radius/videos/pelham" --move-processed

  # Just move existing MOVs without conversion (if MP4s already exist)
  python scripts/convert_and_index.py --root "concert/concerts" --move-processed

  # Force overwrite existing MP4s and move MOVs
  python scripts/convert_and_index.py --root "concert/concerts" --force --move-processed

  # Test what would happen (dry run)
  python scripts/convert_and_index.py --root "concert/concerts" --move-processed --dry-run

  # Convert with higher quality (lower CRF = better quality, larger files)
  python scripts/convert_and_index.py --root "concert/concerts" --crf 22 --move-processed

  # Convert with lower quality (higher CRF = smaller files)
  python scripts/convert_and_index.py --root "concert/concerts" --crf 28 --move-processed

  # Just convert and index (don't move MOVs)
  python scripts/convert_and_index.py --root "concert/concerts"

Default root is `concert/concerts`.
"""
import argparse
import os
import shutil
import subprocess
import sys
import json
import datetime
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


def find_ffprobe():
    ffprobe = shutil.which('ffprobe')
    if ffprobe:
        return ffprobe
    # Try same locations as ffmpeg
    user = os.environ.get('USERPROFILE') or os.path.expanduser('~')
    search_root = os.path.join(user, 'AppData', 'Local', 'Microsoft', 'WinGet', 'Packages')
    if os.path.isdir(search_root):
        for d in os.listdir(search_root):
            if 'ffmpeg' in d.lower() or 'gyan.ffmpeg' in d.lower():
                candidate = os.path.join(search_root, d)
                for root, dirs, files in os.walk(candidate):
                    for fname in files:
                        if fname.lower() == 'ffprobe.exe':
                            return os.path.join(root, fname)
    return None


def get_duration_seconds(path: Path, ffprobe_cmd: str | None):
    """Return duration in seconds using ffprobe, or None if not available."""
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


def convert_file(ffmpeg, src: Path, dst: Path, preset='fast', crf='26', move_to_processed=False):
    """Convert MOV to MP4 with Firefox-compatible encoding and preserve timestamp."""
    # Get original timestamp before conversion
    original_stat = src.stat()
    original_mtime = original_stat.st_mtime
    original_atime = original_stat.st_atime
    
    # Force 8-bit encoding for Firefox compatibility
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
    print(f'Converting: {src.name} -> {dst.name}')
    try:
        proc = subprocess.run(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True, 
            timeout=600,  # 10 minutes per file
            check=False
        )
        
        success = proc.returncode == 0
        if success:
            # Preserve original timestamp on the MP4 file
            os.utime(dst, (original_atime, original_mtime))
            print(f'✓ Successfully converted {src.name} (timestamp preserved)')
        else:
            print(f'✗ Failed to convert {src.name} (exit code: {proc.returncode})')
            if proc.stdout:
                print(f'Error output: {proc.stdout[:300]}...' if len(proc.stdout) > 300 else proc.stdout)
        
        return success
    except subprocess.TimeoutExpired:
        print(f'✗ Conversion timed out for {src.name}')
        return False
    except Exception as e:
        print(f'✗ Conversion error for {src.name}: {e}')
        return False


def generate_index(videos_dir: Path, ffprobe_cmd: str | None = None):
    """Generate index.json from MP4 files with preserved timestamps."""
    print(f'\n=== Generating index for {videos_dir} ===')
    
    files = sorted([p for p in videos_dir.iterdir() if p.is_file() and p.suffix.lower() == '.mp4'])
    if not files:
        print('No MP4 files found for indexing')
        return False
    
    items = []
    for p in files:
        mtime = p.stat().st_mtime
        start_iso = datetime.datetime.fromtimestamp(mtime).isoformat()
        duration = get_duration_seconds(p, ffprobe_cmd)
        items.append({
            'filename': p.name,
            'relpath': p.name,
            'mtime': mtime,
            'start_iso': start_iso,
            'duration': duration
        })
    
    out = {'generated_at': datetime.datetime.now(datetime.timezone.utc).isoformat()+'Z', 'videos': items}
    target = videos_dir / 'index.json'
    with target.open('w', encoding='utf-8') as f:
        json.dump(out, f, indent=2)
    print(f'✓ Wrote {target} with {len(items)} entries')
    return True


def generate_master_manifest(concert_dir: Path, user_dirs: list):
    """Generate a master manifest that references all user video directories."""
    print(f'\n=== Generating master manifest for {concert_dir} ===')
    
    users = []
    all_videos = []  # Collect all videos across users for coverage calculation
    user_videos_map = {}  # Map username -> list of their videos
    
    for user_dir in user_dirs:
        username = user_dir.name
        index_path = user_dir / 'index.json'
        
        if index_path.exists():
            # Try to get display name from users.csv or use username
            display_name = username.title()  # Default to capitalized username
            
            users.append({
                'username': username,
                'displayName': display_name,
                'manifestPath': f'./videos/{username}/index.json'
            })
            
            # Load and collect video data for coverage calculation
            try:
                with index_path.open('r', encoding='utf-8') as f:
                    user_index = json.load(f)
                    user_videos = user_index.get('videos', [])
                    user_videos_map[username] = user_videos
                    if user_videos:
                        all_videos.extend(user_videos)
            except Exception as e:
                print(f'Warning: Could not read {index_path}: {e}')
    
    if not users:
        print('No user directories with indexes found')
        return False
    
    # Calculate video coverage from first to last video across all users
    coverage = None
    if all_videos:
        # Filter videos with valid timestamps and durations
        valid_videos = [v for v in all_videos if 'mtime' in v and 'duration' in v and v['duration'] is not None]
        
        if valid_videos:
            # Find earliest start time and latest end time
            earliest_start = min(v['mtime'] for v in valid_videos)
            latest_video = max(valid_videos, key=lambda v: v['mtime'] + v['duration'])
            latest_end = latest_video['mtime'] + latest_video['duration']
            
            # Calculate total show duration (time span)
            total_show_duration_seconds = latest_end - earliest_start
            
            # Calculate total video content duration (sum of all video durations)
            total_video_content_seconds = sum(v['duration'] for v in valid_videos)
            
            # Calculate coverage percentage
            coverage_percentage = (total_video_content_seconds / total_show_duration_seconds * 100) if total_show_duration_seconds > 0 else 0
            
            # Convert durations to human-readable format
            def format_duration(seconds):
                hours = int(seconds // 3600)
                minutes = int((seconds % 3600) // 60)
                secs = int(seconds % 60)
                return f"{hours:02d}:{minutes:02d}:{secs:02d}"
            
            coverage = {
                'show_duration_seconds': total_show_duration_seconds,
                'show_duration_formatted': format_duration(total_show_duration_seconds),
                'video_content_seconds': total_video_content_seconds,
                'video_content_formatted': format_duration(total_video_content_seconds),
                'coverage_percentage': round(coverage_percentage, 1),
                'earliest_video_start': datetime.datetime.fromtimestamp(earliest_start).isoformat(),
                'latest_video_end': datetime.datetime.fromtimestamp(latest_end).isoformat(),
                'total_videos': len(valid_videos),
                'users_with_videos': len([u for u in users if any(v.get('mtime') for v in user_videos_map.get(u['username'], []))])
            }
            
            print(f'✓ Calculated coverage: {coverage["show_duration_formatted"]} show duration, {coverage["video_content_formatted"]} video content ({coverage["coverage_percentage"]}% coverage, {len(valid_videos)} videos)')
    
    # Extract concert name from directory
    concert_name = concert_dir.name
    
    master_manifest = {
        'concert': concert_name,
        'generated_at': datetime.datetime.now(datetime.timezone.utc).isoformat()+'Z',
        'users': users
    }
    
    # Add coverage data if available
    if coverage:
        master_manifest['coverage'] = coverage
    
    target = concert_dir / 'manifest.json'
    with target.open('w', encoding='utf-8') as f:
        json.dump(master_manifest, f, indent=2)
    
    print(f'✓ Wrote master manifest {target} with {len(users)} users')
    if coverage:
        print(f'✓ Show coverage: {coverage["show_duration_formatted"]} total span')
        print(f'✓ Video content: {coverage["video_content_formatted"]} actual footage ({coverage["coverage_percentage"]}% of show)')
        print(f'✓ Time span: {coverage["earliest_video_start"]} to {coverage["latest_video_end"]}')
    return True


def move_movs_to_processed(videos_dir: Path, dry_run=False):
    """Move all MOV files to processed/ subfolder."""
    print(f'\n=== Moving MOV files to processed folder ===')
    
    movs = [p for p in videos_dir.iterdir() if p.is_file() and p.suffix.lower() == '.mov']
    if not movs:
        print('No MOV files found to move')
        return
    
    processed_dir = videos_dir / 'processed'
    if not dry_run:
        processed_dir.mkdir(exist_ok=True)
    
    moved_count = 0
    for mov in movs:
        processed_path = processed_dir / mov.name
        
        # Handle naming conflicts in processed folder
        counter = 1
        while processed_path.exists():
            stem = mov.stem
            suffix = mov.suffix
            processed_path = processed_dir / f"{stem}_{counter}{suffix}"
            counter += 1
        
        if dry_run:
            print(f'Would move: {mov.name} -> processed/{processed_path.name}')
            moved_count += 1
        else:
            try:
                shutil.move(str(mov), str(processed_path))
                print(f'✓ Moved {mov.name} -> processed/{processed_path.name}')
                moved_count += 1
            except Exception as e:
                print(f'✗ Failed to move {mov.name}: {e}')
    
    print(f'Move summary: {moved_count}/{len(movs)} files moved')


def process_directory(videos_dir: Path, ffmpeg_cmd: str, ffprobe_cmd: str, args):
    """Process a single videos directory: convert MOVs, generate index, and optionally move files."""
    print(f'\n{"="*60}')
    print(f'Processing: {videos_dir}')
    print(f'{"="*60}')
    
    # STEP 1: Convert MOV files to MP4
    print(f'\n--- STEP 1: CONVERSION ---')
    movs = [p for p in videos_dir.iterdir() if p.is_file() and p.suffix.lower() == '.mov']
    if not movs:
        print('No MOV files found in this directory')
    else:
        print(f'Found {len(movs)} MOV files')
        
        to_convert = []
        for mov in movs:
            mp4 = mov.with_suffix('.mp4')
            if mp4.exists() and not args.force:
                print(f'Skipping {mov.name} (MP4 exists, use --force to overwrite)')
            else:
                to_convert.append((mov, mp4))
        
        if to_convert:
            print(f'Converting {len(to_convert)} files...')
            success_count = 0
            for i, (src, dst) in enumerate(to_convert, 1):
                print(f'\n--- Converting {i}/{len(to_convert)} ---')
                if args.dry_run:
                    print(f'Would convert: {src} -> {dst}')
                    success_count += 1
                else:
                    if convert_file(ffmpeg_cmd, src, dst, preset=args.preset, crf=args.crf, move_to_processed=False):
                        success_count += 1
            
            print(f'\nConversion summary: {success_count}/{len(to_convert)} successful')
        else:
            print('No files need conversion')
    
    # STEP 2: Generate index from MP4 files
    print(f'\n--- STEP 2: INDEXING ---')
    if not args.dry_run:
        generate_index(videos_dir, ffprobe_cmd)
    else:
        print('Would generate index.json from MP4 files')
    
    # STEP 3: Move MOV files to processed folder (if requested)
    if args.move_processed:
        print(f'\n--- STEP 3: CLEANUP ---')
        move_movs_to_processed(videos_dir, dry_run=args.dry_run)
    else:
        print(f'\n--- STEP 3: CLEANUP (SKIPPED) ---')
        print('Use --move-processed to move MOV files to processed/ folder')


def main():
    parser = argparse.ArgumentParser(description='Convert MOVs to MP4s and generate video index')
    parser.add_argument('--root', '-r', default='concert/concerts', help='Root folder to scan for videos directories')
    parser.add_argument('--dry-run', action='store_true', help="Don't run conversion, only show what would be done")
    parser.add_argument('--force', action='store_true', help='Overwrite existing MP4 files')
    parser.add_argument('--move-processed', action='store_true', help='Move MOV files to processed/ subfolder after successful conversion')
    parser.add_argument('--preset', default='fast', help='ffmpeg preset (default: fast)')
    parser.add_argument('--crf', default='26', help='ffmpeg CRF quality (default: 26, lower=higher quality)')
    args = parser.parse_args()

    root = Path(args.root)
    if not root.exists():
        print(f'Root path does not exist: {root}')
        sys.exit(2)

    # Find required tools
    if not args.dry_run:
        ffmpeg_cmd = find_ffmpeg()
        if not ffmpeg_cmd:
            print('ffmpeg not found in PATH or common locations. Install ffmpeg or add to PATH.')
            sys.exit(3)
        print(f'Using ffmpeg: {ffmpeg_cmd}')
        
        ffprobe_cmd = find_ffprobe()
        if not ffprobe_cmd:
            print('Warning: ffprobe not found. Durations will be left null.')
        else:
            print(f'Using ffprobe: {ffprobe_cmd}')
    else:
        ffmpeg_cmd = ffprobe_cmd = None

    # Find all videos directories (including user subdirectories)
    videos_dirs = []
    concert_dirs = []  # Track concert directories for master manifests
    
    if root.name == 'videos' and root.is_dir():
        # Direct videos directory - check if it has user subdirectories
        user_subdirs = [d for d in root.iterdir() if d.is_dir() and not d.name == 'processed']
        if user_subdirs:
            # This is a multi-user videos directory
            videos_dirs.extend(user_subdirs)
            concert_dirs.append(root.parent)  # Concert directory is parent of videos
        else:
            # Single user videos directory
            videos_dirs.append(root)
    else:
        # Search for videos subdirectories
        for item in root.rglob('videos'):
            if item.is_dir():
                # Check if this videos directory has user subdirectories
                user_subdirs = [d for d in item.iterdir() if d.is_dir() and not d.name == 'processed']
                if user_subdirs:
                    # Multi-user structure: process each user directory
                    videos_dirs.extend(user_subdirs)
                    concert_dirs.append(item.parent)  # Concert directory
                else:
                    # Single user structure: process the videos directory directly
                    videos_dirs.append(item)
    
    if not videos_dirs:
        print(f'No videos directories found under {root}')
        sys.exit(1)
    
    print(f'Found {len(videos_dirs)} videos directories')
    
    # Process each directory
    processed_concerts = set()
    for videos_dir in videos_dirs:
        try:
            process_directory(videos_dir, ffmpeg_cmd, ffprobe_cmd, args)
            
            # Track which concert this belongs to for master manifest generation
            if videos_dir.parent.name == 'videos':
                # This is a user directory inside a videos folder
                concert_dir = videos_dir.parent.parent
                processed_concerts.add(concert_dir)
            
        except KeyboardInterrupt:
            print('\nInterrupted by user')
            sys.exit(130)
        except Exception as e:
            print(f'Error processing {videos_dir}: {e}')
            continue
    
    # Generate master manifests for multi-user concerts
    for concert_dir in processed_concerts:
        if not args.dry_run:
            try:
                videos_main_dir = concert_dir / 'videos'
                user_dirs = [d for d in videos_main_dir.iterdir() if d.is_dir() and not d.name == 'processed']
                generate_master_manifest(concert_dir, user_dirs)
            except Exception as e:
                print(f'Error generating master manifest for {concert_dir}: {e}')
        else:
            print(f'Would generate master manifest for {concert_dir.name}')
    
    print(f'\n{"="*60}')
    print('ALL PROCESSING COMPLETE')
    print(f'{"="*60}')


if __name__ == '__main__':
    main()