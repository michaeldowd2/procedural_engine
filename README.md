# Procedural Engine

A generic procedural generation system that produces coherent, constraint-aware outputs from schema definitions and learned associations.

## Core Concept

The Procedural Engine generates structured JSON outputs where property values maintain meaningful relationships learned from datasets. It works across any domain by separating *structure* (schema) from *semantics* (data).

**Key Features:**
- Schema-driven generation of arbitrary JSON structures
- Multi-dimensional association learning from datasets
- Manual rule integration for domain expertise
- Deterministic generation via seed
- Controllable adherence to learned patterns (0=independent, 1=faithful to data)
- Support for fixed values with bidirectional inference

## Architecture

### Three-Component System

**1. Association Rules (Core)**
- Learned from datasets using FP-Growth algorithm
- Captures multi-dimensional relationships: `{item_A, item_B} → {item_C}` with confidence
- Handles categorical properties, tags, and high-level structure

**2. Item Embeddings (Sparsity Handling)**
- Dense vector representations for large item libraries (100s-1000s of items)
- Used when specific items don't appear in dataset
- Transfers learned associations to similar items via similarity metrics

**3. Manual Rules (Domain Expertise)**
- Same format as learned rules, integrated seamlessly
- Allows explicit specification of critical relationships
- Contributes proportionally rather than overriding

### Generation Process

```
For each property in schema order:
  1. Find all rules where antecedent ⊆ current_context
  2. Aggregate confidence scores weighted by rule coverage
  3. For unseen items, smooth scores using embedding similarity
  4. Apply adherence via temperature: probs = softmax(scores, T=1/adherence)
  5. Sample value and add to context
```

**Adherence Parameter:**
- `adherence = 0`: Uniform sampling (independent properties)
- `adherence = 1`: Respects learned associations
- `adherence > 1`: Stronger emphasis on data patterns

### Input/Output

**Inputs:**
- **Schema**: JSON defining output structure, property types, and generation order
- **Dataset**: Learned association rules + optional item embeddings
- **Parameters**: seed, adherence, fixed_values

**Output:**
- JSON object conforming to schema with coherent property values

## Use Cases

The engine is domain-agnostic. Initial focus: procedural music composition.

### Example: Music Composer

Generate complete song structures with:
- High-level properties: tempo, key, mode, tags (genre, mood)
- Structural elements: parts (verse, chorus, bridge)
- Low-level details: chord progressions, MIDI patterns, instrument presets

The engine learns which combinations are musically coherent from datasets and can generate novel but stylistically consistent compositions.

## Project Structure

```
procedural_engine/
├── engine/              # Core generation engine (TBD: Python or JavaScript)
│   ├── schema_parser.py
│   ├── rule_engine.py
│   ├── embeddings.py
│   └── generator.py
├── examples/
│   └── composer/        # Music composition example
│       ├── schema.json
│       ├── dataset.json
│       └── data/        # CSV files, embedding models
├── docs/
│   ├── schema_spec.md
│   ├── dataset_spec.md
│   └── architecture.md
└── README.md
```

## Status

Currently in design phase. Folder structure and specifications being developed.
