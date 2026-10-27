"""
scrape_trends.py — Viral & Algorithmic Trend Scraper for Ember Somatic Studio
Targeted data extraction for somatic regulation, vagus nerve, and contemplative spiritual reels/shorts.
Governed by DECISION GATE 0: LOCKED SPECIFICATIONS.
"""

import json
import os
import re

LOCKED_PARAMETERS = {
    "platforms": ["Instagram Reels", "YouTube Shorts"],
    "virality_filters": {
        "english": {"min_views": 250000, "min_save_rate": 0.05},
        "hindi": {"min_views": 50000, "min_save_rate": 0.05},
        "punjabi": {"min_views": 50000, "min_save_rate": 0.05}
    },
    "strict_exclusions": [
        "manifest", "manifestation", "hustle", "hack", "life hack",
        "guru", "mindset shift", "millionaire", "alpha"
    ],
    "query_clusters": {
        "english": [
            "#nervoussystemregulation", "#polyvagaltheory", "#vagusnervereset",
            "#somatichealing", "#contemplativeprayer", "#presence"
        ],
        "hindi": [
            "#sakshibhav", "#shivashakti", "#dhyan",
            "#sukoon", "#nervoussystem", "#manshanti"
        ],
        "punjabi": [
            "#sehaj", "#simran", "#akal",
            "#anand", "#mannshanti", "#sukhoon"
        ]
    }
}

def is_clean_content(text: str) -> bool:
    """Returns False if text contains any forbidden hype/wellness clichés."""
    text_lower = text.lower()
    for word in LOCKED_PARAMETERS["strict_exclusions"]:
        if re.search(r'\b' + re.escape(word) + r'\b', text_lower):
            return False
    return True

def meets_virality_gate(language: str, views: int, saves: int) -> bool:
    """Evaluates whether content passes the view and save rate threshold."""
    lang_key = language.lower()
    if lang_key not in LOCKED_PARAMETERS["virality_filters"]:
        lang_key = "english"
    
    thresholds = LOCKED_PARAMETERS["virality_filters"][lang_key]
    if views < thresholds["min_views"]:
        return False
    
    save_rate = saves / max(views, 1)
    return save_rate >= thresholds["min_save_rate"]

def main():
    print("[Ember Scraper] Initializing viral trend engine with Decision Gate 0 parameters...")
    print(f" -> English Filter: Views > {LOCKED_PARAMETERS['virality_filters']['english']['min_views']}, Save Rate > 5%")
    print(f" -> Hindi/Punjabi Filter: Views > {LOCKED_PARAMETERS['virality_filters']['hindi']['min_views']}, Save Rate > 5%")
    print(f" -> Exclusions: {', '.join(LOCKED_PARAMETERS['strict_exclusions'])}")
    
    vault_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "viral_vault.json")
    if os.path.exists(vault_path):
        with open(vault_path, "r", encoding="utf-8") as f:
            vault = json.load(f)
        print(f" -> Loaded viral vault with {len(vault.get('items', []))} validated items.")

if __name__ == "__main__":
    main()
