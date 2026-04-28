import json
import os
import random
import numpy as np
from .schema_parser import SchemaParser
from .rule_engine import RuleEngine
from .pattern_rules import PatternRuleEngine
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
        self.pattern_rule_engine = PatternRuleEngine(dataset_path)

        from .handlers import get_default_handlers
        self._handlers = get_default_handlers()

    def get_handler(self, p_type):
        return self._handlers.get(p_type)

    def register_handler(self, p_type, handler):
        self._handlers[p_type] = handler

    def _load_preprocessing(self, dataset_path):
        with open(dataset_path, 'r') as f:
            config = json.load(f)
        gen_params = config.get("generation_params", {})
        self.item_confidence_threshold = gen_params.get("item_confidence_threshold", 0.2)
        merged = {}
        for source in config.get("data_sources", []):
            merged.update(source.get("preprocessing", {}))
        return merged

    def _discretize_value(self, prop_name, value):
        """
        Given a numeric property name and its value, find the matching preprocessing
        bin and return the corresponding label string, or None if no mapping exists.
        Returns (target_property, label).
        """
        d_conf = self.preprocessing.get(prop_name)
        if not d_conf or d_conf.get("type") != "bins":
            return None
        bins = d_conf["bins"]
        labels = d_conf["labels"]
        target = d_conf.get("target", "items")
        for i in range(len(bins) - 1):
            if bins[i] <= value < bins[i + 1]:
                return (target, labels[i])
        # Edge: value == last bin boundary
        if value == bins[-1]:
            return (target, labels[-1])
        return None

    def _item_to_numeric_range(self, prop_name, context_items):
        """
        Pass 2: Given a numeric property name and current context items, check if any
        item in context corresponds to a known discretization label for this property.
        Returns (min, max) tuple to constrain sampling, or None if no match found.
        """
        d_conf = self.preprocessing.get(prop_name)
        if not d_conf or d_conf.get("type") != "bins":
            return None
        bins = d_conf["bins"]
        labels = d_conf["labels"]
        target = d_conf.get("target", "items")
        for i, label in enumerate(labels):
            item_str = f"{target}={label}"
            if item_str in context_items:
                return (bins[i], bins[i + 1])
        return None

    def _build_dimension_groups(self, target_prop):
        """
        Return a dict mapping each discretization label to the set of all sibling
        labels in the same dimension for a specific target property.
        """
        groups = {}  # label -> frozenset of all siblings (including self)
        for prop_name, d_conf in self.preprocessing.items():
            if d_conf.get("type") == "bins" and d_conf.get("target", "items") == target_prop:
                if d_conf.get("inject_on_sample", True) is False:
                    continue
                siblings = frozenset(d_conf["labels"])
                for label in siblings:
                    groups[label] = siblings
        return groups

    def _build_item_vocabulary(self, prop_name):
        """Build all known item values for a specific property from learned rules consequents."""
        vocab = set()
        prefix = f"{prop_name}="
        for rule in self.rule_engine.rules:
            for item in rule["antecedents"].union(rule["consequents"]):
                if item.startswith(prefix):
                    vocab.add(item.split("=", 1)[1])
        
        # Add discretization labels for this specific target property
        for d_conf in self.preprocessing.values():
            if (d_conf.get("type") == "bins"
                    and d_conf.get("target", "items") == prop_name
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

    def _compute_sample_edges(self, context_items):
        best = {}
        for rule in self.rule_engine.rules:
            if (rule['antecedents'].issubset(context_items)
                    and rule['consequents'].issubset(context_items)):
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
        context_items = set()

        # ── Prefill fixed_values & seed context items ──────────────────────────
        for k, v in fixed_values.items():
            output[k] = v
            if isinstance(v, list):
                for item in v:
                    context_items.add(f"{k}={item}")
            else:
                context_items.add(f"{k}={v}")
            # Pass 1a: if the fixed value is numeric, also inject its discretized item
            if isinstance(v, (int, float)):
                result = self._discretize_value(k, v)
                if result:
                    target_prop, label = result
                    context_items.add(f"{target_prop}={label}")
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

            handler = self.get_handler(prop["type"])
            if handler:
                handler.handle(prop, context_items, output, self, adherence)

        if return_edges:
            return output, self._compute_sample_edges(context_items)
        return output

