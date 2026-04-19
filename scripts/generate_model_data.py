"""
Mine association rules and export a D3 graph for one or all models.

Usage:
    python scripts/generate_model_data.py               # all models in models/
    python scripts/generate_model_data.py --model song  # specific model
"""
import argparse
import json
import os
import glob
import random
import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import fpgrowth, association_rules
from collections import defaultdict


# ═══════════════════════════════════════════════════════════════════
# Rule mining
# ═══════════════════════════════════════════════════════════════════

def _prune_vocabulary(transactions, min_item_freq):
    if not transactions or min_item_freq <= 0:
        return transactions, set()
    threshold = min_item_freq * len(transactions)
    counts = {}
    for txn in transactions:
        for item in txn:
            counts[item] = counts.get(item, 0) + 1
    keep = {item for item, n in counts.items() if n >= threshold}
    removed = set(counts.keys()) - keep
    pruned = [[item for item in txn if item in keep] for txn in transactions]
    return [t for t in pruned if t], removed


def _extract_csv(source, config, model_dir):
    filepath = os.path.join(model_dir, source["file"])
    if not os.path.exists(filepath):
        print(f"  [SKIP] file not found: {filepath}")
        return []

    delimiter = source.get("delimiter", ",")
    df = pd.read_csv(
        filepath, sep=delimiter, on_bad_lines="skip",
        engine="python" if delimiter != "," else "c",
    )

    preprocessing = config.get("preprocessing", {})
    for col, d_conf in preprocessing.items():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = pd.cut(df[col], bins=d_conf["bins"], labels=d_conf["labels"])

    mappings = source.get("mappings", [])
    extract = source.get("extract", {})
    exclude_suffixes = extract.get("exclude_suffixes", [])
    group_by = source.get("group_by")

    def row_to_items(row):
        items = set()
        for mapping in mappings:
            col, target = mapping["column"], mapping["target"]
            if col in df.columns and pd.notna(row[col]):
                val = str(row[col]).strip()
                if val and not any(val.endswith(s) for s in exclude_suffixes):
                    items.add(f"{target}={val}")
        for col, d_conf in preprocessing.items():
            if col in df.columns and pd.notna(row[col]):
                target = d_conf.get("target", col)
                val = str(row[col])
                if not any(val.endswith(s) for s in exclude_suffixes):
                    items.add(f"{target}={row[col]}")
        if "column" in extract:
            col = extract["column"]
            if col in df.columns and pd.notna(row[col]):
                parts = [p.strip() for p in str(row[col]).split(extract.get("delimiter", ",")) if p.strip()]
                for part in parts:
                    if any(part.endswith(s) for s in exclude_suffixes):
                        continue
                    for pre, target in extract.get("prefixes", {}).items():
                        if part.startswith(pre):
                            items.add(f"{target}={part[len(pre):]}")
                            break
        return items

    if group_by and group_by in df.columns:
        transactions = []
        for _, group in df.groupby(group_by):
            itemset = set()
            for _, row in group.iterrows():
                itemset.update(row_to_items(row))
            if itemset:
                transactions.append(list(itemset))
        return transactions
    else:
        transactions = []
        for _, row in df.iterrows():
            items = row_to_items(row)
            if items:
                transactions.append(list(items))
        return transactions


def _extract_wide_tsv(source, model_dir):
    filepath = os.path.join(model_dir, source["file"])
    if not os.path.exists(filepath):
        print(f"  [SKIP] file not found: {filepath}")
        return []

    extract    = source.get("extract", {})
    prefixes   = extract.get("prefixes", {})
    ex_suffixes = extract.get("exclude_suffixes", [])
    group_col  = source.get("group_by", "TRACK_ID")
    delimiter  = source.get("delimiter", "\t")
    transactions = {}

    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        raw_header = f.readline().rstrip("\n").split(delimiter)
        try:
            group_idx = raw_header.index(group_col)
        except ValueError:
            group_idx = 0
        tag_start = len(raw_header) - 1

        for line in f:
            fields = line.rstrip("\n").split(delimiter)
            if len(fields) <= tag_start:
                continue
            group_key = fields[group_idx].strip()
            if not group_key:
                continue
            raw_tags = [t.strip() for t in fields[tag_start:] if t.strip()]
            if group_key not in transactions:
                transactions[group_key] = set()
            for tag in raw_tags:
                if any(tag.endswith(s) for s in ex_suffixes):
                    continue
                for pre, target in prefixes.items():
                    if tag.startswith(pre):
                        transactions[group_key].add(f"{target}={tag[len(pre):]}")
                        break

    return [list(items) for items in transactions.values() if len(items) > 1]


