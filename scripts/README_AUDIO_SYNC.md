# Audio Synchronization Scripts

This folder contains scripts for analyzing and synchronizing overlapping concert videos using audio analysis.

## Overview

The audio sync system separates timestamp alignment from audio fine-tuning to achieve millisecond-precision synchronization between overlapping videos.

## Scripts

### `audio_sync_analyzer.py` - Core Analysis Engine
**Main Functions:**
- `find_overlapping_videos(concert_manifest_path)` - Discovers overlapping video pairs from concert manifests
- `sync_two_videos(video1, video2, ...)` - Analyzes audio sync between two specific videos
- `analyze_overlap_with_timestamps(overlap_info, ...)` - Timestamp-constrained analysis for precise results

**Analysis Methods:**
- **FFT Cross-Correlation**: Sub-millisecond precision using parabolic interpolation
- **Beat Detection**: 1ms resolution beat matching with librosa
- **Spectral Analysis**: MFCC and chroma features for confidence scoring
- **Timestamp Constraints**: Uses file timestamps to validate and weight results

**Key Features:**
- Millisecond precision (1ms beat detection, sub-ms FFT)
- Timestamp validation (rejects unrealistic offsets)
- Weighted confidence scoring (beat detection preferred over FFT)
- Absolute timing calculations (exact start times relative to video1)

### `analyze_sync_properly.py` - High-Level Interface
**Purpose:** User-friendly wrapper that provides clear, actionable sync instructions

**Workflow:**
1. Loads concert manifest and finds all overlapping videos
2. For each overlap, calculates timestamp-based estimate
3. Runs audio analysis for millisecond fine-tuning
4. Combines results into absolute timing instructions
5. Outputs human-readable sync instructions and JSON data

**Output:**
- Console: Step-by-step analysis with confidence scores
- File: `sync_instructions.json` with precise timing data

## Data Flow

```
Concert Manifest
       ↓
find_overlapping_videos() → [overlap_info...]
       ↓
analyze_overlap_with_timestamps() → analysis for each overlap
       ↓                              ↓
timestamp estimate              audio_sync_analyzer.py
(from file times)              (FFT + beat analysis)
       ↓                              ↓
       └─── COMBINED RESULT ─────────┘
                    ↓
         absolute_v2_start_time
         (exact timing in seconds)
```

## Usage Examples

### Analyze All Overlaps in a Concert
```bash
python scripts/analyze_sync_properly.py
# Creates: scripts/sync_instructions.json
```

### Analyze Specific Video Pair
```bash
python scripts/audio_sync_analyzer.py \
  --video1 "path/to/video1.mp4" \
  --video2 "path/to/video2.mp4" \
  --expected-offset 31.0 \
  --tolerance 1.0
```

### Analyze Concert with Custom Settings
```bash
python scripts/audio_sync_analyzer.py \
  --concert "9-19-25 Chris Stussy Chicago at Radius" \
  --overlap-duration 10 \
  --tolerance 2.0 \
  --output results.json
```

## Output Format

### sync_instructions.json
```json
[
  {
    "overlap_index": 1,
    "video1_info": "ethan/IMG_1765.mp4",
    "video2_info": "pelham/IMG_7367.mp4", 
    "video1_seek_time": 0.0,
    "video2_seek_time": 31.090000,
    "timestamp_estimate": 31.000,
    "audio_fine_tuning_ms": 90.000,
    "absolute_precision_seconds": 31.090000,
    "sync_confidence": 0.821,
    "overlap_duration": 2.551,
    "precision_achieved_ms": 90.000
  }
]
```

## Key Concepts

### Timestamp vs Audio Alignment
- **Timestamp**: When overlap occurs (from file modification times)
- **Audio**: Fine-tuning within overlap (from acoustic analysis)
- **Result**: Absolute start time = timestamp + audio_adjustment

### Confidence Scoring
- **FFT**: Raw cross-correlation peak strength
- **Beat**: Percentage of beats that match within tolerance
- **Combined**: Weighted by proximity to timestamp estimate

### Tolerance Constraints
- System rejects offsets too far from timestamp estimates
- Typical tolerance: ±1-2 seconds around expected timing
- Prevents false matches from noise or different songs

## Dependencies
- librosa: Audio analysis and beat detection
- numpy: Signal processing and FFT operations  
- scipy: Cross-correlation and signal filtering
- ffmpeg: Audio extraction from video files

## Integration
The sync results can be used to:
1. Trim videos at precise transition points (ffmpeg)
2. Configure web players for seamless handoffs
3. Generate synchronized playlists
4. Build multi-angle viewing experiences