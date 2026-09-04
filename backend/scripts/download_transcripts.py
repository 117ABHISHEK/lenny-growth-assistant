"""Copies a curated subset of Lenny's Podcast transcripts into backend/data/transcripts/.
Source: git clone --depth 1 https://github.com/ChatPRD/lennys-podcast-transcripts.git backend/data_source
"""
import shutil
from pathlib import Path

SOURCE_DIR = Path(__file__).parent.parent / "data_source" / "episodes"
DEST_DIR = Path(__file__).parent.parent / "data" / "transcripts"

# Curated growth / PMF / onboarding cluster
CURATED_EPISODES = [
    "annie-duke", "april-dunford", "april-dunford-20", "ben-horowitz",
    "bob-moesta", "bob-moesta-20", "ami-vora", "andy-johns",
    "aparna-chennapragada", "asha-sharma", "bangaly-kaba", "boz",
    "andrew-wilkinson", "anuj-rathi", "arielle-jackson", "austin-hay",
    "adam-fishman", "ada-chen-rekhi", "alisa-cohn", "alex-hardimen",
    "bill-carr", "bob-baxley", "ben-williams", "annie-pearl",
    "anton-osika", "amjad-masad", "andy-raskin", "andy-raskin_",
    "archie-abrams", "barbra-gago",
]

def main():
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    copied = 0
    for guest in CURATED_EPISODES:
        src = SOURCE_DIR / guest / "transcript.md"
        if src.exists():
            dest_folder = DEST_DIR / guest
            dest_folder.mkdir(exist_ok=True)
            shutil.copy(src, dest_folder / "transcript.md")
            copied += 1
        else:
            print(f"WARNING: missing transcript for {guest}")
    print(f"Copied {copied}/{len(CURATED_EPISODES)} transcripts to {DEST_DIR}")

if __name__ == "__main__":
    main()