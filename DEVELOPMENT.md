# Development Guide

This document outlines the workflow for maintaining and updating the Procedural Engine.

## Core Workflow

The typical development loop follows these steps:

1.  **Modify Source**: Update the schema (`schema.json`), dataset configuration (`dataset.json`), or core logic in `engine/`.
2.  **Refresh Model**: Run the automation script to re-mine rules and update sample data.
3.  **Verify**: Cross-check the output via the CLI or the Explorer UI.

### 1. Refreshing the Model

Whenever you change the data source mappings or the schema, you must update the learned association rules and regenerated the samples.

Use the provided convenience script:

```bash
python scripts/refresh_model.py --model song
```

This script performs three critical actions:
- **Rule Mining**: Runs `generate_model_data.py` to extract transactions from CSV/TSV sources and mine association rules using FP-Growth.
- **Embedding Generation**: Runs `generate_embeddings.py` to update the similarity matrix for item libraries (e.g., instruments).
- **Sample Generation**: Runs `generate_samples.py` to produce a fresh set of JSON outputs for the visualization tool.

### 2. Manual Verification (CLI)

To quickly verify that the generator is working correctly without opening the browser:

```bash
python test_generation.py
```

Check the console output to ensure:
- The JSON structure matches the schema.
- Data doesn't "leak" between properties (e.g., genre tags staying in the `genre` field).
- Numeric properties are being discretized into the correct target tags.

### 3. Visual Verification (Explorer UI)

Open `index.html` in your browser.
- **Graph View**: Check the association rules for the model. Use the "Min confidence" and "Min lift" sliders to filter for high-quality rules.
- **Samples View**: Browse the 10 standard prompts in the sidebar to ensure the generated songs look musically coherent.

---

## Technical Maintenance

### Adding a New Data Source
1.  Place the new data file in `models/{model}/data/`.
2.  Add a new entry to the `data_sources` list in `dataset.json`.
3.  Define the `type` (`csv`, `wide_tsv`, or `time_series_dir`) and the `mappings` or `extract` rules.
4.  Run `python scripts/refresh_model.py`.

### Tuning Discretization
If you find that numeric values (like tempo) are being categorized too broadly or narrowly, update the `bins` and `labels` in the `preprocessing` section of `dataset.json`.

---

## Agentic Development

If an AI agent is performing maintenance:
- **Always** run `refresh_model.py` after modifying `dataset.json` or `schema.json`.
- **Always** verify output by grepping `models/{model}/model_data/learned_rules.json` or running `test_generation.py`.