def _extract_time_series_dir(source, model_dir):
    folder_path = os.path.join(model_dir, source["folder"])
    if not os.path.exists(folder_path):
        print(f"  [SKIP] folder not found: {folder_path}")
        return []

    csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
    print(f"  Found {len(csv_files)} files")
    extract = source.get("extract", {})
    prefixes = extract.get("prefixes", {})
    ex_suffixes = extract.get("exclude_suffixes", [])

    transactions = []
    for file in csv_files:
        try:
            df = pd.read_csv(file)
            df_numeric = df.select_dtypes(include=["number"])
            if df_numeric.empty:
                continue
            max_vals = df_numeric.max()
            itemset = set()
            for col, val in max_vals.items():
                if pd.notna(val) and val > 0.5:
                    if any(col.endswith(s) for s in ex_suffixes):
                        continue
                    for pre, target in prefixes.items():
                        if col.startswith(pre):
                            clean = col[len(pre):].replace("_", " ").strip()
                            itemset.add(f"{target}={clean}")
                            break
            if itemset:
                transactions.append(list(itemset))
        except Exception as e:
            print(f"  Error: {file}: {e}")
    return transactions


def _mine_source(name, transactions, min_support, min_confidence, max_len=4):
    if not transactions:
        print(f"  [SKIP] no transactions")
        return []

    n = len(transactions)
    print(f"  {n} transactions, encoding...")

    te = TransactionEncoder()
    te_ary = te.fit_transform(transactions)
    df = pd.DataFrame(te_ary, columns=te.columns_)
    print(f"  Vocabulary: {len(te.columns_)} unique items  Matrix: {df.shape}")

    freq = fpgrowth(df, min_support=min_support, use_colnames=True, max_len=max_len)
    if freq.empty:
        print(f"  No frequent itemsets at min_support={min_support}")
        return []
    print(f"  Frequent itemsets: {len(freq)}")

    rules_df = association_rules(freq, metric="confidence", min_threshold=min_confidence)
    print(f"  --> {len(rules_df)} rules")

    result = []
    for _, row in rules_df.iterrows():
        result.append({
            "antecedents": sorted(row["antecedents"]),
            "consequents": sorted(row["consequents"]),
            "confidence":  float(row["confidence"]),
            "support":     float(row["support"]),
            "lift":        float(row["lift"]),
            "source":      name,
        })
    return result


def _merge_rules(all_rules):
    best = {}
    for rule in all_rules:
        key = (tuple(sorted(rule["antecedents"])), tuple(sorted(rule["consequents"])))
        if key not in best or rule["confidence"] > best[key]["confidence"]:
            best[key] = rule
    return list(best.values())


