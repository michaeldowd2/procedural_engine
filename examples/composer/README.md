# Music Composer Example

This example demonstrates using the Procedural Engine for procedural music composition.

## Overview

The composer generates complete song structures including:
- High-level properties: tempo, key, mode, genre/mood tags
- Song structure: verse/chorus/bridge arrangement
- Instruments: selection from preset library
- Musical parts: chord progressions and MIDI patterns for each section

## Files

### Schema
- `schema.json` - Defines the output structure and property types

### Dataset
- `dataset.json` - Configuration for association rules and embeddings
- `data/music_metadata.csv` - Genre/tempo/key relationships
- `data/song_structures.csv` - Common song structures by genre
- `data/instrument_presets.json` - Library of instrument presets with tags
- `data/chord_progressions.json` - Chord progressions with mode/tag associations

## Example Usage

```python
from procedural_engine import Generator

# Load schema and dataset
generator = Generator(
    schema="examples/composer/schema.json",
    dataset="examples/composer/dataset.json"
)

# Generate with no constraints
song = generator.generate(seed=42, adherence=1.0)

# Generate with fixed tempo
song = generator.generate(
    seed=42,
    adherence=0.8,
    fixed_values={"tempo": 128, "tags": ["pop", "energetic"]}
)
```

## Sample Output

```json
{
  "tempo": 128,
  "key": "C",
  "mode": "major",
  "tags": ["pop", "upbeat", "energetic"],
  "target_duration": 210,
  "instruments": ["preset_001", "preset_003", "preset_006"],
  "structure": "verse-chorus-verse-chorus-bridge-chorus",
  "parts": [
    {
      "part_type": "verse",
      "part_tags": ["mellow"],
      "chords": ["C", "G", "Am", "F"],
      "instrument_patterns": {
        "preset_001": "pattern_042",
        "preset_003": "pattern_071",
        "preset_006": "pattern_105"
      }
    },
    {
      "part_type": "chorus",
      "part_tags": ["energetic", "driving"],
      "chords": ["C", "G", "Am", "F"],
      "instrument_patterns": {
        "preset_001": "pattern_043",
        "preset_003": "pattern_072",
        "preset_006": "pattern_106"
      }
    }
  ]
}
```

## Dataset Notes

The sample datasets are intentionally small for illustration. In production:
- `music_metadata.csv` would contain 1000s of songs
- Instrument and pattern libraries would contain 100s-1000s of items
- Embeddings would be pre-trained on large corpora
- Manual rules would encode specific musical knowledge
