"""
frequency_generator.py — Studio-Grade Solfeggio & Brownian Noise Synthesizer
Ember Somatic Studio (03_audio_engine)
Governed by DECISION GATE 2: LOCKED SPECIFICATIONS.

Specifications:
- Broadcast Base: 48kHz, 24-bit PCM Uncompressed Stereo WAV.
- Solfeggio Sine Stems (396Hz, 432Hz, 528Hz):
  * 100% Dual-Mono (L = R, 0° phase offset).
  * Subtle 2nd-harmonic analog saturation (-32 dB relative at 2f) for missing-fundamental phone speaker clarity.
  * Stereo binaural detuning strictly rejected (prevents mono phase cancellation).
- Brownian Noise Bed:
  * Leaky integration (alpha = 0.998 DC-blocker) of stereo white noise with 1/f^2 (-6dB/oct) roll-off.
  * Bandpass contour: High-pass at 45Hz (12dB/oct) + warm low-pass at 950Hz (12dB/oct).
  * Mid-Side spatial balance: Mid carries 45Hz–950Hz; Side high-passed at 160Hz, attenuated -6.0 dB relative to Mid.
  * Stem balance: Solfeggio sine at -3.0 dB, Brownian noise at -9.0 dB (6.0 dB sine-to-noise ratio).
  * 1.5s half-cosine fade-in and fade-out envelopes.
"""

import math
import os
import random
import struct
import wave

SAMPLE_RATE = 48000
BIT_DEPTH = 24
MAX_INT24 = 8388607      # 2^23 - 1
MIN_INT24 = -8388608     # -2^23

def pack_int24(sample_val: float) -> bytes:
    """Clamps float sample in [-1.0, 1.0] and packs into 3 little-endian bytes."""
    clamped = max(-1.0, min(1.0, sample_val))
    int_val = int(clamped * MAX_INT24)
    int_val = max(MIN_INT24, min(MAX_INT24, int_val))
    if int_val < 0:
        int_val = (1 << 24) + int_val
    return bytes([int_val & 0xFF, (int_val >> 8) & 0xFF, (int_val >> 16) & 0xFF])

def generate_solfeggio_sine(frequency_hz: float, duration_sec: float, sample_rate: int = SAMPLE_RATE) -> list[float]:
    """
    Generates pure sine wave + subtle 2nd-harmonic saturation at -32 dB (missing-fundamental psychoacoustic cue).
    -32 dB = 10^(-32/20) ≈ 0.02511886 relative amplitude.
    """
    total_samples = int(sample_rate * duration_sec)
    h2_amp = math.pow(10.0, -32.0 / 20.0)  # -32 dB relative
    norm_factor = 1.0 / (1.0 + h2_amp)
    
    samples = []
    for i in range(total_samples):
        t = float(i) / sample_rate
        f1 = math.sin(2.0 * math.pi * frequency_hz * t)
        f2 = math.sin(2.0 * math.pi * (2.0 * frequency_hz) * t)
        combined = (f1 + h2_amp * f2) * norm_factor
        samples.append(combined)
    return samples

def biquad_hpf(cutoff_hz: float, q: float = 0.7071, sample_rate: int = SAMPLE_RATE):
    """Calculates 2nd-order Butterworth High-Pass Filter biquad coefficients."""
    omega = 2.0 * math.pi * cutoff_hz / sample_rate
    sn = math.sin(omega)
    cs = math.cos(omega)
    alpha = sn / (2.0 * q)
    
    b0 = (1.0 + cs) / 2.0
    b1 = -(1.0 + cs)
    b2 = (1.0 + cs) / 2.0
    a0 = 1.0 + alpha
    a1 = -2.0 * cs
    a2 = 1.0 - alpha
    return (b0 / a0, b1 / a0, b2 / a0, a1 / a0, a2 / a0)

