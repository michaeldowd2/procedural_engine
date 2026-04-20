# Song Schema v2 - Example Output

This document shows what a generated song looks like with the new schema structure.

## Key Design Features

### 1. Nested Pattern Structures
Both chords and instrument patterns use the same repeating structure:
- `pattern_structure`: Array of pattern IDs (e.g., `["A", "B"]`)
- `repetitions`: How many times to repeat the entire structure
- `patterns`: Dictionary mapping IDs to actual content

### 2. Duration Constraints
Each part has `duration_bars` which must be satisfied by patterns:
```
total_bars = sum(len(patterns[p]) for p in pattern_structure) × repetitions
```

### 3. Anti-Correlated Part Tags
Part tags use negative context weights to create contrast:
- `parts[-1].part_tags: -0.5` means "less likely to repeat previous part's tags"
- Creates dynamic variation: sparse → dense, mellow → energetic

### 4. Pattern Encoding (Instruments)
String-based rhythm notation where each pattern = 1 bar:
- `"1"` = whole note (event on beat 1, held for 4 beats)
- `"11"` = two half notes (events on beats 1 & 3, each held 2 beats)
- `"1010"` = four quarter notes
- `"10101010"` = eight eighth notes
- `"1-10"` = half note, quarter rest, quarter note

## Example Generated Song

```json
{
  "tempo": 128,
  "key": "C",
  "mode": "minor",
  "target_duration": 210,
  "tags": ["energetic", "dark", "electronic"],
  "instrument_list": ["kick", "snare", "closed_hat", "bass", "synth_lead", "pad"],
  "part_structure": "intro-verse-chorus-verse-chorus-bridge-chorus",

  "parts": {
    "intro_0": {
      "part_type": "intro",
      "part_tags": ["sparse", "atmospheric"],
      "duration_bars": 8,

      "chords": {
        "pattern_structure": ["A"],
        "repetitions": 2,
        "patterns": {
          "A": ["i", "VI", "III", "VII"]
        }
      },
      "_chord_calc": "4 chords in A = 4 bars, repetitions = 8/4 = 2 ✓",

      "instruments": {
        "kick": {
          "pattern_structure": ["A", "B"],
          "repetitions": 4,
          "patterns": {
            "A": "1000",
            "B": "1010"
          },
          "_calc": "2 patterns, repetitions = 8/2 = 4 ✓"
        },
        "closed_hat": {
          "pattern_structure": ["A"],
          "repetitions": 8,
          "patterns": {
            "A": "10101010"
          },
          "_calc": "1 pattern, repetitions = 8/1 = 8 ✓"
        },
        "pad": {
          "pattern_structure": ["A"],
          "repetitions": 8,
          "patterns": {
            "A": "1---"
          },
          "_calc": "1 pattern, repetitions = 8/1 = 8 ✓"
        }
      }
    },

    "verse_0": {
      "part_type": "verse",
      "part_tags": ["dense", "driving"],
      "duration_bars": 16,

      "chords": {
        "pattern_structure": ["A", "B"],
        "repetitions": 2,
        "patterns": {
          "A": ["i", "VI", "III", "VII"],
          "B": ["i", "iv", "VI", "VII"]
        }
      },
      "_chord_calc": "A=4 bars, B=4 bars, repetitions = 16/(4+4) = 2 ✓",

      "instruments": {
        "kick": {
          "pattern_structure": ["A"],
          "repetitions": 16,
          "patterns": {
            "A": "1010"
          },
          "_calc": "1 pattern, repetitions = 16/1 = 16 ✓"
        },
        "snare": {
          "pattern_structure": ["A"],
          "repetitions": 16,
          "patterns": {
            "A": "0010"
          },
          "_calc": "1 pattern, repetitions = 16/1 = 16 ✓"
        },
        "closed_hat": {
          "pattern_structure": ["A", "B"],
          "repetitions": 8,
          "patterns": {
            "A": "10101010",
            "B": "1010101-"
          },
          "_calc": "2 patterns, repetitions = 16/2 = 8 ✓"
        },
        "bass": {
          "pattern_structure": ["A", "B"],
          "repetitions": 8,
          "patterns": {
            "A": "1-1-1010",
            "B": "10101-10"
          },
          "_calc": "2 patterns, repetitions = 16/2 = 8 ✓"
        },
        "synth_lead": {
          "pattern_structure": ["A", "B", "C"],
          "repetitions": 5,
          "patterns": {
            "A": "0-101010",
            "B": "10-10-10",
            "C": "1-1-10-1"
          },
          "_calc": "3 patterns, repetitions = 16/3 = 5.33 (rounds to 5, leaves 1 bar partial) ⚠️"
        },
        "pad": {
          "pattern_structure": ["A"],
          "repetitions": 16,
          "patterns": {
            "A": "1---"
          },
          "_calc": "1 pattern, repetitions = 16/1 = 16 ✓"
        }
      }
    },

    "chorus_0": {
      "part_type": "chorus",
      "part_tags": ["energetic", "uplifting"],
      "duration_bars": 16,

      "chords": {
        "pattern_structure": ["A"],
        "repetitions": 4,
        "patterns": {
          "A": ["i", "VI", "III", "VII"]
        }
      },

      "instruments": {
        "kick": {
          "pattern_structure": ["A"],
          "repetitions": 16,
          "patterns": {
            "A": "1010"
          }
        },
        "snare": {
          "pattern_structure": ["A", "B"],
          "repetitions": 4,
          "patterns": {
            "A": "0010",
            "B": "00101010"
          }
        },
        "closed_hat": {
          "pattern_structure": ["A"],
          "repetitions": 16,
          "patterns": {
            "A": "10101010"
          }
        },
        "bass": {
          "pattern_structure": ["A"],
          "repetitions": 8,
          "patterns": {
            "A": "1-101-10"
          }
        },
        "synth_lead": {
          "pattern_structure": ["A", "B"],
          "repetitions": 4,
          "patterns": {
            "A": "1-10-101",
            "B": "101-1010"
          }
        },
        "pad": {
          "pattern_structure": ["A"],
          "repetitions": 8,
          "patterns": {
            "A": "1-"
          }
        }
      }
    }
  }
}
```

