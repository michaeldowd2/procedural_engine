# Procedural Engine

A Python-based procedural generation system that produces coherent, constraint-aware outputs from schema definitions and learned association rules.

## Core Concept

The engine generates structured JSON outputs where property values maintain meaningful relationships learned from real datasets. It separates *structure* (schema) from *semantics* (association rules mined via FP-Growth).

**Key Features:**
- **Schema-Driven**: Generate arbitrary JSON structures defined in `schema.json`.
- **Inline Rule Mining**: Rules are mined from source data on first use — no pre-generation step required.
- **Deterministic**: Seed-based generation for repeatable results.
- **Controllable Adherence**: `adherence` parameter (0 to 1+) controls how closely outputs follow learned patterns.
- **Bidirectional Inference**: Fixed numeric values automatically inject their discretized tags into context, and vice versa.
- **Explorer UI**: A browser-based tool to browse generated samples and their learned rule connections.

## Architecture

### Engine (`engine/`)

| Module | Role |
|---|---|
| `generator.py` | Orchestrates generation; resolves schema properties in order using rules and embeddings |
| `rule_miner.py` | FP-Growth rule mining from CSV/TSV/time-series sources |
| `rule_engine.py` | Loads and queries association rules against a generation context |
| `schema_parser.py` | Parses and validates `schema.json` |
| `embeddings.py` | Vector similarity for large item libraries (e.g. instruments) |

### Model (`models/<name>/`)

| File | Role |
|---|---|
| `schema.json` | Defines output structure — property names, types, ranges/values |
| `dataset.json` | Data sources, preprocessing bins, item libraries, manual rules |
| `data/` | Source CSV/TSV files used for rule mining |
| `model_data/` | Mined artifacts: `learned_rules.json` |
And at the project root:

| Path | Purpose |
|---|---|
| `output/{model}/generations.json` | Generated samples for the Explorer UI |

### Preprocessing

Preprocessing (numeric→tag binning) is defined **per data source** inside `dataset.json` under each source's `"preprocessing"` key. The generator collects all preprocessing across sources at startup.

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Generate samples for the Explorer

Rules are mined inline automatically on first run:

```bash
python scripts/generate_samples.py --model song
```

This writes `output/song/generations.json`, which the Explorer reads.

### 3. Open the Explorer

Open `index.html` in a browser. Select a generation from the sidebar to visualize its items and rule connections as a force-directed graph. Pinned inputs (fixed values) are highlighted with a gold ring.

### 4. Run a quick generation test

```bash
python test_generation.py
```

## Using the Generator in Code

```python
from engine import Generator

gen = Generator(
    schema_path="models/song/schema.json",
    dataset_path="models/song/dataset.json",
    # generate_rules_inline=True  (default — mines rules from data sources on init)
    # generate_rules_inline=False (reads pre-generated model_data/learned_rules.json)
)

# Unconstrained
song = gen.generate(seed=42, adherence=1.0)

# Constrained — fixed values pin certain properties
song = gen.generate(
    seed=42,
    adherence=0.8,
    fixed_values={"genre": ["rock"], "tags": ["energy_high"]},
)

# With rule edges (for visualisation)
song, edges = gen.generate(seed=42, return_edges=True)
```

## Scripts

| Script | Purpose |
|---|---|
| `scripts/generate_samples.py` | Generate sample outputs for the Explorer UI |
| `scripts/generate_embeddings.py` | Build instrument embeddings (run when instrument data changes) |
| `scripts/generate_model_data.py` | Pre-generate `learned_rules.json` for offline/production use |
| `scripts/refresh_model.py` | Runs all three above in sequence |
| `scripts/inspect_rules.py` | Print mined rule stats for a model |
| `scripts/check_tags.py` | Verify tag dimension constraints across sample seeds |

## Pre-generating Rules (Optional)

By default rules are mined fresh each time `Generator` is instantiated (`generate_rules_inline=True`). For production use or faster startup, pre-generate and cache them:

```bash
python scripts/generate_model_data.py --model song
```

Then use:

```python
gen = Generator(schema_path, dataset_path, generate_rules_inline=False)
```

## Project Structure

```
procedural_engine/
├── engine/
│   ├── generator.py       # Main generation logic
│   ├── rule_miner.py      # FP-Growth rule mining
│   ├── rule_engine.py     # Rule loading and context queries
│   ├── schema_parser.py   # Schema validation
│   └── embeddings.py      # Vector similarity
├── models/
│   └── song/
│       ├── schema.json    # Output structure definition
│       ├── dataset.json   # Data sources, preprocessing, libraries
│       ├── data/          # Source datasets (CSV/TSV)
│       └── model_data/    # Generated: learned_rules.json, generations.json
├── scripts/               # CLI tools (see table above)
├── test_generation.py     # Quick CLI generation test
└── index.html             # Explorer UI
```
