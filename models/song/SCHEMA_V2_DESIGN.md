# Schema v2 Design Document

## Overview

Schema v2 introduces sophisticated pattern structures, temporal anti-correlation, and duration constraints while maintaining full compatibility with the generic procedural engine.

## Key Innovations

### 1. Nested Pattern/Repetition System

**Problem:** Musical parts have repeating structures at multiple levels (phrase patterns, bar patterns, beat patterns)

**Solution:** Unified `pattern_structure` + `repetitions` + `patterns` system

```json
{
  "pattern_structure": ["A", "B"],
  "repetitions": 2,
  "patterns": {
    "A": [...],
    "B": [...]
  }
}
```

**Benefits:**
- Works for both chords and instrument patterns
- Human-readable structure
- Enforces mathematical constraints naturally
- Scales to any nesting depth

### 2. Anti-Correlated Context

**Problem:** Sequential parts should have dynamic contrast (not all verses should be identical)

**Solution:** Negative context correlation weights

```json
{
  "context": {
    "global.tags": 1.0,
    "parts[-1].part_tags": -0.5,
    "parts[-2].part_tags": -0.3
  }
}
```

**How it works:**
- Positive weight: "pick values that co-occur with this context"
- Negative weight: "pick values that DON'T co-occur with this context"
- Engine adjusts rule scores: `score × context_weight`

**Example:**
- If `parts[-1].part_tags = ["sparse", "mellow"]`
- Rules matching `["sparse"]` or `["mellow"]` get **negative** scores
- This **boosts** opposite tags like `["dense", "energetic"]`

### 3. Duration Constraints

**Problem:** Pattern lengths must sum to part duration

**Solution:** `duration_bars` property that patterns must satisfy

**Constraint formula:**
```python
total_bars = sum(len(patterns[p]) for p in pattern_structure) × repetitions
assert total_bars == duration_bars
```

**Engine behavior:**
- Generate `duration_bars` first
- When sampling patterns, filter candidates by constraint satisfaction
- Rules can encode "pattern A is 2 bars long" as metadata
- Fallback: randomly allocate bars across pattern structure

### 4. Pattern Encoding (String-Based)

**Problem:** Need human-readable, compact representation of rhythmic patterns

**Solution:** String notation where each character represents a sub-division

**Encoding rules:**
- `1` = note/event
- `0` = rest/silence
- `-` = sustain/hold previous note

**Examples:**
```
"1"         → whole note (4 beats)
"11"        → two half notes (beats 1 & 3)
"1010"      → quarter notes (4 events)
"10101010"  → eighth notes (8 events)
"1-10"      → half, quarter rest, quarter
"1---0101"  → whole note, two eighth notes
```

**Benefits:**
- Easy to read/write manually
- Compact storage
- Pattern length = string length / time_division
- Can represent arbitrary rhythmic complexity

## Schema Type Extensions

To support v2, the following new types are introduced:

### `part_tag_list`
Like `tag_list` but:
- Treated as distinct namespace from global tags
- Supports anti-correlation in context
- Used for part-level energy/density descriptors

### `part_dict`
Dictionary of parts keyed by name (`verse_0`, `chorus_0`, etc.)
- Engine iterates through `part_structure` to determine part names
- Each part generated using nested `part_schema`

### `pattern_structure` (composite type)
Contains three sub-fields:
- `pattern_structure`: list of pattern IDs
- `repetitions`: integer
- `patterns`: dictionary mapping IDs to content

### `instrument_dict`
Dictionary keyed by instrument name
- Engine iterates through `instrument_list` to determine keys
- Each instrument gets pattern structure matching `duration_bars`

## Engine Compatibility

### Context Resolution
**Current behavior:** Context is a list `["global.tags", "part_type"]`

**v2 enhancement:** Context can be dict with weights:
```json
{
  "global.tags": 1.0,
  "parts[-1].part_tags": -0.5
}
```

**Implementation:**
```python
def apply_context_weights(rule_score, context_values, context_weights):
    for ctx_item, ctx_weight in context_weights.items():
        if ctx_item in rule.antecedent:
            rule_score *= ctx_weight
    return rule_score
```

### Temporal References
**New syntax:** `parts[-1].property` = previous part's property

**Engine resolution:**
```python
def resolve_context_reference(ref, current_state):
    if "[-" in ref:
        # Extract: parts[-1].part_tags
        container, index, property = parse_temporal_ref(ref)
        index = len(current_state[container]) + int(index)  # -1 becomes last index
        return current_state[container][index][property]
    else:
        # Standard: global.tags
        return current_state[ref]
```

### Pattern Generation
**Constraint-aware sampling:**

```python
def generate_pattern_structure(duration_bars, context):
    # Sample pattern_structure and repetitions
    candidates = []
    for structure in all_structures:
        for reps in range(1, max_reps):
            total = sum(len(patterns[p]) for p in structure) * reps
            if total == duration_bars:
                candidates.append((structure, reps))

    # Weight by context rules
    scores = [score_by_context(c, context) for c in candidates]
    return sample(candidates, weights=scores)
```