## Pattern Decoding Examples

### Kick Drum Pattern: `"1010"`
```
Beat:  1   2   3   4
       |   |   |   |
       X   -   X   -
```
- Events on beats 1 and 3
- Each held for 1 beat (quarter notes)

### Hi-Hat Pattern: `"10101010"`
```
Beat:  1   2   3   4
       | | | | | | | |
       X - X - X - X -
```
- Events on every half-beat
- Each held for half a beat (eighth notes)

### Bass Pattern: `"1-101-10"`
```
Beat:  1   2   3   4
       |   |   |   |
       X---X - X---X -
```
- Event on beat 1, held for 2 beats
- Event on beat 2.5, held for 1 beat
- Event on beat 3.5, held for 1.5 beats
- Creates syncopated bass groove

### Pad Pattern: `"1---"` or `"1-"`
```
Beat:  1   2   3   4
       |   |   |   |
       X-----------
```
- Single sustained note/chord held throughout the bar
- `"1---"` explicitly shows 4-beat hold
- `"1-"` is shorthand for same thing (hold to end)

## Duration Constraint Examples

### Example 1: Simple Repetition
```json
{
  "duration_bars": 8,
  "pattern_structure": ["A"],
  "repetitions": 4,
  "patterns": {
    "A": "1010"
  }
}
```
Calculation: `1 pattern × 4 repetitions = 4 bars` ❌ **INVALID** (doesn't match 8 bars)

Should be: `repetitions: 8` ✓

### Example 2: Multiple Patterns
```json
{
  "duration_bars": 16,
  "pattern_structure": ["A", "B"],
  "repetitions": 2,
  "patterns": {
    "A": ["i", "VI", "III", "VII"],
    "B": ["i", "iv", "VI", "VII"]
  }
}
```
Calculation: `(4 chords in A + 4 chords in B) × 2 repetitions = 16 bars` ✓

### Example 3: Complex Structure
```json
{
  "duration_bars": 12,
  "pattern_structure": ["A", "B", "C"],
  "repetitions": 2,
  "patterns": {
    "A": "1010",
    "B": "10101010",
    "C": "1-10"
  }
}
```
Calculation: `(1 bar + 1 bar + 1 bar) × 2 repetitions = 6 bars` ❌ **INVALID**

Should be: `repetitions: 4` to get 12 bars ✓

## Anti-Correlation Example

Given context configuration:
```json
{
  "context": {
    "global.tags": 1.0,
    "parts[-1].part_tags": -0.5
  }
}
```

If previous part had `part_tags: ["sparse", "mellow"]`:
- Tags like `["dense", "energetic"]` get **boosted** (opposite energy)
- Tags like `["sparse", "chill"]` get **reduced** (similar energy)
- Creates natural dynamics and contrast between sections
