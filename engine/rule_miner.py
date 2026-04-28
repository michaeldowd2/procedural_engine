import os
import random
import glob
import numpy as np
import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import fpgrowth, association_rules


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

    preprocessing = source.get("preprocessing", {})
    for col, d_conf in preprocessing.items():
        if col not in df.columns:
            continue
        ptype = d_conf.get("type")
        if ptype == "bins":
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = pd.cut(df[col], bins=d_conf["bins"], labels=d_conf["labels"])
        elif ptype == "add_suffix":
            df[col] = df[col].astype(str).str.strip() + d_conf.get("suffix", "")

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
            if d_conf.get("type") != "bins":
                continue
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

    extract     = source.get("extract", {})
    prefixes    = extract.get("prefixes", {})
    ex_suffixes = extract.get("exclude_suffixes", [])
    group_col   = source.get("group_by", "TRACK_ID")
    delimiter   = source.get("delimiter", "\t")
    transactions = {}

    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        raw_header = f.readline().rstrip("\n").split(delimiter)
        try:
            group_idx = raw_header.index(group_col)
        except ValueError:
            group_idx = 0
        item_start = len(raw_header) - 1

        for line in f:
            fields = line.rstrip("\n").split(delimiter)
            if len(fields) <= item_start:
                continue
            group_key = fields[group_idx].strip()
            if not group_key:
                continue
            raw_items = [t.strip() for t in fields[item_start:] if t.strip()]
            if group_key not in transactions:
                transactions[group_key] = set()
            for item in raw_items:
                if any(item.endswith(s) for s in ex_suffixes):
                    continue
                for pre, target in prefixes.items():
                    if item.startswith(pre):
                        transactions[group_key].add(f"{target}={item[len(pre):]}")
                        break

    return [list(items) for items in transactions.values() if len(items) > 1]


def _extract_time_series_dir(source, model_dir):
    folder_path = os.path.join(model_dir, source["folder"])
    if not os.path.exists(folder_path):
        print(f"  [SKIP] folder not found: {folder_path}")
        return []

    csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
    print(f"  Found {len(csv_files)} files")
    extract     = source.get("extract", {})
    prefixes    = extract.get("prefixes", {})
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
    seed                = mining_params.get("seed", 0)

    random.seed(seed)
    np.random.seed(seed)
    print(f"[mine_rules] seed={seed}")

    all_rules = []

    for source in config.get("data_sources", []):
        stype = source.get("type", "csv")
        name  = source["name"]

        s_support   = source.get("min_support", min_support)
        s_conf      = source.get("min_confidence", min_confidence)
        s_item_freq = source.get("min_item_freq", min_item_freq)
        s_max_ant   = source.get("max_antecedent_size", max_antecedent_size)
        s_samples   = source.get("samples", source.get("samples_per_source", samples_per_source))

        print(f"\n[{name}] ({stype})")
        print(f"  Params: min_support={s_support}, min_conf={s_conf}, min_item_freq={s_item_freq}, max_ant={s_max_ant}, samples={s_samples or 'all'}")

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

        if s_samples and len(txns) > s_samples:
            txns = random.sample(txns, s_samples)
            print(f"  Sampled down to {s_samples} transactions")

        txns, removed_vocab = _prune_vocabulary(txns, s_item_freq)
        if removed_vocab:
            print(f"  Pruned {len(removed_vocab)} rare items (< {s_item_freq * 100:.2f}% freq)")

        source_rules = _mine_source(name, txns, s_support, s_conf, max_len=s_max_ant + 1)
        all_rules.extend(source_rules)
        print(f"  Cumulative total: {len(all_rules)} rules")

    print(f"\nMerging rules from all sources...")
    merged = _merge_rules(all_rules)
    print(f"Final rule count after merge: {len(merged)}")
    return merged
