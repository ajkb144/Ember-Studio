"""
render_reels.py — Multi-Layer Broadcast Compositor for Ember Somatic Studio
Composites Master 24-bit Audio + Tactile B-Roll + Synchronized Subtitles.
Renders platform-safe 1080x1920 (9:16 vertical) exports.
"""

import os
import subprocess
import sys
import imageio_ffmpeg

def get_ffmpeg_path() -> str:
    return imageio_ffmpeg.get_ffmpeg_exe()

def render_reel(video_path: str, audio_path: str, subtitle_path: str, output_path: str,
                video_start: float = 49.5, duration: float = 48.64, language: str = "EN"):
    """
    Renders a vertical 9:16 Reel (1080x1920) combining:
    - Center-cropped high-res tactile footage
    - Master conditioned voice & 432Hz frequency bed
    - Burned-in precision subtitles in platform safe zone
    """
    ffmpeg_exe = get_ffmpeg_path()
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    escaped_sub = subtitle_path.replace("\\", "/").replace(":", "\\:")
    
    # Subtitle filter using ASS engine for pixel-perfect 1080x1920 rendering
    sub_filter = f"ass='{escaped_sub}'" if subtitle_path.endswith('.ass') else f"subtitles='{escaped_sub}'"
    
    # Video filter chain:
    # 1. Scale 1440x1440 to 1920x1920
    # 2. Crop center 1080x1920 (9:16 vertical)
    # 3. Burn in precision subtitles
    vf_chain = f"scale=1920:1920,crop=1080:1920,{sub_filter}"

    cmd = [
        ffmpeg_exe, "-y",
        "-ss", str(video_start),
        "-t", str(duration),
        "-i", video_path,
        "-i", audio_path,
        "-vf", vf_chain,
        "-map", "0:v",
        "-map", "1:a",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "19",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "320k",
        "-movflags", "+faststart",
        output_path
    ]

    print(f"[Ember Compositor] Rendering {language} Reel...")
    print(f"  Video: {video_path} (from {video_start}s for {duration}s)")
    print(f"  Audio: {audio_path}")
    print(f"  Sub:   {subtitle_path}")
    print(f"  Out:   {output_path}")

    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print("[Ember Compositor] Render failed! Stderr:")
        print(res.stderr[-800:])
        raise RuntimeError("FFmpeg render failed.")
    
    print(f"[Ember Compositor] Render SUCCESS: {output_path}")

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    video_path = os.path.join(base_dir, "04_cohesive_compositor", "visual_vault", "20261028_113824~2.mp4")
    audio_path = os.path.join(base_dir, "03_audio_engine", "master_audio_SEED_01_EN.wav")
    sub_path = os.path.join(base_dir, "04_cohesive_compositor", "subtitles", "SEED_01_EN.ass")
    output_path = os.path.join(base_dir, "04_cohesive_compositor", "final_exports", "SEED_01_EN_Reel.mp4")

    render_reel(
        video_path=video_path,
        audio_path=audio_path,
        subtitle_path=sub_path,
        output_path=output_path,
        video_start=49.5,
        duration=48.64,
        language="EN"
    )

if __name__ == "__main__":
    main()