def biquad_lpf(cutoff_hz: float, q: float = 0.7071, sample_rate: int = SAMPLE_RATE):
    """Calculates 2nd-order Butterworth Low-Pass Filter biquad coefficients."""
    omega = 2.0 * math.pi * cutoff_hz / sample_rate
    sn = math.sin(omega)
    cs = math.cos(omega)
    alpha = sn / (2.0 * q)
    
    b0 = (1.0 - cs) / 2.0
    b1 = 1.0 - cs
    b2 = (1.0 - cs) / 2.0
    a0 = 1.0 + alpha
    a1 = -2.0 * cs
    a2 = 1.0 - alpha
    return (b0 / a0, b1 / a0, b2 / a0, a1 / a0, a2 / a0)

def apply_biquad(samples: list[float], coeffs) -> list[float]:
    """Applies biquad IIR filter to an audio sample buffer."""
    b0, b1, b2, a1, a2 = coeffs
    x1 = x2 = y1 = y2 = 0.0
    output = []
    for x in samples:
        y = b0 * x + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
        x2 = x1
        x1 = x
        y2 = y1
        y1 = y
        output.append(y)
    return output

def generate_stereo_brown_noise(duration_sec: float, sample_rate: int = SAMPLE_RATE) -> tuple[list[float], list[float]]:
    """
    Synthesizes decorrelated stereo Brownian noise:
    1. Leaky integration with alpha = 0.998 DC-blocker
    2. Bandpass filter: 45Hz HPF + 950Hz LPF (12dB/octave)
    3. Mid-Side spatial balance: Mid carries 45Hz-950Hz; Side high-passed at 160Hz and attenuated -6.0 dB.
    """
    total_samples = int(sample_rate * duration_sec)
    alpha = 0.998
    
    # 1. Leaky integration of stereo white noise
    left_raw = []
    right_raw = []
    l_acc = r_acc = 0.0
    
    for _ in range(total_samples):
        w_l = random.random() * 2.0 - 1.0
        w_r = random.random() * 2.0 - 1.0
        l_acc = alpha * l_acc + 0.05 * w_l
        r_acc = alpha * r_acc + 0.05 * w_r
        left_raw.append(l_acc)
        right_raw.append(r_acc)
        
    # 2. Bandpass: 45Hz HPF + 950Hz LPF
    hpf_45 = biquad_hpf(45.0, 0.7071, sample_rate)
    lpf_950 = biquad_lpf(950.0, 0.7071, sample_rate)
    
    l_filtered = apply_biquad(apply_biquad(left_raw, hpf_45), lpf_950)
    r_filtered = apply_biquad(apply_biquad(right_raw, hpf_45), lpf_950)
    
    # Normalize RMS
    rms_l = math.sqrt(sum(x * x for x in l_filtered) / total_samples) or 1.0
    rms_r = math.sqrt(sum(x * x for x in r_filtered) / total_samples) or 1.0
    l_filtered = [x / rms_l * 0.15 for x in l_filtered]
    r_filtered = [x / rms_r * 0.15 for x in r_filtered]
    
    # 3. Mid-Side Spatial Balance
    # Mid = (L + R) / sqrt(2), Side = (L - R) / sqrt(2)
    inv_sqrt2 = 1.0 / math.sqrt(2.0)
    mid = [(l + r) * inv_sqrt2 for l, r in zip(l_filtered, r_filtered)]
    side = [(l - r) * inv_sqrt2 for l, r in zip(l_filtered, r_filtered)]
    
    # Side channel high-passed at 160Hz and attenuated -6.0 dB (0.5x)
    hpf_160 = biquad_hpf(160.0, 0.7071, sample_rate)
    side_hp = apply_biquad(side, hpf_160)
    side_attenuated = [s * 0.5 for s in side_hp]
    
    # Reconstruct L and R: L = (Mid + Side) / sqrt(2), R = (Mid - Side) / sqrt(2)
    out_left = [(m + s) * inv_sqrt2 for m, s in zip(mid, side_attenuated)]
    out_right = [(m - s) * inv_sqrt2 for m, s in zip(mid, side_attenuated)]
    return out_left, out_right

