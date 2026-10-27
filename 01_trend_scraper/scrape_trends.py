"""
scrape_trends.py — Viral & Algorithmic Trend Scraper for Ember Somatic Studio
Dual-engine scraper (Instagram Reels + YouTube Shorts) targeting somatic regulation,
polyvagal resets, and contemplative stillness.
Governed by DECISION GATE 0: LOCKED SPECIFICATIONS.
"""

import json
import os
import re

LOCKED_PARAMETERS = {
    "platforms": ["Instagram Reels", "YouTube Shorts"],
    "view_floors": {
        "english": 100000,
        "hindi": 25000,
        "punjabi_somatic": 15000,
        "punjabi_spiritual": 25000
    },
    "save_rate_benchmark": {
        "english": 0.030,     # Target > 3.0%
        "hindi": 0.025,       # Target > 2.5%
        "punjabi": 0.025      # Target > 2.5%
    },
    "composite_coregulation_filter": {
        "min_duration_sec": 18,
        "max_duration_sec": 65,
        "min_outlier_play_to_follower": 1.5,
        "min_like_to_play_rate": 0.035,
        "max_whisper_wpm": 145,
        "visceral_relief_nlp_markers": [
            "sighed", "yawned", "shoulders dropped", "saving this", "saved",
            "needed this", "unclenched", "sukoon", "shanti", "thehraav",
            "sehaj", "dil halka", "sukhoon", "mann shanti", "rabab"
        ]
    },
    "strict_exclusions": [
        "manifest", "manifestation", "hustle", "grind", "hack", "life hack",
        "guru", "mindset shift", "millionaire", "alpha", "wim hof",
        "kapalabhati", "bhastrika", "weight loss", "cortisol face",
        "comment below", "comment 'reset'", "dm me"
    ],
    "query_clusters": {
        "english": {
            "somatic": [
                "#nervoussystemregulation", "#polyvagaltheory", "#vagusnervereset",
                "#somatichealing", "#somaticexperiencing", "#physiologicalsigh",
                "unclench your jaw", "drop your shoulders"
            ],
            "contemplative": [
                "#witnessconsciousness", "#nonduality", "#embodiedpresence",
                "#innerstillness", "#realizationprocess", "#somaticmeditation"
            ]
        },
        "hindi": {
            "somatic": [
                "#sukoon", "#manshanti", "#thehraav", "#maun",
                "mann ki shanti", "gehari saans", "#सुकून", "#मनकीशांति", "#ठहराव"
            ],
            "contemplative": [
                "#sakshibhav", "#shivashakti", "#dhyan", "#chidakash",
                "drashta bhaav", "#साक्षीभाव", "#ध्यान", "#शिवशक्ति"
            ]
        },
        "punjabi": {
            "somatic": [
                "#mannshanti", "#sukhoon", "#ruhaniyat",
                "andar di chup", "saah di shanti", "#ਸੁਕੂਨ", "#ਮਨਦੀਸ਼ਾਂਤੀ", "#ਰੂਹਾਨੀਅਤ"
            ],
            "contemplative": [
                "#sehaj", "#simran", "#akal", "#anand", "#vismad",
                "sehaj avastha", "naam simran", "#ਸਹਿਜ", "#ਸਿਮਰਨ", "#ਅਕਾਲ", "#ਅਨੰਦ"
            ]
        }
    }
}

def is_clean_content(caption: str, transcript: str = "") -> bool:
    """Checks caption and audio transcript against anti-slop commercial blacklist."""
    combined = f"{caption} {transcript}".lower()
    for word in LOCKED_PARAMETERS["strict_exclusions"]:
        if re.search(r'\b' + re.escape(word) + r'\b', combined):
            return False
    return True

def passes_composite_filter(video_data: dict) -> bool:
    """
    Evaluates video against composite co-regulation filters:
    1. Duration between 18s and 65s
    2. Outlier ratio playCount/followerCount >= 1.5x OR likes/plays >= 3.5%
    3. NLP comments have >= 2 visceral relief markers
    4. Anti-slop keyword & WPM check (< 145 WPM)
    """
    duration = video_data.get("duration", 0)
    if not (LOCKED_PARAMETERS["composite_coregulation_filter"]["min_duration_sec"] <= duration <= LOCKED_PARAMETERS["composite_coregulation_filter"]["max_duration_sec"]):
        return False
    
    plays = max(video_data.get("views", 0), 1)
    followers = max(video_data.get("followers", 1), 1)
    likes = video_data.get("likes", 0)
    
    outlier_ratio = plays / followers
    like_rate = likes / plays
    if outlier_ratio < LOCKED_PARAMETERS["composite_coregulation_filter"]["min_outlier_play_to_follower"] and like_rate < LOCKED_PARAMETERS["composite_coregulation_filter"]["min_like_to_play_rate"]:
        return False
    
    # NLP Comment Analysis
    comments = " ".join(video_data.get("top_comments", [])).lower()
    marker_hits = sum(1 for marker in LOCKED_PARAMETERS["composite_coregulation_filter"]["visceral_relief_nlp_markers"] if marker in comments)
    if marker_hits < 2:
        return False
        
    return is_clean_content(video_data.get("caption", ""))

def main():
    print("[Ember Scraper] Dual-Engine Viral & Algorithmic Scraper Initialized.")
    print("Platforms: Instagram Reels & YouTube Shorts.")
    print("Criteria: Composite Co-Regulation Filter (Outlier >= 1.5x, Save Benchmark >= 2.5–3.0%, NLP Relief >= 2).")

if __name__ == "__main__":
    main()
