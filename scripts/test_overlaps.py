#!/usr/bin/env python3

import sys
import os

# Add scripts directory to path
scripts_dir = os.path.join(os.path.dirname(__file__), 'scripts')
sys.path.insert(0, scripts_dir)

from audio_sync_analyzer import find_overlapping_videos
import json

# Test overlap detection
overlaps = find_overlapping_videos('concert/concerts/9-19-25 Chris Stussy Chicago at Radius/manifest.json')
print(f'Found {len(overlaps)} overlapping video pairs:')

for i, overlap in enumerate(overlaps):
    v1 = overlap['video1']
    v2 = overlap['video2']
    print(f'{i+1}. {v1["username"]}/{v1["filename"]} <-> {v2["username"]}/{v2["filename"]}')
    print(f'   Overlap: {overlap["overlap_duration"]:.1f} seconds')
    print(f'   V1 start in overlap: {overlap["v1_overlap_start"]:.1f}s')
    print(f'   V2 start in overlap: {overlap["v2_overlap_start"]:.1f}s')
    print()

# Show the specific overlap you asked about
print("=== Specific overlap analysis ===")
ethan_img1765_time = 1758349705.0  # from index.json
pelham_img7367_time = 1758349674.0  # from index.json

print(f"Ethan IMG_1765 start: {ethan_img1765_time}")
print(f"Pelham IMG_7367 start: {pelham_img7367_time}")
print(f"Time difference: {ethan_img1765_time - pelham_img7367_time:.1f} seconds")
print("Pelham started recording 31 seconds before Ethan")