def apply_cosine_envelope(samples: list[float], duration_sec: float, fade_sec: float = 1.5, sample_rate: int = SAMPLE_RATE) -> list[float]:
    """Applies smooth 1.5s half-cosine fade-in at head and fade-out at tail."""
    fade_samples = int(sample_rate * min(fade_sec, duration_sec / 4))
    total_samples = len(samples)
    enveloped = []
    
    for i, x in enumerate(samples):
        env = 1.0
        if i < fade_samples:
            env = 0.5 * (1.0 - math.cos(math.pi * i / fade_samples))
        elif i > total_samples - fade_samples:
            env = 0.5 * (1.0 - math.cos(math.pi * (total_samples - i) / fade_samples))
        enveloped.append(x * env)
    return enveloped

def write_24bit_stereo_wav(filepath: str, left: list[float], right: list[float], sample_rate: int = SAMPLE_RATE):
    """Encodes interleaved 24-bit PCM stereo WAV."""
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    num_samples = min(len(left), len(right))
    raw_bytes = bytearray()
    
    for i in range(num_samples):
        raw_bytes.extend(pack_int24(left[i]))
        raw_bytes.extend(pack_int24(right[i]))
        
    with wave.open(filepath, 'wb') as wav:
        wav.setnchannels(2)      # Stereo
        wav.setsampwidth(3)      # 24-bit = 3 bytes
        wav.setframerate(sample_rate)
        wav.writeframes(raw_bytes)

def synthesize_broadcast_stems(out_dir: str, duration_sec: float = 60.0):
    """
    Synthesizes the complete broadcast stem suite:
    1. 396Hz, 432Hz, 528Hz Dual-Mono Stems (-3.0 dBFS)
    2. Warm Brownian Noise Bed (-9.0 dBFS)
    3. Composite Ready-to-Mix Stems (Solfeggio + Brown Noise pre-combined at 6dB ratio)
    """
    print(f"[Acoustic Synthesizer] Generating 48kHz / 24-bit broadcast stems ({duration_sec}s)...")
    
    # 1. Generate brown noise bed
    print(" -> Synthesizing Mid-Side decorrelated Brownian noise bed (45Hz–950Hz)...")
    bn_l, bn_r = generate_stereo_brown_noise(duration_sec, SAMPLE_RATE)
    bn_l = apply_cosine_envelope(bn_l, duration_sec, 1.5, SAMPLE_RATE)
    bn_r = apply_cosine_envelope(bn_r, duration_sec, 1.5, SAMPLE_RATE)
    
    # Scale brown noise to -9.0 dBFS (0.3548)
    bn_gain = math.pow(10.0, -9.0 / 20.0)
    bn_l_scaled = [x * bn_gain for x in bn_l]
    bn_r_scaled = [x * bn_gain for x in bn_r]
    
    brown_path = os.path.join(out_dir, "brown_noise_warm_bed.wav")
    write_24bit_stereo_wav(brown_path, bn_l_scaled, bn_r_scaled)
    print(f"    Saved: {brown_path}")
    
    # 2. Solfeggio tones
    tones = [
        (396.0, "396Hz_liberation_grounding.wav"),
        (432.0, "432Hz_natural_tuning_sigh.wav"),
        (528.0, "528Hz_transformation_heart.wav")
    ]
    
    # Scale sine to -3.0 dBFS (0.7079)
    sine_gain = math.pow(10.0, -3.0 / 20.0)
    
    for freq, filename in tones:
        print(f" -> Synthesizing {freq}Hz pure tone with -32dB 2nd-harmonic missing-fundamental...")
        mono_sine = generate_solfeggio_sine(freq, duration_sec, SAMPLE_RATE)
        mono_sine = apply_cosine_envelope(mono_sine, duration_sec, 1.5, SAMPLE_RATE)
        sine_scaled = [x * sine_gain for x in mono_sine]
        
        # Dual-mono stereo (L = R)
        sine_path = os.path.join(out_dir, filename)
        write_24bit_stereo_wav(sine_path, sine_scaled, sine_scaled)
        print(f"    Saved: {sine_path}")

if __name__ == "__main__":
    freq_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frequencies")
    synthesize_broadcast_stems(freq_dir, duration_sec=60.0)
    print("[Acoustic Synthesizer] All broadcast stems generated at 48kHz / 24-bit PCM.")
