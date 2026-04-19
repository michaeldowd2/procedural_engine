# Procedural Engine

A Python-based procedural generation system that produces coherent, constraint-aware outputs from schema definitions and learned association rules.

## Core Concept

The Procedural Engine generates structured JSON outputs where property values maintain meaningful relationships learned from datasets. It works by separating *structure* (schema) from *semantics* (association rules).

**Key Features:**
- **Schema-Driven**: Generate arbitrary JSON structures defined by a schema.
- **Association Learning**: Learns multi-dimensional relationships from datasets using rule-mining (FP-Growth).
- **Deterministic**: Supports seed-based generation for repeatable results.
- **Controllable Adherence**: Adjust the `adherence` parameter (0 to 1+) to control how closely the generator follows learned patterns.
- **Bidirectional Inference**: Supports fixed values with type-aware inference (e.g., setting a numeric value automatically injects its discretized tag into the context).
- **Explorer UI**: A web-based visualization tool to inspect learned rules and generated samples.

## Architecture

### 1. Association Rules
The core "intelligence" of the engine. Rules are mined from datasets and capture relationships like `{tag_A, tag_B} → {tag_C}` with specific confidence and lift scores.

### 2. Item Embeddings
Dense vector representations are used for large item libraries. This allows the engine to transfer learned associations from one item to similar items based on vector distance, handling data sparsity effectively.

### 3. Discretization & Bins
Continuous numeric properties (like tempo or energy) are mapped to discrete tags during generation. This allows the rule engine to treat numeric ranges as categorical concepts, enabling complex cross-dimension associations.

## Explorer UI

The project includes a built-in **Procedural Engine Explorer** (`index.html`). This tool allows you to:
- Visualize the network of association rules as a force-directed graph.
- Filter rules by confidence, lift, and data source.
- Browse and inspect generated samples in real-time.

To use the explorer, simply open `index.html` in a modern web browser.

## Project Structure

```text
procedural_engine/
├── engine/              # Core generation engine (Python)
│   ├── generator.py     # Main generation logic
│   ├── rule_engine.py   # Association rule querying
│   ├── schema_parser.py # Schema validation and parsing
│   └── embeddings.py    # Vector similarity management
├── models/              # Domain-specific models
│   └── song/            # Music composition model
│       ├── schema.json  # Structure definition
│       ├── dataset.json # Rule configuration & discretization
│       └── data/        # Source CSV/JSON datasets
├── scripts/             # Data processing and generation tools
│   ├── generate_model_data.py # Mines rules and builds graph data
│   ├── generate_samples.py    # Batch generation for the explorer
│   └── generate_embeddings.py # Builds vector models
├── test_generation.py   # Simple CLI test script
└── index.html           # Explorer UI
```

## Quick Start

### 1. Installation
Ensure you have Python 3.8+ installed.
```bash
pip install -r requirements.txt
```

### 2. Prepare Data (Optional)
If you want to rebuild the association rules for the song model:
```bash
python scripts/generate_model_data.py --model song
```

### 3. Generate Samples
Generate a batch of samples for the Explorer UI:
```bash
python scripts/generate_samples.py --model song --count 10
```

### 4. Run CLI Test
Run the simple test script to see the generator in action:
```bash
python test_generation.py
```

### 5. Open Explorer
Open `index.html` in your browser to visualize the rules and browse the samples you just generated.

## Status

**Alpha Implementation**. The core engine is functional and optimized for procedural music composition, but the APIs are still subject to change.
