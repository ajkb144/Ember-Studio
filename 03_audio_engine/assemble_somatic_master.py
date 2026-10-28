"""
assemble_somatic_master.py — Precision Audio Splicing & Mastering Engine for SEED_01
Splices Amanjot's voice memo, applies clinical room tone crossfades,
runs the broadcast conditioning chain, and auto-ducks the 432Hz + brown noise stem.
"""

import math
import os
import wave
import numpy as np
import scipy.signal as signal
from master_mixer import (
    condition_voice_track,
    calculate_ducking_envelope,
    true_peak_limiter,
    SAMPLE_RATE
)

def read_wav_as_float(file_path: str):
    with wave.open(file_path, "rb") as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        fs = wf.getframerate()
        n_frames = wf.getnframes()
        raw_bytes = wf.readframes(n_frames)

    if sampwidth == 2:
        audio = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
    elif sampwidth == 3:
        # 24-bit PCM
        raw = np.frombuffer(raw_bytes, dtype=np.uint8)
        raw = raw.reshape(-1, 3)
        padded = np.zeros((raw.shape[0], 4), dtype=np.uint8)
        padded[:, 1:] = raw
        audio = padded.view('<i4').reshape(-1).astype(np.float32) / 2147483648.0
    elif sampwidth == 4:
        audio = np.frombuffer(raw_bytes, dtype=np.int32).astype(np.float32) / 2147483648.0
    else:
        raise ValueError(f"Unsupported sample width: {sampwidth}")

    if n_channels == 2:
        audio = audio.reshape(-1, 2)
    return audio, fs

def write_wav_24bit(file_path: str, audio: np.ndarray, fs: int = SAMPLE_RATE):
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    if audio.ndim == 1:
        audio = np.column_stack([audio, audio])
    
    # Clip to [-1.0, 0.999999]
    audio = np.clip(audio, -1.0, 0.999999)
    int_audio = (audio * 8388607.0).astype(np.int32)
    
    # Pack to 24-bit PCM bytes
    raw_bytes = bytearray()
    for frame in int_audio:
        for ch in frame:
            b = int(ch).to_bytes(4, byteorder='little', signed=True)
            raw_bytes.extend(b[:3])

    with wave.open(file_path, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(3)
        wf.setframerate(fs)
        wf.writeframes(raw_bytes)
    print(f"[Audio Engine] Wrote 24-bit Master WAV: {file_path} ({len(audio)/fs:.2f}s)")

def crossfade(a: np.ndarray, b: np.ndarray, fade_samples: int) -> np.ndarray:
    """Equal-power crossfade between two audio segments."""
    fade_out = np.cos(np.linspace(0, np.pi / 2, fade_samples))
    fade_in = np.sin(np.linspace(0, np.pi / 2, fade_samples))
    
    cross = a[-fade_samples:] * fade_out + b[:fade_samples] * fade_in
    return np.concatenate([a[:-fade_samples], cross, b[fade_samples:]])

def main():
    raw_wav_path = os.path.join(os.path.dirname(__file__), "raw_voice_memos", "memo_1_decoded.wav")
    freq_432_path = os.path.join(os.path.dirname(__file__), "frequencies", "432Hz_natural_tuning_sigh.wav")
    brown_path = os.path.join(os.path.dirname(__file__), "frequencies", "brown_noise_warm_bed.wav")
    spliced_out = os.path.join(os.path.dirname(__file__), "spliced_voice_SEED_01.wav")
    master_out = os.path.join(os.path.dirname(__file__), "master_audio_SEED_01_EN.wav")

    print("[Audio Engine] Loading decoded raw voice recording...")
    raw_audio, fs = read_wav_as_float(raw_wav_path)
    if raw_audio.ndim > 1:
        raw_audio = np.mean(raw_audio, axis=1)

    fade_len = int(fs * 0.020) # 20ms crossfade

    # Slice A: 3.35s to 34.85s (Hook through "...or soften.")
    slice_a = raw_audio[int(3.35 * fs) : int(34.85 * fs)].copy()
    # Apply gentle 50ms fade-in to avoid any click
    slice_a[:int(fs*0.05)] *= np.linspace(0, 1, int(fs*0.05))

    # Room Tone Sample from clean silence window (52.5s to 56.5s)
    rt_sample = raw_audio[int(52.5 * fs) : int(56.5 * fs)].copy()
    rt_len = len(rt_sample)
    
    # Create 4.50s Somatic Silence Bed using looped organic room tone
    pause_samples = int(4.50 * fs)
    pause_bed = np.tile(rt_sample, int(np.ceil(pause_samples / rt_len)))[:pause_samples]

    # Slice B: 57.65s to 68.85s (Take 2: "Bring the eyes back to center... watching your body let go")
    slice_b = raw_audio[int(57.65 * fs) : int(68.85 * fs)].copy()

    # Outro Room Tone: 1.50s with smooth exponential decay
    outro_samples = int(1.50 * fs)
    outro_bed = pause_bed[:outro_samples].copy()
    outro_bed *= np.linspace(1.0, 0.0, outro_samples) ** 2

    # Assemble complete voice track with equal-power crossfades
    track = crossfade(slice_a, pause_bed, fade_len)
    track = crossfade(track, slice_b, fade_len)
    track = crossfade(track, outro_bed, fade_len)

    total_sec = len(track) / fs
    print(f"[Audio Engine] Spliced Voice Track assembled: {total_sec:.2f} seconds")
    write_wav_24bit(spliced_out, track, fs)

    # Apply Locked Vocal Conditioning DSP Chain
    print("[Audio Engine] Conditioning vocal track through SM7B curve + De-Esser + Opto-Leveler...")
    vocal_conditioned = condition_voice_track(track, fs)

    # Normalize conditioned vocal to -16.0 LUFS target
    v_rms = np.sqrt(np.mean(vocal_conditioned ** 2) + 1e-12)
    target_vocal_rms = math.pow(10.0, -18.0 / 20.0)
    vocal_norm = vocal_conditioned * (target_vocal_rms / v_rms)

    # Load 432Hz and Brown Noise Stems
    print("[Audio Engine] Loading 432Hz and Brown Noise stems...")
    stem_432, _ = read_wav_as_float(freq_432_path)
    stem_brown, _ = read_wav_as_float(brown_path)

    n_samples = len(vocal_norm)
    # Loop/trim stems to exact track length
    stem_432 = stem_432[:n_samples]
    stem_brown = stem_brown[:n_samples]

    # Combined Bed: 432Hz Sine Tone + Brown Noise Bed (-6dB relative)
    combined_bed = stem_432 * 0.7 + stem_brown * 0.3

    # Calculate Respiration-Synced Lookahead Auto-Ducking Envelope
    print("[Audio Engine] Computing Respiration-Synced Auto-Ducking envelope...")
    duck_gain = calculate_ducking_envelope(vocal_norm, fs)
    ducked_bed = combined_bed * duck_gain[:, np.newaxis]

    # Mix: Sum Vocal (centered) + Ducked Bed
    vocal_stereo = np.column_stack([vocal_norm, vocal_norm])
    mixed = vocal_stereo + ducked_bed

    # Master Bus True Peak Limiter (-1.5 dBTP)
    print("[Audio Engine] Applying 4x oversampled True Peak limiter (-1.5 dBTP)...")
    mastered = true_peak_limiter(mixed, ceiling_db=-1.5, fs=fs)

    # Write Broadcast Master WAV
    write_wav_24bit(master_out, mastered, fs)
    print(f"[Audio Engine] Master render complete: {master_out}")

if __name__ == "__main__":
    main()
