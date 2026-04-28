# Wave Function Collapse (WFC) Solver

The WFC Solver in this engine is a generic, N-dimensional constraint-satisfaction algorithm designed for procedural generation. Unlike standard WFC implementations that strictly deal with 2D image tiles, this solver is mathematically generic. It reads its dimensions and allowed states directly from the schema and applies context-triggered probabilistic rules.

It can be used to generate anything from 1D musical patterns (kick drums, chord progressions) to 2D game tilemaps, simply by defining a `wfc_grid` property in `schema.json`.

---

## 1. How It Works

1. **Initialization**: The solver initializes an N-dimensional grid where every cell exists in a "superposition" containing all possible states defined by the schema's `domain`.
2. **Rule Application**: Context-triggered rules from `pattern_rules.json` assign probability weights to these states based on their grid coordinates (`index`).
3. **Collapse**: The solver repeatedly finds the cell with the lowest "entropy" (fewest possible states) and collapses it to a single state using the probability weights.
4. **Adherence Scaling**: The engine scales the probability weights based on the global `adherence` parameter (0.0 to 1.0). 
   - `1.0`: Strict adherence. A weight of `0.0` absolutely excludes a state.
   - `0.5`: Looser. The defined weights are favored, but a `0.0` weight scales to `0.5`, making it possible (a "happy accident").
   - `0.0`: Total chaos. All states are assigned a uniform weight of `1.0`.
5. **Propagation**: If an `adjacency` rule dictates that two states cannot be next to each other, collapsing a cell will actively prune invalid states from its neighbors.

---

## 2. Rule Types (`pattern_rules.json`)

Rules are triggered based on the presence of `context_trigger` items (e.g., `["genre=Dance"]`). If the trigger matches the current song's context, the rule applies to the specified `target_property`.

### A. `state_weights`

The most common rule. It assigns relative likelihoods to specific states if the `condition` evaluates to `True`.

**Example: A Four-on-the-Floor Kick Drum**
This requires two rules: one for the downbeats, one for the off-beats.
```json
{
  "context_trigger": ["genre=Dance"],
  "target_property": "kick_pattern",
  "type": "state_weights",
  "condition": "index[0] % 2 == 0",
  "action": {
    "weights": {
      "9": 50.0, 
      "8": 10.0,
      "default": 0.0
    }
  }
}
```
*At `adherence=1.0`, even indices (downbeats) will ONLY generate a `9` or `8`. Everything else (`default: 0.0`) is excluded.*

```json
{
  "context_trigger": ["genre=Dance"],
  "target_property": "kick_pattern",
  "type": "state_weights",
  "condition": "index[0] % 2 != 0",
  "action": {
    "weights": {
      "0": 50.0,
      "default": 0.0
    }
  }
}
```
*Odd indices (off-beats) will ONLY generate a `0` (rest).*

### B. `adjacency`

Prevents `state_2` from appearing at a specific `offset` from `state_1`.

**Example: Prevent Chord V from moving to Chord IV**
```json
{
  "context_trigger": [],
  "target_property": "chord_progression",
  "type": "adjacency",
  "action": {
    "state_1": 5,
    "state_2": 4,
    "offset": [1]
  }
}
```
*If a cell collapses to `5`, the cell at `[index + 1]` will have `4` instantly removed from its allowed states.*

---

## 3. Condition Strings

The `condition` string in a `state_weights` rule is evaluated as raw Python code. It has access to a tuple named `index`, representing the coordinate of the cell being evaluated.

- **1D Arrays (e.g., Audio Sequences)**: Use `index[0]`.
  - Every 4th step: `"index[0] % 4 == 0"`
  - Specific steps: `"index[0] in [2, 6, 10, 14]"`
  - Always apply: `"True"`

- **2D Arrays (e.g., Tilemaps)**: Use `index[0]` for X and `index[1]` for Y.
  - Borders of a 16x16 map: `"index[0] == 0 or index[0] == 15 or index[1] == 0 or index[1] == 15"`
  - Checkerboard pattern: `"(index[0] + index[1]) % 2 == 0"`

---

## 4. Dictionary Mapping

If a `wfc_grid` property in the schema has a `dictionary_map` key (e.g., `"dictionary_map": "chord_mode_map"`), the solver will look in the `"dictionaries"` object inside `pattern_rules.json` to swap the numeric states for human-readable strings before returning the final JSON.

These dictionaries also use `context_trigger` arrays, allowing you to output completely different strings depending on the context.

**Example:**
```json
"dictionaries": {
  "chord_mode_map": [
    {
      "context_trigger": ["mode=major"],
      "mapping": { "1": "I", "2": "ii", "-1": "hold" }
    },
    {
      "context_trigger": ["mode=minor"],
      "mapping": { "1": "i", "2": "ii°", "-1": "hold" }
    }
  ]
}
```

---

## Summary for LLM Assistants

When asked by the User to create a new musical rhythm, map layout, or pattern constraint:
1. Identify the target property (e.g., `kick_pattern`).
2. Identify the mathematical grid coordinate logic required (e.g., `index[0] in [4, 12]` for a snare drum backbeat).
3. Determine the required `state_weights`. Use `0.0` to exclude something completely at maximum adherence, and large numbers (e.g., `50.0`) to strongly enforce something. Always provide a `"default"` key.
4. Add the rule to the `rules` array in `models/song/data/pattern_rules.json`.