## Manual Rules for v2

### Part Tag Rules
```json
{
  "antecedent": ["part_type=verse"],
  "consequent": ["part_tag=sparse", "part_tag=mellow"],
  "confidence": 0.7
}
```

### Pattern Length Rules
```json
{
  "antecedent": ["part_type=chorus", "duration_bars=16"],
  "consequent": ["pattern_repetitions=4"],
  "confidence": 0.8
}
```

### Instrument Pattern Rules
```json
{
  "antecedent": ["instrument=kick", "part_tag=dense"],
  "consequent": ["pattern=10101010"],
  "confidence": 0.9,
  "note": "Dense parts → eighth-note kick pattern"
}
```

### Anti-Correlation Rules
```json
{
  "antecedent": ["part_tag=sparse", "context.parts[-1].part_tag=sparse"],
  "consequent": ["part_tag=dense"],
  "confidence": 0.6,
  "note": "Manual rule reinforcing anti-correlation"
}
```

## Migration Path

### Phase 1: Schema Definition (This PR)
- Define new schema.json structure ✓
- Document pattern encoding ✓
- Create example outputs ✓

### Phase 2: Engine Extensions (Future)
- Implement context weight multipliers
- Add temporal reference resolution (parts[-1])
- Add constraint-aware pattern sampling
- Support composite types (pattern_structure, instrument_dict)

### Phase 3: Data & Rules (Future)
- Create part_tag datasets
- Build manual rules for pattern structures
- Add instrument pattern libraries
- Mine temporal part_tag sequences from real songs

## Benefits Summary

✅ **Generic:** No song-specific code in engine
✅ **Expressive:** Captures musical structure naturally
✅ **Constrained:** Duration constraints prevent invalid outputs
✅ **Dynamic:** Anti-correlation creates variation
✅ **Readable:** Pattern encoding is human-friendly
✅ **Scalable:** Pattern system works for simple or complex music

## Calculated Fields

### The Problem
To ensure patterns match `duration_bars`, repetitions must be calculated rather than sampled.

### Formula (Instruments)
```
repetitions = duration_bars / len(pattern_structure)
```

**Example:**
- `duration_bars = 16`
- `pattern_structure = ["A", "B"]` (length = 2)
- `repetitions = 16 / 2 = 8` ✓

### Formula (Chords)
Chords are more complex because each pattern can contain multiple bars:
```
repetitions = duration_bars / sum(len(patterns[p]) for p in pattern_structure)
```

**Example:**
- `duration_bars = 16`
- `pattern_structure = ["A", "B"]`
- `patterns.A = ["I", "vi", "IV", "V"]` (4 chords = 4 bars)
- `patterns.B = ["I", "V", "IV", "V"]` (4 chords = 4 bars)
- `repetitions = 16 / (4 + 4) = 2` ✓

### Implementation
Schema specifies:
```json
{
  "type": "calculated",
  "formula": "duration_bars / len(pattern_structure)"
}
```

Engine behavior:
1. Generate `duration_bars` first
2. Sample `pattern_structure` (context-aware)
3. Calculate `repetitions` using formula
4. If result is not integer, either:
   - Round and accept partial bar at end
   - Resample pattern_structure until divisible
   - Add constraint to pattern_structure sampling

### Edge Cases

**Non-divisible duration:**
- `duration_bars = 16`, `pattern_structure = ["A", "B", "C"]` (length 3)
- `repetitions = 16 / 3 = 5.33...`

**Options:**
1. **Round down:** `repetitions = 5`, total = 15 bars (1 bar short)
2. **Round up:** `repetitions = 6`, total = 18 bars (2 bars over)
3. **Resample:** Try different pattern_structure lengths that divide evenly
4. **Constraint:** Only allow pattern_structure lengths that divide `duration_bars`

**Recommendation:** Option 3 (resample) during generation with fallback to Option 1 (round down) if no divisible structure found after N attempts.

## Open Questions

1. **Pattern normalization:** Should `"1"` and `"1---"` be treated as equivalent?
2. **Time signature:** Currently assumes 4/4. Support for 3/4, 7/8, etc.?
3. **Pattern resolution:** Should patterns resolve to MIDI notes, or stay abstract?
4. **Swing/groove:** How to encode non-quantized rhythms?
5. **Velocity/dynamics:** Include in pattern encoding (e.g., `1v127-0v64`)?
6. **Non-divisible durations:** How strict should the constraint be? Allow partial bars?

## Next Steps

1. Review schema.json structure
2. Validate example outputs match intended behavior
3. Implement engine support for new types
4. Create sample datasets with part_tags and pattern metadata
5. Test generation with temporal anti-correlation
