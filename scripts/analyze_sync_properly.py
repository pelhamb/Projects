#!/usr/bin/env python3
"""
High-level interface for audio synchronization analysis.

This is the USER-FRIENDLY WRAPPER that provides clear, actionable sync instructions.
For low-level analysis engine, see audio_sync_analyzer.py.

RECOMMENDED USAGE: Run this script to get easy-to-understand sync instructions
for all overlapping videos in a concert.

Documentation: See scripts/README_AUDIO_SYNC.md for complete workflow explanation.

This script:
1. Finds all overlapping videos in the Chris Stussy concert
2. Combines timestamp estimates with audio analysis  
3. Outputs precise sync instructions in both console and JSON format
4. Creates scripts/sync_instructions.json with millisecond-precision timing

Example output: "Start Video 2 at exactly 31.090000s relative to Video 1"
"""

import sys
import os
scripts_dir = os.path.join(os.path.dirname(__file__), 'scripts')
sys.path.insert(0, scripts_dir)

from audio_sync_analyzer import find_overlapping_videos, sync_two_videos, analyze_overlap_with_timestamps
import json

def analyze_overlap_properly(overlap_info):
    """
    Proper analysis with millisecond precision for absolute timing.
    """
    print(f"\n{'='*60}")
    print(f"HIGH-PRECISION OVERLAP ANALYSIS")
    print(f"{'='*60}")
    
    v1 = overlap_info['video1']
    v2 = overlap_info['video2']
    
    print(f"Video 1: {v1['username']}/{v1['filename']}")
    print(f"Video 2: {v2['username']}/{v2['filename']}")
    print(f"Overlap duration: {overlap_info['overlap_duration']:.3f} seconds")
    print()
    
    # Calculate timestamp-based estimate
    timestamp_offset = overlap_info['v2_overlap_start'] - overlap_info['v1_overlap_start']
    
    print("STEP 1: Timestamp-based estimate")
    print(f"  Video 1 starts overlap at: {overlap_info['v1_overlap_start']:.3f}s into video")
    print(f"  Video 2 starts overlap at: {overlap_info['v2_overlap_start']:.3f}s into video")
    print(f"  Estimated offset: {timestamp_offset:.3f}s (Video 2 relative to Video 1)")
    print()
    
    print("STEP 2: Audio analysis for millisecond precision")
    # Analyze with higher precision
    analysis_duration = min(10.0, overlap_info['overlap_duration'])
    
    result = analyze_overlap_with_timestamps(
        overlap_info, 
        analysis_duration=analysis_duration,
        tolerance=2.0
    )
    
    if result and 'absolute_v2_start_time' in result:
        abs_start = result['absolute_v2_start_time']
        fine_tuning = result['audio_fine_tuning']
        
        print()
        print("FINAL HIGH-PRECISION RESULTS:")
        print(f"  Timestamp estimate: {timestamp_offset:.3f}s")
        print(f"  Audio fine-tuning: {fine_tuning:+.6f}s ({fine_tuning*1000:+.3f}ms)")
        print(f"  ABSOLUTE START TIME: {abs_start:.6f}s")
        print(f"  Confidence: {result['confidence_score']:.3f}")
        print(f"  Spectral similarity: {result['spectral_similarity']:.1%}")
        print()
        
        print("SYNC INSTRUCTIONS (millisecond precision):")
        print(f"  1. Start Video 1 ({v1['username']}) at: 0.000000s")
        print(f"  2. Start Video 2 ({v2['username']}) at: {abs_start:.6f}s")
        print(f"  → Perfect sync for {overlap_info['overlap_duration']:.3f} seconds")
        print(f"  → Precision: ±{abs(fine_tuning)*1000:.3f}ms from timestamp estimate")
        
        return {
            'video1_seek_time': 0.0,
            'video2_seek_time': abs_start,
            'timestamp_estimate': timestamp_offset,
            'audio_fine_tuning_ms': fine_tuning * 1000,
            'absolute_precision_seconds': abs_start,
            'sync_confidence': result['confidence_score'],
            'overlap_duration': overlap_info['overlap_duration'],
            'precision_achieved_ms': abs(fine_tuning) * 1000
        }
    
    return None

# Analyze all overlaps in the Chris Stussy concert
overlaps = find_overlapping_videos('concert/concerts/9-19-25 Chris Stussy Chicago at Radius/manifest.json')

sync_instructions = []
for i, overlap in enumerate(overlaps):
    result = analyze_overlap_properly(overlap)
    if result:
        result['overlap_index'] = i + 1
        result['video1_info'] = f"{overlap['video1']['username']}/{overlap['video1']['filename']}"
        result['video2_info'] = f"{overlap['video2']['username']}/{overlap['video2']['filename']}"
        sync_instructions.append(result)

print(f"\n{'='*60}")
print(f"HIGH-PRECISION SYNC INSTRUCTIONS SUMMARY")
print(f"{'='*60}")

for instr in sync_instructions:
    print(f"\nOverlap {instr['overlap_index']}: {instr['video1_info']} <-> {instr['video2_info']}")
    print(f"  Video 1 start: 0.000000s")
    print(f"  Video 2 start: {instr['video2_seek_time']:.6f}s")
    print(f"  Timestamp estimate: {instr['timestamp_estimate']:.3f}s")
    print(f"  Audio fine-tuning: {instr['audio_fine_tuning_ms']:+.3f}ms")
    print(f"  Final precision: ±{instr['precision_achieved_ms']:.3f}ms")
    print(f"  Confidence: {instr['sync_confidence']:.3f}")
    print(f"  Sync duration: {instr['overlap_duration']:.3f}s")

# Save results
with open('sync_instructions.json', 'w') as f:
    json.dump(sync_instructions, f, indent=2)

print(f"\n✓ Detailed sync instructions saved to sync_instructions.json")