def mine_rules(config, model_dir):
    mining_params       = config.get("rule_mining_params", {})
    min_support         = mining_params.get("min_support", 0.05)
    min_confidence      = mining_params.get("min_confidence", 0.3)
    samples_per_source  = mining_params.get("samples_per_source", 5000)
    min_item_freq       = mining_params.get("min_item_freq", 0.01)
    max_antecedent_size = mining_params.get("max_antecedent_size", 3)

    all_rules = []

    for source in config.get("data_sources", []):
        stype = source.get("type", "csv")
        name  = source["name"]
        print(f"\n[{name}] ({stype})")

        if stype == "csv":
            txns = _extract_csv(source, config, model_dir)
        elif stype == "wide_tsv":
            txns = _extract_wide_tsv(source, model_dir)
        elif stype == "time_series_dir":
            txns = _extract_time_series_dir(source, model_dir)
        else:
            print(f"  Unknown type: {stype}")
            continue

        print(f"  Extracted {len(txns)} transactions")

        if samples_per_source and len(txns) > samples_per_source:
            txns = random.sample(txns, samples_per_source)
            print(f"  Sampled down to {samples_per_source} transactions")

        txns, removed_vocab = _prune_vocabulary(txns, min_item_freq)
        if removed_vocab:
            print(f"  Pruned {len(removed_vocab)} rare items (< {min_item_freq * 100:.0f}% freq)")

        per_source_max_ant = source.get("max_antecedent_size", max_antecedent_size)
        source_rules = _mine_source(name, txns, min_support, min_confidence, max_len=per_source_max_ant + 1)
        all_rules.extend(source_rules)
        print(f"  Cumulative total: {len(all_rules)} rules")

    print(f"\nMerging rules from all sources...")
    merged = _merge_rules(all_rules)
    print(f"Final rule count after merge: {len(merged)}")
    return merged


# ═══════════════════════════════════════════════════════════════════
# Graph export
# ═══════════════════════════════════════════════════════════════════

def _group(item_id):
    return item_id.split("=")[0] if "=" in item_id else "unknown"

def _label(item_id):
    return item_id.split("=", 1)[1] if "=" in item_id else item_id

def _score(rule):
    conf = rule.get("confidence", 0.0)
    lift = rule.get("lift", 1.0)
    if lift < 1.1:
        return 0.0
    ant_groups  = {_group(a) for a in rule["antecedents"]}
    cons_groups = {_group(c) for c in rule["consequents"]}
    base = conf * min(lift, 6.0)
    if ant_groups != cons_groups:
        base *= 1.4
    if len(rule["antecedents"]) > 1:
        base *= 1.2
    return base


def export_graph(
    rules,
    out_path,
    min_lift        = 1.2,
    max_rules_total = 1500,
    max_per_source  = 500,
    synonym_groups  = None,
):
    total_loaded = len(rules)
    print(f"\nLoaded {total_loaded:,} rules")

    rules = [r for r in rules if r.get("lift", 1.0) >= min_lift]
    print(f"After lift >= {min_lift}: {len(rules):,} rules remain")

    for r in rules:
        r["_score"] = _score(r)
    rules.sort(key=lambda r: r["_score"], reverse=True)

    per_source = defaultdict(list)
    for r in rules:
        src = r.get("source", "unknown")
        if len(per_source[src]) < max_per_source:
            per_source[src].append(r)

    capped = sorted(
        (r for bucket in per_source.values() for r in bucket),
        key=lambda r: r["_score"], reverse=True,
    )
    selected = capped[:max_rules_total]
    print(f"Selected {len(selected):,} rules for graph")

    src_counts = defaultdict(int)
    for r in selected:
        src_counts[r.get("source", "unknown")] += 1
    for src, n in sorted(src_counts.items()):
        print(f"  {src}: {n:,}")

    nodes    = {}
    edge_map = {}

    for rule in selected:
        ants  = rule["antecedents"]
        cons  = rule["consequents"]
        conf  = rule["confidence"]
        lift  = rule.get("lift", 1.0)
        sup   = rule.get("support", 0.0)
        src   = rule.get("source", "unknown")
        score = rule["_score"]

        rule_label = (
            "if "
            + ", ".join(_label(a) for a in ants)
            + "  →  "
            + ", ".join(_label(c) for c in cons)
            + f"  [conf {conf:.2f} · lift {lift:.2f}]"
        )

        for item in ants + cons:
            if item not in nodes:
                nodes[item] = {"id": item, "group": _group(item),
                               "degree": 0, "_lift_sum": 0.0, "_rule_cnt": 0}
            nodes[item]["degree"]    += 1
            nodes[item]["_lift_sum"] += lift
            nodes[item]["_rule_cnt"] += 1

        for ant in ants:
            for con in cons:
                key = (ant, con)
                if key not in edge_map or score > edge_map[key]["_score"]:
                    edge_map[key] = {
                        "source": ant, "target": con,
                        "value": round(conf, 4), "confidence": round(conf, 4),
                        "lift": round(lift, 3), "support": round(sup, 4),
                        "score": round(score, 3), "rule": rule_label,
                        "dataset": src, "_score": score,
                    }

    # Synonym edges (only between nodes already in the graph)
    for group in (synonym_groups or []):
        present = [item for item in group if item in nodes]
        for i, a in enumerate(present):
            for b in present[i + 1:]:
                if (a, b) not in edge_map and (b, a) not in edge_map:
                    edge_map[(a, b)] = {
                        "source": a, "target": b,
                        "value": 1.0, "confidence": 1.0,
                        "lift": 1.0, "support": 1.0, "score": 0.0,
                        "rule": f"synonym: {_label(a)} ≈ {_label(b)}",
                        "dataset": "synonyms", "type": "synonym", "_score": 0.0,
                    }
                    nodes[a]["degree"] += 1
                    nodes[b]["degree"] += 1

    node_list = []
    for node in nodes.values():
        rc = node.pop("_rule_cnt")
        ls = node.pop("_lift_sum")
        node["lift_avg"] = round(ls / rc, 2) if rc else 1.0
        node_list.append(node)

    links = [{k: v for k, v in e.items() if k != "_score"} for e in edge_map.values()]

    all_lifts = [l["lift"] for l in links]
    meta = {
        "total_rules_in_file": total_loaded,
        "rules_after_lift_filter": len(rules),
        "rules_shown": len(selected),
        "nodes": len(node_list),
        "edges": len(links),
        "min_lift_filter": min_lift,
        "lift_range": (
            [round(min(all_lifts), 2), round(max(all_lifts), 2)] if all_lifts else [0, 0]
        ),
        "sources": dict(sorted(src_counts.items())),
    }

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump({"meta": meta, "nodes": node_list, "links": links}, f)

    print(f"Exported -> {out_path}")
    print(f"  {len(node_list)} nodes, {len(links)} edges")
    print(f"  Lift range: {meta['lift_range'][0]} - {meta['lift_range'][1]}")


