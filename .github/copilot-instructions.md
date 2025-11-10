# VSCoding Project Instructions

## Project Overview
This workspace contains multiple Python projects and a concert video platform:

### 2. Concert Video Platform (`concert/`)
**Architecture**: Multi-user concert video sharing with synchronized playback
- **Data Structure**: `concerts/[Date-Artist-Venue]/videos/[username]/` contains user's videos + index.json
- **Manifest System**: Each concert has `manifest.json` listing all users and their video manifests
- **Web Interface**: Static HTML/CSS/JS in `webcode/` with concert-specific pages
- **Video Processing**: Convert MOV→MP4, generate timestamps, create indexes

**Key Workflows**:
```bash
# Process new concert videos (converts MOV→MP4, generates indexes, moves files)
python scripts/convert_and_index.py --root "concert/concerts/[concert-name]/videos" --move-processed

# Serve files locally for testing (handles video range requests)
python scripts/simple_http_server.py --port 8000 --directory .
# Then visit: http://localhost:8000/concert/webcode/homepage.html
```

**Data Flow**:
1. Users upload MOV files to `concerts/[concert]/videos/[username]/`
2. `convert_and_index.py` converts to MP4, extracts timestamps, generates `index.json` per user
3. Script generates master `manifest.json` linking all user manifests
4. Web interface loads manifest, renders timeline, enables synchronized multi-user playback

**File Patterns**:
- `manifest.json`: Concert-level metadata with user list and manifest paths
- `videos/[user]/index.json`: User's video list with timestamps and durations
- `videos/[user]/processed/`: Original MOV files moved here after conversion
- `webcode/[concert-slug].html`: Auto-generated concert pages

## Development Guidelines

### Code Modification Policy
- **DO NOT modify existing files** unless explicitly requested to build/implement something
- **Scripts/utilities belong in `scripts/` folder** - always place new Python files there
- **Existing web interface** (`webcode/`) should not be touched without explicit request
- **Concert player, timeline, CSS** are stable - don't modify unless asked to implement features
- **When user is "ideating" or brainstorming** - create example/demo scripts in `scripts/` folder instead of modifying existing code

### Python Development
- **All new Python scripts** go in `scripts/` folder
- **Analysis/utility scripts** should be standalone and not modify existing functionality
- **Audio analysis** dependencies in `scripts/audio_requirements.txt`
- **Testing scripts** should have descriptive names like `test_audio_sync.py` or `demo_sequential_player.py`

### Video Processing
- **Always use main conversion script** - handles both single-user and multi-user concert structures automatically
- **Testing Web Interface**: User typically has the HTTP server running already - don't start the server, just reference URLs for testing
- **File Timestamps**: Video conversion preserves original MOV file timestamps on converted MP4s for accurate timeline generation

### Cross-Platform
- **bashrunner** handles Windows/Unix shell differences automatically
- **Scripts use forward slashes** in paths (Python handles conversion)

## Dependencies
- Video: ffmpeg (for MOV→MP4 conversion)
- Web: Static files, no build process
- Python: subprocess, json, pathlib, datetime (see `scripts/audio_requirements.txt` for audio analysis)
- Visualization: vispy, numpy (for sungraph)

### 1. bashrunner Library (`bashrunner/`) and 4. SunGraph Visualization (`sungraph/`)
- 3D sun path visualization using vispy
- Animated solar arc demonstration with numpy-generated elliptical paths
- Cross-platform Python library for executing bash commands via subprocess
- Main API: `run_bash_command(command: str)` returns `subprocess.CompletedProcess`
- Windows compatibility: Uses `shell=True` automatically on Windows platforms
- Test with: `python bashrunner/example.py` or the VS Code task "Run example.py"

## Quick Start
1. `python scripts/simple_http_server.py` - Start web server
2. Visit concert pages at `http://localhost:8000/concert/webcode/`

