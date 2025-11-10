#!/usr/bin/env python3
"""
Audio synchronization analyzer for concert videos.

This is the CORE ENGINE for audio sync analysis. For user-friendly interface,
see analyze_sync_properly.py or refer to README_AUDIO_SYNC.md for complete documentation.

This script analyzes overlapping videos to find precise timing offsets
for synchronization using:
1. FFT cross-correlation of audio tracks
2. Beat detection and matching
3. Spectral feature analysis

Usage:
    python scripts/audio_sync_analyzer.py --video1 path/to/video1.mp4 --video2 path/to/video2.mp4
    python scripts/audio_sync_analyzer.py --concert "concert-name" --analyze-all-overlaps

Documentation: See scripts/README_AUDIO_SYNC.md for complete workflow and integration guide.
"""

import argparse
import json
import sys
from pathlib import Path
import datetime
import numpy as np
import librosa
import subprocess
import tempfile
import os
import shutil
from scipy import signal
from scipy.signal import find_peaks
import matplotlib.pyplot as plt


def find_ffmpeg():
    """Find ffmpeg executable."""
    ffmpeg = shutil.which('ffmpeg')
    if ffmpeg:
        return ffmpeg
    # Check common WinGet locations
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


def extract_audio_segment(video_path, start_time=0, duration=60, sample_rate=22050):
    """
    Extract audio from video file using ffmpeg.
    
    Args:
        video_path: Path to video file
        start_time: Start time in seconds
        duration: Duration to extract in seconds
        sample_rate: Audio sample rate
    
    Returns:
        numpy array of audio samples, actual sample rate
    """
    ffmpeg_cmd = find_ffmpeg()
    if not ffmpeg_cmd:
        raise RuntimeError("ffmpeg not found")
    
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
        temp_path = temp_audio.name
    
    try:
        # Extract audio segment using ffmpeg
        cmd = [
            ffmpeg_cmd, '-i', str(video_path),
            '-ss', str(start_time),
            '-t', str(duration),
            '-ar', str(sample_rate),
            '-ac', '1',  # mono
            '-acodec', 'pcm_s16le',
            '-y', temp_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {result.stderr}")
        
        # Load audio with librosa
        audio, sr = librosa.load(temp_path, sr=sample_rate)
        return audio, sr
        
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def find_audio_offset_fft(audio1, audio2, sr, max_offset_seconds=10):
    """
    Find time offset between two audio signals using FFT cross-correlation with sub-millisecond precision.
    
    Args:
        audio1, audio2: Audio signals as numpy arrays
        sr: Sample rate
        max_offset_seconds: Maximum offset to search
    
    Returns:
        offset in seconds (to sub-millisecond precision)
        confidence score
    """
    # Ensure signals are the same length for optimal correlation
    min_len = min(len(audio1), len(audio2))
    max_len = max(len(audio1), len(audio2))
    
    # Use the shorter length but pad to next power of 2 for FFT efficiency
    target_len = int(2 ** np.ceil(np.log2(max_len)))
    
    audio1_padded = np.pad(audio1[:min_len], (0, target_len - min_len))
    audio2_padded = np.pad(audio2[:min_len], (0, target_len - min_len))
    
    # Apply windowing to reduce edge effects
    window = np.hanning(len(audio1_padded))
    audio1_windowed = audio1_padded * window
    audio2_windowed = audio2_padded * window
    
    # Compute cross-correlation using FFT
    correlation = signal.correlate(audio1_windowed, audio2_windowed, mode='full')
    
    # Find peak with sub-sample precision using parabolic interpolation
    max_corr_idx = np.argmax(np.abs(correlation))
    
    # Parabolic interpolation for sub-sample precision
    if 0 < max_corr_idx < len(correlation) - 1:
        y1, y2, y3 = np.abs(correlation[max_corr_idx-1:max_corr_idx+2])
        x_offset = 0.5 * (y1 - y3) / (y1 - 2*y2 + y3) if (y1 - 2*y2 + y3) != 0 else 0
        max_corr_idx += x_offset
    
    # Convert to time offset with sub-millisecond precision
    offset_samples = max_corr_idx - (len(correlation) // 2)
    offset_seconds = offset_samples / sr
    
    # Calculate confidence as normalized correlation peak
    confidence = np.max(np.abs(correlation)) / (np.sqrt(np.sum(audio1_padded**2) * np.sum(audio2_padded**2)) + 1e-10)
    
    # Limit to reasonable range
    if abs(offset_seconds) > max_offset_seconds:
        print(f"Warning: Large offset detected ({offset_seconds:.6f}s), may be unreliable")
    
    return offset_seconds, confidence


def detect_beats(audio, sr):
    """
    Detect beat timestamps in audio signal.
    
    Returns:
        beat_times: Array of beat timestamps in seconds
        tempo: Estimated tempo in BPM
    """
    # Use librosa beat tracking
    tempo, beat_frames = librosa.beat.beat_track(y=audio, sr=sr, hop_length=512)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=512)
    
    return beat_times, tempo


def find_beat_offset(beats1, beats2, max_offset=10):
    """
    Find offset between two beat sequences with millisecond precision.
    
    Args:
        beats1, beats2: Arrays of beat timestamps
        max_offset: Maximum offset to consider in seconds
    
    Returns:
        best_offset: Offset in seconds (to millisecond precision)
        confidence: Matching confidence score
    """
    if len(beats1) == 0 or len(beats2) == 0:
        return 0, 0
    
    # Try different offsets with millisecond precision
    offset_range = np.arange(-max_offset, max_offset, 0.001)  # 1ms resolution
    scores = []
    
    for offset in offset_range:
        beats2_shifted = beats2 + offset
        
        # Count matches within tolerance (50ms for high precision)
        tolerance = 0.05  # 50ms tolerance
        matches = 0
        
        for beat1 in beats1:
            distances = np.abs(beats2_shifted - beat1)
            if np.min(distances) < tolerance:
                matches += 1
        
        # Normalize by number of beats
        score = matches / max(len(beats1), len(beats2_shifted))
        scores.append(score)
    
    best_idx = np.argmax(scores)
    best_offset = offset_range[best_idx]
    confidence = scores[best_idx]
    
    return best_offset, confidence


def analyze_spectral_features(audio, sr):
    """
    Extract spectral features for audio matching.
    
    Returns:
        features: Dictionary of spectral features
    """
    # Compute mel-frequency cepstral coefficients
    mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
    
    # Compute chroma features (use the correct librosa function)
    chroma = librosa.feature.chroma_stft(y=audio, sr=sr)
    
    # Compute spectral centroid
    spectral_centroid = librosa.feature.spectral_centroid(y=audio, sr=sr)
    
    return {
        'mfcc_mean': np.mean(mfcc, axis=1),
        'mfcc_std': np.std(mfcc, axis=1),
        'chroma_mean': np.mean(chroma, axis=1),
        'spectral_centroid_mean': np.mean(spectral_centroid)
    }


def sync_two_videos(video1_path, video2_path, overlap_start=0, overlap_duration=30, expected_offset=None, tolerance=1.0):
    """
    Analyze synchronization between two overlapping videos.
    
    Args:
        video1_path, video2_path: Paths to video files
        overlap_start: Start time of overlap in video1 (seconds)
        overlap_duration: Duration of overlap to analyze
        expected_offset: Expected time offset based on timestamps (seconds)
        tolerance: Acceptable error range around expected offset (seconds)
    
    Returns:
        sync_result: Dictionary with offset and confidence metrics
    """
    print(f"Analyzing sync between:")
    print(f"  Video 1: {video1_path}")
    print(f"  Video 2: {video2_path}")
    print(f"  Overlap: {overlap_start}s for {overlap_duration}s")
    if expected_offset is not None:
        print(f"  Expected offset: {expected_offset:.3f}s ± {tolerance}s")
    
    try:
        # Extract audio segments
        print("Extracting audio segments...")
        audio1, sr1 = extract_audio_segment(video1_path, overlap_start, overlap_duration)
        audio2, sr2 = extract_audio_segment(video2_path, 0, overlap_duration)
        
        # Ensure same sample rate
        if sr1 != sr2:
            audio2 = librosa.resample(audio2, orig_sr=sr2, target_sr=sr1)
            sr2 = sr1
        
        # FFT-based correlation
        print("Computing FFT cross-correlation...")
        fft_offset, fft_confidence = find_audio_offset_fft(audio1, audio2, sr1)
        
        # Beat-based analysis
        print("Detecting beats...")
        beats1, tempo1 = detect_beats(audio1, sr1)
        beats2, tempo2 = detect_beats(audio2, sr2)
        
        beat_offset, beat_confidence = find_beat_offset(beats1, beats2)
        
        # Spectral feature analysis
        features1 = analyze_spectral_features(audio1, sr1)
        features2 = analyze_spectral_features(audio2, sr2)
        
        # Determine best offset using timestamp constraints
        recommended_offset, confidence_score = determine_best_offset(
            fft_offset, fft_confidence,
            beat_offset, beat_confidence,
            expected_offset, tolerance
        )
        
        # Combine results
        result = {
            'fft_offset_seconds': float(fft_offset),
            'fft_confidence': float(fft_confidence),
            'beat_offset_seconds': float(beat_offset),
            'beat_confidence': float(beat_confidence),
            'tempo1_bpm': float(tempo1) if np.isscalar(tempo1) else float(tempo1[0]) if len(tempo1) > 0 else 0.0,
            'tempo2_bpm': float(tempo2) if np.isscalar(tempo2) else float(tempo2[0]) if len(tempo2) > 0 else 0.0,
            'recommended_offset': float(recommended_offset),
            'confidence_score': float(confidence_score),
            'expected_offset': float(expected_offset) if expected_offset is not None else None,
            'tolerance': float(tolerance),
            'analysis_duration': float(overlap_duration),
            'spectral_similarity': float(calculate_spectral_similarity(features1, features2))
        }
        
        print(f"Results:")
        print(f"  FFT offset: {fft_offset:.3f}s (confidence: {fft_confidence:.3f})")
        print(f"  Beat offset: {beat_offset:.3f}s (confidence: {beat_confidence:.3f})")
        print(f"  Tempo: {result['tempo1_bpm']:.1f} BPM vs {result['tempo2_bpm']:.1f} BPM")
        if expected_offset is not None:
            print(f"  Expected: {expected_offset:.3f}s ± {tolerance}s")
        print(f"  RECOMMENDED: {recommended_offset:.3f}s (confidence: {confidence_score:.3f})")
        
        return result
        
    except Exception as e:
        print(f"Error analyzing sync: {e}")
        return None


def determine_best_offset(fft_offset, fft_confidence, beat_offset, beat_confidence, expected_offset=None, tolerance=1.0):
    """
    Determine the best offset using timestamp constraints and multiple analysis methods.
    
    Args:
        fft_offset, fft_confidence: FFT cross-correlation results
        beat_offset, beat_confidence: Beat detection results
        expected_offset: Expected offset from timestamp analysis
        tolerance: Acceptable range around expected offset
    
    Returns:
        best_offset: Recommended offset
        confidence: Overall confidence score
    """
    candidates = []
    
    # Add FFT result
    candidates.append({
        'offset': fft_offset,
        'confidence': fft_confidence,
        'method': 'FFT',
        'base_weight': 0.3  # Lower weight for FFT due to potential noise
    })
    
    # Add beat result
    candidates.append({
        'offset': beat_offset,
        'confidence': beat_confidence,
        'method': 'Beat',
        'base_weight': 0.7  # Higher weight for beat detection
    })
    
    if expected_offset is not None:
        # Weight candidates based on how close they are to expected offset
        for candidate in candidates:
            distance = abs(candidate['offset'] - expected_offset)
            
            if distance <= tolerance:
                # Within tolerance - boost confidence
                proximity_bonus = (tolerance - distance) / tolerance  # 0 to 1
                candidate['proximity_weight'] = 1.0 + proximity_bonus
                candidate['within_tolerance'] = True
            else:
                # Outside tolerance - penalize heavily
                penalty = min(distance / tolerance, 5.0)  # Cap penalty at 5x
                candidate['proximity_weight'] = 1.0 / penalty
                candidate['within_tolerance'] = False
        
        # Calculate weighted scores
        for candidate in candidates:
            weighted_confidence = (
                candidate['confidence'] * 
                candidate['base_weight'] * 
                candidate['proximity_weight']
            )
            candidate['weighted_score'] = weighted_confidence
        
        print(f"Offset candidate evaluation:")
        for candidate in candidates:
            status = "✓" if candidate['within_tolerance'] else "✗"
            print(f"  {status} {candidate['method']}: {candidate['offset']:.3f}s "
                  f"(raw conf: {candidate['confidence']:.3f}, "
                  f"weighted: {candidate['weighted_score']:.3f})")
        
        # Choose best candidate
        best_candidate = max(candidates, key=lambda c: c['weighted_score'])
        return best_candidate['offset'], best_candidate['weighted_score']
    
    else:
        # No timestamp constraint - use simple weighted average
        total_weight = sum(c['base_weight'] * c['confidence'] for c in candidates)
        if total_weight == 0:
            return 0.0, 0.0
        
        weighted_offset = sum(
            c['offset'] * c['base_weight'] * c['confidence'] 
            for c in candidates
        ) / total_weight
        
        avg_confidence = sum(c['confidence'] for c in candidates) / len(candidates)
        
        return weighted_offset, avg_confidence


def calculate_spectral_similarity(features1, features2):
    """Calculate similarity between spectral features."""
    # Simple cosine similarity of MFCC means
    mfcc1 = features1['mfcc_mean']
    mfcc2 = features2['mfcc_mean']
    
    dot_product = np.dot(mfcc1, mfcc2)
    norm1 = np.linalg.norm(mfcc1)
    norm2 = np.linalg.norm(mfcc2)
    
    if norm1 == 0 or norm2 == 0:
        return 0
    
    return dot_product / (norm1 * norm2)


def analyze_overlap_with_timestamps(overlap_info, analysis_duration=30, tolerance=1.0):
    """
    Analyze a video overlap using timestamp information to constrain the search.
    
    Args:
        overlap_info: Overlap information from find_overlapping_videos()
        analysis_duration: Duration to analyze (seconds)
        tolerance: Acceptable error range (seconds)
    
    Returns:
        sync_result: Analysis results with absolute timing relative to video1
    """
    # Calculate the approximate offset from timestamps
    timestamp_offset = overlap_info['v2_overlap_start'] - overlap_info['v1_overlap_start']
    
    print(f"\n=== Timestamp-Constrained Analysis ===")
    print(f"Video 1 ({overlap_info['video1']['username']}): starts overlap at {overlap_info['v1_overlap_start']:.3f}s into video")
    print(f"Video 2 ({overlap_info['video2']['username']}): starts overlap at {overlap_info['v2_overlap_start']:.3f}s into video")
    print(f"Timestamp-based offset: {timestamp_offset:.3f}s (video2 relative to video1)")
    print(f"Searching for fine-tuning within ±{tolerance:.3f}s")
    
    # Use the shorter of overlap duration or analysis duration
    actual_duration = min(overlap_info['overlap_duration'], analysis_duration)
    
    # Analyze with expected offset near zero (we're looking for fine-tuning)
    result = sync_two_videos(
        overlap_info['video1']['video_path'],
        overlap_info['video2']['video_path'],
        overlap_info['v1_overlap_start'],
        actual_duration,
        expected_offset=0.0,  # Within overlap, expect small adjustments
        tolerance=tolerance
    )
    
    if result:
        # Calculate the ABSOLUTE timing: when should video2 start relative to video1's beginning
        audio_fine_tuning = result['recommended_offset']
        absolute_v2_start = timestamp_offset + audio_fine_tuning
        
        # Add absolute timing information to result
        result['timestamp_offset'] = float(timestamp_offset)
        result['audio_fine_tuning'] = float(audio_fine_tuning) 
        result['absolute_v2_start_time'] = float(absolute_v2_start)
        result['precision_milliseconds'] = float(abs(audio_fine_tuning) * 1000)
        
        print(f"\n=== PRECISION TIMING RESULTS ===")
        print(f"Timestamp offset: {timestamp_offset:.3f}s")
        print(f"Audio fine-tuning: {audio_fine_tuning:+.6f}s ({audio_fine_tuning*1000:+.3f}ms)")
        print(f"ABSOLUTE VIDEO2 START: {absolute_v2_start:.6f}s relative to video1")
        print(f"Precision achieved: ±{abs(audio_fine_tuning)*1000:.3f}ms from timestamp estimate")
        
    return result


def find_overlapping_videos(concert_manifest_path):
    """
    Find all overlapping video pairs in a concert.
    
    Returns:
        overlaps: List of overlap information dictionaries
    """
    with open(concert_manifest_path, 'r') as f:
        manifest = json.load(f)
    
    # Load all user videos
    all_videos = []
    base_dir = Path(concert_manifest_path).parent
    
    for user in manifest['users']:
        user_manifest_path = base_dir / user['manifestPath']
        with open(user_manifest_path, 'r') as f:
            user_data = json.load(f)
        
        for video in user_data['videos']:
            video_info = {
                'username': user['username'],
                'filename': video['filename'],
                'start_time': video['mtime'],
                'duration': video['duration'],
                'end_time': video['mtime'] + video['duration'],
                'video_path': base_dir / 'videos' / user['username'] / video['filename']
            }
            all_videos.append(video_info)
    
    # Find overlaps
    overlaps = []
    for i, video1 in enumerate(all_videos):
        for video2 in all_videos[i+1:]:
            # Check for temporal overlap
            overlap_start = max(video1['start_time'], video2['start_time'])
            overlap_end = min(video1['end_time'], video2['end_time'])
            
            if overlap_start < overlap_end:
                overlap_duration = overlap_end - overlap_start
                
                # Calculate relative positions
                v1_overlap_start = overlap_start - video1['start_time']
                v2_overlap_start = overlap_start - video2['start_time']
                
                overlaps.append({
                    'video1': video1,
                    'video2': video2,
                    'overlap_duration': overlap_duration,
                    'v1_overlap_start': v1_overlap_start,
                    'v2_overlap_start': v2_overlap_start,
                    'overlap_start_timestamp': overlap_start
                })
    
    return overlaps


def main():
    parser = argparse.ArgumentParser(description='Analyze audio synchronization between concert videos')
    parser.add_argument('--video1', help='Path to first video file')
    parser.add_argument('--video2', help='Path to second video file')
    parser.add_argument('--concert', help='Concert name to analyze all overlaps')
    parser.add_argument('--analyze-all-overlaps', action='store_true', help='Analyze all overlapping video pairs')
    parser.add_argument('--overlap-start', type=float, default=0, help='Start time of overlap in video1 (seconds)')
    parser.add_argument('--overlap-duration', type=float, default=30, help='Duration of overlap to analyze (seconds)')
    parser.add_argument('--expected-offset', type=float, help='Expected offset from timestamp analysis (seconds)')
    parser.add_argument('--tolerance', type=float, default=1.0, help='Acceptable error range around expected offset (seconds)')
    parser.add_argument('--output', help='Output JSON file for results')
    
    args = parser.parse_args()
    
    if args.video1 and args.video2:
        # Analyze specific video pair
        result = sync_two_videos(
            args.video1, args.video2, 
            args.overlap_start, args.overlap_duration,
            expected_offset=args.expected_offset,
            tolerance=args.tolerance
        )
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
        else:
            print(json.dumps(result, indent=2))
    
    elif args.concert:
        # Analyze all overlaps in concert
        concert_path = Path('concert/concerts') / args.concert / 'manifest.json'
        if not concert_path.exists():
            print(f"Concert manifest not found: {concert_path}")
            sys.exit(1)
        
        overlaps = find_overlapping_videos(concert_path)
        print(f"Found {len(overlaps)} overlapping video pairs")
        
        results = []
        for i, overlap in enumerate(overlaps):
            print(f"\n{'='*60}")
            print(f"Analyzing overlap {i+1}/{len(overlaps)}")
            print(f"{'='*60}")
            
            # Use timestamp-constrained analysis
            result = analyze_overlap_with_timestamps(
                overlap, 
                analysis_duration=args.overlap_duration,
                tolerance=args.tolerance
            )
            
            if result:
                result['overlap_info'] = {
                    'video1_user': overlap['video1']['username'],
                    'video1_file': overlap['video1']['filename'],
                    'video2_user': overlap['video2']['username'],
                    'video2_file': overlap['video2']['filename'],
                    'overlap_duration': overlap['overlap_duration'],
                    'overlap_timestamp': overlap['overlap_start_timestamp'],
                    'v1_overlap_start': overlap['v1_overlap_start'],
                    'v2_overlap_start': overlap['v2_overlap_start']
                }
                results.append(result)
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
        else:
            print(f"\n{'='*60}")
            print(f"SUMMARY: {len(results)} sync analyses completed")
            print(f"{'='*60}")
            for result in results:
                info = result['overlap_info']
                print(f"{info['video1_user']}/{info['video1_file']} <-> {info['video2_user']}/{info['video2_file']}")
                print(f"  Recommended offset: {result['recommended_offset']:.3f}s (confidence: {result['confidence_score']:.3f})")
                print(f"  Expected: {result['expected_offset']:.3f}s, Beat: {result['beat_offset_seconds']:.3f}s, FFT: {result['fft_offset_seconds']:.3f}s")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()