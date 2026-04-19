import json
from engine import Generator
import pprint

def main():
    print("Initializing Generator...")
    gen = Generator(
        schema_path="models/song/schema.json",
        dataset_path="models/song/dataset.json"
    )
    
    print("\n--- Generating Unconstrained Song ---")
    song1 = gen.generate(seed=42, adherence=1.0)
    print(json.dumps(song1, indent=2))
    
    print("\n--- Generating Constrained Song (Ambient, Chill) ---")
    song2 = gen.generate(
        seed=100, 
        adherence=2.0, 
        fixed_values={"tags": ["ambient", "chill"], "tempo": 70}
    )
    print(json.dumps(song2, indent=2))

if __name__ == "__main__":
    main()