# ═══════════════════════════════════════════════════════════════════
# Per-model runner
# ═══════════════════════════════════════════════════════════════════

def run_model(model_dir):
    dataset_path = os.path.join(model_dir, "dataset.json")
    if not os.path.exists(dataset_path):
        print(f"[SKIP] No dataset.json in {model_dir}")
        return

    with open(dataset_path) as f:
        config = json.load(f)

    model_data_dir = os.path.join(model_dir, "model_data")
    os.makedirs(model_data_dir, exist_ok=True)

    rules = mine_rules(config, model_dir)

    rules_path = os.path.join(model_data_dir, "learned_rules.json")
    with open(rules_path, "w") as f:
        json.dump(rules, f, indent=2)

    graph_path = os.path.join(model_data_dir, "graph_data.json")
    export_graph(rules, graph_path, synonym_groups=config.get("tag_synonyms", []))


# ═══════════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mine rules and export graph for model(s).")
    parser.add_argument("--model", help="Model name to process (default: all models in models/)")
    args = parser.parse_args()

    base_dir    = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    models_root = os.path.join(base_dir, "models")

    if args.model:
        model_dirs = [os.path.join(models_root, args.model)]
    else:
        model_dirs = sorted(
            d for d in glob.glob(os.path.join(models_root, "*/"))
            if os.path.isfile(os.path.join(d, "dataset.json"))
        )

    if not model_dirs:
        print("No models found.")
    else:
        for model_dir in model_dirs:
            model_name = os.path.basename(model_dir.rstrip("/\\"))
            print(f"\n{'='*60}")
            print(f"Model: {model_name}")
            print(f"{'='*60}")
            run_model(model_dir)

    # Regenerate manifest
    all_models = sorted(
        os.path.basename(d.rstrip("/\\"))
        for d in glob.glob(os.path.join(models_root, "*/"))
        if os.path.isfile(os.path.join(d, "dataset.json"))
    )
    manifest_path = os.path.join(models_root, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump({"models": all_models}, f, indent=2)
    print(f"\nManifest -> {manifest_path}: {all_models}")
