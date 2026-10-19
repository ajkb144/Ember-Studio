"""
frequency_generator.py — Mathematical Solfeggio Frequency & Warm Brown Noise Synthesizer
Ember Somatic Studio (03_audio_engine)

Synthesizes studio-grade pure tone Solfeggio frequencies (396Hz, 432Hz, 528Hz)
and layered organic warm brown noise stems for nervous system co-regulation.
Can run standalone with zero external dependencies (standard library wave/struct/math)
or accelerated with numpy/scipy when available.
"""

import math
import os
import struct
import wave
import random

SAMPLE_RATE = 48000  # Broadcast standard 48kHz
BIT_DEPTH = 16       # 16-bit PCM (standard)
MAX_AMP = 32767      # Max amplitude for 16-bit signed PCM

def generate_solfeggio_tone(frequency_hz: float, duration_sec: float, sample_rate: int = SAMPLE_RATE, amplitude: float = 0.5) -> bytes:
    """Generate pure sine wave audio buffer for a given Solfeggio frequency with smooth 1.5s fade-in and fade-out."""
    total_samples = int(sample_rate * duration_sec)
    fade_samples = int(sample_rate * min(1.5, duration_sec / 4))
    raw_bytes = bytearray()

    for i in range(total_samples):
        # Calculate envelope
        env = 1.0
        if i < fade_samples:
            env = 0.5 * (1.0 - math.cos(math.pi * i / fade_samples))
        elif i > total_samples - fade_samples:
            env = 0.5 * (1.0 - math.cos(math.pi * (total_samples - i) / fade_samples))
        
        # Pure sine calculation
        t = float(i) / sample_rate
        sample_val = math.sin(2.0 * math.pi * frequency_hz * t) * amplitude * env
        int_sample = int(sample_val * MAX_AMP)
        int_sample = max(-32768, min(32767, int_sample))
        raw_bytes.extend(struct.pack('<h', int_sample))

    return bytes(raw_bytes)

def generate_brown_noise(duration_sec: float, sample_rate: int = SAMPLE_RATE, amplitude: float = 0.15) -> bytes:
    """Generate 1/f^2 warm Brownian noise (integrated white noise) for somatic soothing."""
    total_samples = int(sample_rate * duration_sec)
    fade_samples = int(sample_rate * min(1.5, duration_sec / 4))
    raw_bytes = bytearray()
    
    last_val = 0.0
    for i in range(total_samples):
        white = (random.random() * 2.0 - 1.0)
        # Brownian integration filter with slight leakage to prevent DC drift
        last_val = (last_val * 0.98) + (white * 0.05)
        
        # Envelope fade
        env = 1.0
        if i < fade_samples:
            env = 0.5 * (1.0 - math.cos(math.pi * i / fade_samples))
        elif i > total_samples - fade_samples:
            env = 0.5 * (1.0 - math.cos(math.pi * (total_samples - i) / fade_samples))

        sample_val = last_val * amplitude * env
        int_sample = int(sample_val * MAX_AMP)
        int_sample = max(-32768, min(32767, int_sample))
        raw_bytes.extend(struct.pack('<h', int_sample))

    return bytes(raw_bytes)

def write_wave_file(filepath: str, audio_data: bytes, sample_rate: int = SAMPLE_RATE, channels: int = 1):
    """Write mono or stereo PCM audio bytes to .wav file."""
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    with wave.open(filepath, 'wb') as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(2)  # 16-bit = 2 bytes
        wav.setframerate(sample_rate)
        wav.writeframes(audio_data)

def synthesize_core_pack(out_dir: str, duration_sec: float = 60.0):
    """Generate the baseline 396Hz, 432Hz, 528Hz, and brown noise stems."""
    tones = [
        (396.0, "396Hz_liberation_grounding.wav"),
        (432.0, "432Hz_natural_tuning_sigh.wav"),
        (528.0, "528Hz_transformation_heart.wav")
    ]
    print(f"Synthesizing Solfeggio tones ({duration_sec}s @ {SAMPLE_RATE}Hz)...")
    for freq, filename in tones:
        path = os.path.join(out_dir, filename)
        data = generate_solfeggio_tone(freq, duration_sec)
        write_wave_file(path, data)
        print(f" -> Generated: {path}")

    # Brownian noise
    brown_path = os.path.join(out_dir, "brown_noise_warm_bed.wav")
    brown_data = generate_brown_noise(duration_sec)
    write_wave_file(brown_path, brown_data)
    print(f" -> Generated: {brown_path}")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    freq_dir = os.path.join(current_dir, "frequencies")
    synthesize_core_pack(freq_dir, duration_sec=60.0)
    print("Core frequency stems generation complete.")
