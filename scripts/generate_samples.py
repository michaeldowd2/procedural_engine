"""
Generate sample outputs using the procedural engine and write them to
models/{model}/model_data/generations.json for the visualiser.

Usage:
    python scripts/generate_samples.py              # defaults to 'song'
    python scripts/generate_samples.py --model song
"""
import sys
import os
import json
import argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from engine.generator import Generator

parser = argparse.ArgumentParser()
parser.add_argument("--model", default="song")
args, _ = parser.parse_known_args()

_models_root = os.path.join(os.path.dirname(__file__), "..", "models")
SCHEMA   = os.path.join(_models_root, args.model, "schema.json")
DATASET  = os.path.join(_models_root, args.model, "dataset.json")
OUT_DIR  = os.path.join(_models_root, args.model, "model_data")
OUT_FILE = os.path.join(OUT_DIR, "generations.json")

PROMPTS = [
    {"label": "Unconstrained (seed 1)",  "seed": 1,  "fixed_values": {}},
    {"label": "High-energy rock",        "seed": 2,  "fixed_values": {"tags": ["rock", "energy_high"]}},
    {"label": "Slow ambient chill",      "seed": 3,  "fixed_values": {"tags": ["ambient", "chill", "tempo_slow"]}},
    {"label": "Happy pop",               "seed": 4,  "fixed_values": {"tags": ["pop", "mood_happy"]}},
    {"label": "Jazz minor (seed 5)",     "seed": 5,  "fixed_values": {"tags": ["jazz"], "mode": "dorian"}},
    {"label": "Dark electronic",         "seed": 6,  "fixed_values": {"tags": ["electronic", "mood_dark", "energy_high"]}},
    {"label": "Fast upbeat rap",         "seed": 7,  "fixed_values": {"tags": ["rap", "tempo_fast", "energy_high"]}},
    {"label": "Mellow r&b",              "seed": 8,  "fixed_values": {"tags": ["r&b", "mood_neutral", "energy_low"]}},
    {"label": "Long epic (tempo=128)",   "seed": 9,  "fixed_values": {"tempo": 128, "tags": ["long"]}},
    {"label": "Short energetic (seed 10)","seed": 10, "fixed_values": {"tags": ["tempo_very_fast", "energy_high", "short"]}},
]

def main():
    print("Loading generator…")
    gen = Generator(SCHEMA, DATASET)

    samples = []
    for prompt in PROMPTS:
        print(f"  Generating: {prompt['label']}")
        song = gen.generate(
            seed=prompt["seed"],
            adherence=0.8,
            fixed_values=prompt.get("fixed_values", {}),
        )
        samples.append({
            "label":        prompt["label"],
            "seed":         prompt["seed"],
            "fixed_values": prompt.get("fixed_values", {}),
            "song":         song,
        })

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT_FILE, "w") as f:
        json.dump(samples, f, indent=2)
    print(f"\nSaved {len(samples)} samples to {OUT_FILE}")

if __name__ == "__main__":
    main()
