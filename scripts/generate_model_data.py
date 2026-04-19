"""
Pre-generate learned_rules.json for one or all models.

By default the Generator mines rules inline on each instantiation (generate_rules_inline=True).
Run this script when you want faster startup times or intend to use generate_rules_inline=False.

Usage:
    python scripts/generate_model_data.py               # all models in models/
    python scripts/generate_model_data.py --model song  # specific model
"""
import argparse
import json
import os
import sys
import glob

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from engine.rule_miner import mine_rules


def run_model(model_dir):
    dataset_path = os.path.join(model_dir, "dataset.json")
    if not os.path.exists(dataset_path):
        print(f"[SKIP] No dataset.json in {model_dir}")
        return

    with open(dataset_path) as f:
        config = json.load(f)

    model_data_dir = os.path.join(model_dir, "model_data")
    os.makedirs(model_data_dir, exist_ok=True)

    rules = mine_rules(config, model_dir)

    rules_path = os.path.join(model_data_dir, "learned_rules.json")
    with open(rules_path, "w") as f:
        json.dump(rules, f, indent=2)
    print(f"Saved {len(rules)} rules -> {rules_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pre-generate learned_rules.json for model(s).")
    parser.add_argument("--model", help="Model name to process (default: all models in models/)")
    args = parser.parse_args()

    base_dir    = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    models_root = os.path.join(base_dir, "models")

    if args.model:
        model_dirs = [os.path.join(models_root, args.model)]
    else:
        model_dirs = sorted(
            d for d in glob.glob(os.path.join(models_root, "*/"))
            if os.path.isfile(os.path.join(d, "dataset.json"))
        )

    if not model_dirs:
        print("No models found.")
    else:
        for model_dir in model_dirs:
            model_name = os.path.basename(model_dir.rstrip("/\\"))
            print(f"\n{'='*60}")
            print(f"Model: {model_name}")
            print(f"{'='*60}")
            run_model(model_dir)

    # Regenerate manifest
    all_models = sorted(
        os.path.basename(d.rstrip("/\\"))
        for d in glob.glob(os.path.join(models_root, "*/"))
        if os.path.isfile(os.path.join(d, "dataset.json"))
    )
    output_root = os.path.join(base_dir, "output")
    os.makedirs(output_root, exist_ok=True)
    manifest_path = os.path.join(output_root, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump({"models": all_models}, f, indent=2)
    print(f"\nManifest -> {manifest_path}: {all_models}")
