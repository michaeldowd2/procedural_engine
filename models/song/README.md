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
