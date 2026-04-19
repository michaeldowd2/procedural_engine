"""
Generate sample outputs using the procedural engine and write them to
models/{model}/output/generations.json for the visualiser.

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

_root        = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_models_root = os.path.join(_root, "models")
SCHEMA   = os.path.join(_models_root, args.model, "schema.json")
DATASET  = os.path.join(_models_root, args.model, "dataset.json")
OUT_DIR  = os.path.join(_root, "output", args.model)
OUT_FILE = os.path.join(OUT_DIR, "generations.json")

PROMPTS = [
    {"label": "Unconstrained (seed 1)",   "seed": 1,  "fixed_values": {}},
    {"label": "High-energy rock",         "seed": 2,  "fixed_values": {"genre": ["rock"],       "tags": ["high_energy"]}},
    {"label": "Slow ambient chill",       "seed": 3,  "fixed_values": {"genre": ["ambient"],    "tags": ["chill", "tempo_slow"]}},
    {"label": "Happy pop",                "seed": 4,  "fixed_values": {"genre": ["pop"],         "tags": ["happy_mood"]}},
    {"label": "Jazz minor (seed 5)",      "seed": 5,  "fixed_values": {"genre": ["jazz"],        "mode": "dorian"}},
    {"label": "Dark electronic",          "seed": 6,  "fixed_values": {"genre": ["electronic"],  "tags": ["dark_mood", "high_energy"]}},
    {"label": "Fast upbeat rap",          "seed": 7,  "fixed_values": {"genre": ["rap"],         "tags": ["tempo_fast", "high_energy"]}},
    {"label": "Mellow r&b",              "seed": 8,  "fixed_values": {"genre": ["r&b"],         "tags": ["neutral_mood", "low_energy"]}},
    {"label": "Long epic (tempo=128)",    "seed": 9,  "fixed_values": {"tempo": 128,             "tags": ["long"]}},
    {"label": "Short energetic (seed 10)","seed": 10, "fixed_values": {"tags": ["tempo_very_fast", "high_energy", "short"]}},
]

def main():
    print("Loading generator…")
    gen = Generator(SCHEMA, DATASET)

    samples = []
    for prompt in PROMPTS:
        print(f"  Generating: {prompt['label']}")
        song, edges = gen.generate(
            seed=prompt["seed"],
            adherence=0.8,
            fixed_values=prompt.get("fixed_values", {}),
            return_edges=True,
        )
        print(f"    {len(edges)} rule connections")
        samples.append({
            "label":        prompt["label"],
            "seed":         prompt["seed"],
            "fixed_values": prompt.get("fixed_values", {}),
            "song":         song,
            "edges":        edges,
        })

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT_FILE, "w") as f:
        json.dump(samples, f, indent=2)
    print(f"\nSaved {len(samples)} samples to {OUT_FILE}")

    # Keep manifest up to date so the Explorer knows which models exist
    import glob as _glob
    output_root = os.path.join(_root, "output")
    all_models = sorted(
        os.path.basename(d.rstrip("/\\"))
        for d in _glob.glob(os.path.join(output_root, "*/"))
        if os.path.isfile(os.path.join(d, "generations.json"))
    )
    manifest_path = os.path.join(output_root, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump({"models": all_models}, f, indent=2)
    print(f"Manifest updated -> {manifest_path}: {all_models}")

if __name__ == "__main__":
    main()
