import json
import os
import random
import numpy as np
from .schema_parser import SchemaParser
from .rule_engine import RuleEngine
from .embeddings import EmbeddingsManager


class Generator:
    def __init__(self, schema_path, dataset_path, generate_rules_inline=True):
        self.schema_parser = SchemaParser(schema_path)
        self.embeddings_manager = EmbeddingsManager(dataset_path)
        self.preprocessing = self._load_preprocessing(dataset_path)

        inline_rules = None
        if generate_rules_inline:
            from .rule_miner import mine_rules
            with open(dataset_path, 'r') as f:
                config = json.load(f)
            model_dir = os.path.dirname(dataset_path)
            inline_rules = mine_rules(config, model_dir)

        self.rule_engine = RuleEngine(dataset_path, inline_rules=inline_rules)

    def _load_preprocessing(self, dataset_path):
        with open(dataset_path, 'r') as f:
            config = json.load(f)
        gen_params = config.get("generation_params", {})
        self.tag_confidence_threshold = gen_params.get("tag_confidence_threshold", 0.2)
        merged = {}
        for source in config.get("data_sources", []):
            merged.update(source.get("preprocessing", {}))
        return merged

    def _discretize_value(self, prop_name, value):
        """
        Given a numeric property name and its value, find the matching preprocessing
        bin and return the corresponding label tag string, or None if no mapping exists.
        Returns (target_property, label).
        """
        d_conf = self.preprocessing.get(prop_name)
        if not d_conf or d_conf.get("type") != "bins":
            return None
        bins = d_conf["bins"]
        labels = d_conf["labels"]
        target = d_conf.get("target", "tags")
        for i in range(len(bins) - 1):
            if bins[i] <= value < bins[i + 1]:
                return (target, labels[i])
        # Edge: value == last bin boundary
        if value == bins[-1]:
            return (target, labels[-1])
        return None

    def _tag_to_numeric_range(self, prop_name, context_tags):
        """
        Pass 2: Given a numeric property name and current context tags, check if any
        tag in context corresponds to a known discretization label for this property.
        Returns (min, max) tuple to constrain sampling, or None if no match found.
        """
        d_conf = self.preprocessing.get(prop_name)
        if not d_conf or d_conf.get("type") != "bins":
            return None
        bins = d_conf["bins"]
        labels = d_conf["labels"]
        target = d_conf.get("target", "tags")
        for i, label in enumerate(labels):
            tag_str = f"{target}={label}"
            if tag_str in context_tags:
                return (bins[i], bins[i + 1])
        return None

    def _build_dimension_groups(self, target_prop):
        """
        Return a dict mapping each discretization label to the set of all sibling
        labels in the same dimension for a specific target property.
        """
        groups = {}  # label -> frozenset of all siblings (including self)
        for prop_name, d_conf in self.preprocessing.items():
            if d_conf.get("type") == "bins" and d_conf.get("target", "tags") == target_prop:
                if d_conf.get("inject_on_sample", True) is False:
                    continue
                siblings = frozenset(d_conf["labels"])
                for label in siblings:
                    groups[label] = siblings
        return groups

    def _build_tag_vocabulary(self, prop_name):
        """Build all known tag values for a specific property from learned rules consequents."""
        vocab = set()
        prefix = f"{prop_name}="
        for rule in self.rule_engine.rules:
            for item in rule["antecedents"].union(rule["consequents"]):
                if item.startswith(prefix):
                    vocab.add(item.split("=", 1)[1])
        
        # Add discretization labels for this specific target property
        for d_conf in self.preprocessing.values():
            if (d_conf.get("type") == "bins"
                    and d_conf.get("target", "tags") == prop_name
                    and d_conf.get("inject_on_sample", True) is not False):
                vocab.update(d_conf["labels"])
        return sorted(vocab)

    def _sample_with_adherence(self, options_probs, adherence):
        """Sample a value from options_probs dict using temperature-scaled softmax."""
        if not options_probs:
            return None
        items = list(options_probs.keys())
        scores = np.array(list(options_probs.values()), dtype=float)
        if adherence == 0:
            probs = np.ones(len(items)) / len(items)
        else:
            temperature = 1.0 / adherence
            scores = scores - np.max(scores)
            exp_scores = np.exp(scores / temperature)
            probs = exp_scores / np.sum(exp_scores)
        return np.random.choice(items, p=probs)

    def _compute_sample_edges(self, context_tags):
        best = {}
        for rule in self.rule_engine.rules:
            if (rule['antecedents'].issubset(context_tags)
                    and rule['consequents'].issubset(context_tags)):
                for ant in rule['antecedents']:
                    for cons in rule['consequents']:
                        if ant == cons:
                            continue
                        key = (ant, cons)
                        if key not in best or rule['confidence'] > best[key]:
                            best[key] = rule['confidence']
        return [{"source": s, "target": t, "confidence": c} for (s, t), c in best.items()]

    def generate(self, seed=None, adherence=1.0, fixed_values=None, return_edges=False):
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

        fixed_values = fixed_values or {}
        output = {}
        context_tags = set()

        # ── Prefill fixed_values & seed context tags ──────────────────────────
        for k, v in fixed_values.items():
            output[k] = v
            if isinstance(v, list):
                for item in v:
                    context_tags.add(f"{k}={item}")
            else:
                context_tags.add(f"{k}={v}")
            # Pass 1a: if the fixed value is numeric, also inject its discretized tag
            if isinstance(v, (int, float)):
                result = self._discretize_value(k, v)
                if result:
                    target_prop, label = result
                    context_tags.add(f"{target_prop}={label}")
                    # Only inject into output if the target property exists in schema
                    # and we want it to be visible in the final JSON.
                    if self.schema_parser.get_property(target_prop):
                        if target_prop not in output:
                            output[target_prop] = []
                        if isinstance(output[target_prop], list) and label not in output[target_prop]:
                            output[target_prop].append(label)

        # ── Resolve global properties in schema order ─────────────────────────
        for prop in self.schema_parser.get_all_properties():
            name = prop["name"]

            if name in output:
                continue

            if prop["type"] == "numeric":
                min_v, max_v = prop["range"]

                # Pass 2: check if a tag already in context narrows the range
                constrained = self._tag_to_numeric_range(name, context_tags)
                if constrained:
                    lo, hi = constrained
                    lo = max(int(lo), int(min_v))
                    hi = min(int(hi), int(max_v))
                else:
                    lo, hi = int(min_v), int(max_v)

                value = random.randint(lo, hi)
                output[name] = value
                context_tags.add(f"{name}={value}")

                # Pass 1b: discretize the freshly sampled numeric value and inject tag
                # (Skipped for properties that set inject_on_sample: false, e.g. target_duration)
                d_conf_for_prop = self.preprocessing.get(name, {})
                if d_conf_for_prop.get("inject_on_sample", True) is not False:
                    result = self._discretize_value(name, value)
                    if result:
                        target_prop, label = result
                        context_tags.add(f"{target_prop}={label}")
                        # Auto-inject into the target list if it was already generated or is pre-filled
                        if target_prop in output and isinstance(output[target_prop], list):
                            if label not in output[target_prop]:
                                output[target_prop].append(label)

            elif prop["type"] == "categorical":
                rule_probs = self.rule_engine.query_context(context_tags)
                options = {v: 0.1 for v in prop["values"]}
                for r_cons, conf in rule_probs.items():
                    if r_cons.startswith(f"{name}="):
                        val = r_cons.split("=", 1)[1]
                        if val in options:
                            options[val] += conf
                chosen = self._sample_with_adherence(options, adherence)
                output[name] = chosen
                context_tags.add(f"{name}={chosen}")

            elif prop["type"] == "tag_list":
                min_count = prop.get("min_items", 1)
                max_count = prop.get("max_items", 5)

                dim_groups = self._build_dimension_groups(name)
                tag_vocab = self._build_tag_vocabulary(name)

                # Build initial pool; pre-exclude siblings of context-pinned labels
                remaining = {t: True for t in tag_vocab}
                for ctx_tag in context_tags:
                    if ctx_tag.startswith(f"{name}="):
                        val = ctx_tag.split("=", 1)[1]
                        if val in dim_groups:
                            for sibling in dim_groups[val]:
                                if sibling != val:
                                    remaining.pop(sibling, None)

                temperature = 1.0 / adherence if adherence > 0 else 1.0
                chosen = []

                # ── Truly sequential: re-query rules after each pick ─────────
                for i in range(max_count):
                    if not remaining:
                        break

                    rule_probs = self.rule_engine.query_context(context_tags)

                    # Score each candidate: base + context boost + rule boost
                    scores = {}
                    for tag in remaining:
                        score = 0.1
                        if f"{name}={tag}" in context_tags:
                            score += 1.0
                        score += rule_probs.get(f"{name}={tag}", 0.0)
                        scores[tag] = score

                    # Early stopping: stop after min_count once rule support dries up
                    if i >= min_count and max(scores.values()) <= self.tag_confidence_threshold:
                        break

                    vals  = list(scores.keys())
                    s     = np.array(list(scores.values()), dtype=float)
                    s     = s - np.max(s)
                    probs = np.exp(s / temperature)
                    probs = probs / probs.sum()
                    pick  = np.random.choice(vals, p=probs)
                    chosen.append(pick)
                    del remaining[pick]
                    context_tags.add(f"{name}={pick}")

                    # Hard-exclude all dimension siblings of the chosen tag
                    if pick in dim_groups:
                        for sibling in dim_groups[pick]:
                            remaining.pop(sibling, None)

                output[name] = chosen
                # context_tags updated inside loop; no further update needed

            elif prop["type"] == "item_list":
                count = random.randint(prop.get("min_items", 1), prop.get("max_items", 4))
                lib = prop.get("item_library")
                lib_items = self.embeddings_manager.get_library_items(lib)
                if not lib_items:
                    output[name] = []
                    continue
                count = min(count, len(lib_items))
                chosen = np.random.choice(lib_items, size=count, replace=False).tolist()
                output[name] = chosen
                for c in chosen:
                    context_tags.add(f"{name}={c}")

            elif prop["type"] == "part_list":
                struct = output.get("structure", "")
                parts = [p for p in struct.split("-") if p]
                output[name] = []

                for p in parts:
                    part_dict = {"part_type": p}
                    sub_schema = prop.get("part_schema", {}).get("properties", [])
                    local_context = set(context_tags)
                    local_context.add(f"part_type={p}")

                    for sub_prop in sub_schema:
                        s_name = sub_prop["name"]
                        if s_name == "part_type":
                            continue

                        if sub_prop["type"] == "tag_list":
                            rule_probs = self.rule_engine.query_context(local_context)
                            sub_opts = {t: 0.1 for t in ["energetic", "driving", "mellow", "upbeat", "dark", "chill"]}
                            for r_cons, conf in rule_probs.items():
                                if r_cons.startswith(f"{s_name}="):
                                    val = r_cons.split("=", 1)[1]
                                    sub_opts[val] = sub_opts.get(val, 0.1) + conf
                            sub_count = random.randint(
                                sub_prop.get("min_items", 1),
                                min(sub_prop.get("max_items", 2), len(sub_opts))
                            )
                            sub_scores = np.array(list(sub_opts.values()), dtype=float)
                            sub_scores /= sub_scores.sum()
                            picked = np.random.choice(list(sub_opts.keys()), size=sub_count, replace=False, p=sub_scores).tolist()
                            part_dict[s_name] = picked
                            for t in picked:
                                local_context.add(f"{s_name}={t}")

                        elif sub_prop["type"] == "item_list":
                            lib = sub_prop.get("item_library")
                            items = self.embeddings_manager.get_library_items(lib)
                            if items:
                                n = random.randint(sub_prop.get("min_items", 2), min(sub_prop.get("max_items", 4), len(items)))
                                part_dict[s_name] = [random.choice(items) for _ in range(n)]
                            else:
                                part_dict[s_name] = []

                    output[name].append(part_dict)

        if return_edges:
            return output, self._compute_sample_edges(context_tags)
        return output
