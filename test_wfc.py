import json
import sys
import os

# Add the parent directory to sys.path so we can import engine
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.generator import Generator

def main():
    model_dir = os.path.join(os.path.dirname(__file__), "models", "song")
    schema_path = os.path.join(model_dir, "schema.json")
    dataset_path = os.path.join(model_dir, "dataset.json")

    print(f"Initializing Generator from {dataset_path}...")
    generator = Generator(schema_path, dataset_path, generate_rules_inline=False)

    print("\nGenerating with fixed 'genre=Dance' and 'mode=major'...")
    output = generator.generate(seed=42, fixed_values={"genre": "Dance", "mode": "major"}, adherence=1.0)
    
    print("\nOutput Kick Pattern (Adherence 1.0):")
    print(output.get("kick_pattern"))
    
    print("\nOutput Parts (checking chord progression):")
    for part in output.get("parts", []):
        print(f"{part['entity_type']}: {part.get('chord_progression')}")

    print("\nGenerating with fixed 'genre=Dance' and 'mode=major' (Adherence 0.1)...")
    output_creative = generator.generate(seed=42, fixed_values={"genre": "Dance", "mode": "major"}, adherence=0.1)
    
    print("\nOutput Kick Pattern (Adherence 0.1):")
    print(output_creative.get("kick_pattern"))

if __name__ == "__main__":
    main()
