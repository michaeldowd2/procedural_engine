# Song Model

Procedural music composition model. Generates complete song metadata including tempo, key, mode, genre, tags, instrument selection, song structure, and per-part chord progressions.

## Files

| File | Purpose |
|---|---|
| `schema.json` | Output structure — property names, types, ranges, and item libraries |
| `dataset.json` | Data sources, preprocessing bins, manual rules, item libraries |
| `data/` | Source datasets used for rule mining |
| `model_data/` | Generated outputs (created by scripts) |

## Data Sources

| Source | Type | What it contributes |
|---|---|---|
| `spotify_songs.csv` | CSV | genre, key, mode, tempo, energy, valence associations |
| `jamendo/...tsv` | wide_tsv | genre, mood/tag, instrument co-occurrences |
| `SegLabelHard/` | time_series_dir | emotion, instrument, vocal tag associations |
| `song_structures.csv` | CSV | genre→structure relationships |

## Preprocessing

Numeric binning is defined inside the `spotify_songs` source in `dataset.json`. Four columns are discretized into tags:

| Column | Tags produced |
|---|---|
| `tempo` | `tempo_slow`, `tempo_moderate`, `tempo_fast`, `tempo_very_fast` |
| `energy` | `energy_low`, `energy_medium`, `energy_high` |
| `valence` | `mood_dark`, `mood_neutral`, `mood_happy` |
| `target_duration` | `short`, `medium-short`, `medium`, `medium-long`, `long` |

`target_duration` has `"inject_on_sample": false` — it maps tags to numeric ranges during generation but does not auto-inject the label back into the output.

## Generating Samples

From the project root:

```bash
python scripts/generate_samples.py --model song
```

This mines rules inline and writes `model_data/generations.json` for the Explorer UI.

## Schema Overview

```
{
  tempo          numeric  60–200 BPM
  key            categorical  C, C#, D, ... B
  mode           categorical  major, minor, dorian, ...
  genre          tag_list
  tags           tag_list     mood, energy, tempo, style tags
  target_duration numeric     seconds
  instruments    item_list    from instrument_presets library
  structure      categorical  verse-chorus-... patterns
  parts          part_list    per-section chords and tags
}
```

## Wave Function Collapse (WFC) Patterns

The engine supports generic N-dimensional pattern generation via a Wave Function Collapse solver. Properties using the `wfc_grid` type in the schema (like `kick_pattern` and `chord_progression`) are generated as follows:

1. **Schema Dimensions & Domain**: The schema defines the dimensions of the grid (e.g., `[16]` for a 16-step 1D array) and the base mathematical domain of possible states (e.g., `[0, 1, ..., 9]`).
2. **Context-Triggered Rules**: `data/pattern_rules.json` contains generative rules (`state_weights`, `adjacency`) that trigger based on context items (e.g., `genre=Dance`).
3. **Linear Adherence Scaling**: Rules define abstract probability weights (where a weight of `0.0` means complete exclusion). The global `adherence` parameter linearly interpolates these weights toward a uniform distribution (`1.0`) as adherence decreases. 
   - `adherence = 1.0`: Strict adherence to defined weights.
   - `adherence = 0.5`: Defined weights are heavily favored, but excluded items (`0.0`) become possible (`0.5`).
   - `adherence = 0.0`: All states are completely uniform (pure chaos/creativity).
4. **Dictionary Substitution**: After the numeric grid is solved, an optional `dictionary_map` can substitute states with human-readable values (e.g., mapping `1` to `I` based on a `mode=major` trigger).
