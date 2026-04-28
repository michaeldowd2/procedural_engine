import numpy as np
from .base_handler import PropertyHandler

class RuleItemListHandler(PropertyHandler):
    def handle(self, prop, context_items, output, generator, adherence):
        name = prop["name"]
        min_count = prop.get("min_items", 1)
        max_count = prop.get("max_items", 5)

        dim_groups = generator._build_dimension_groups(name)
        item_vocab = generator._build_item_vocabulary(name)

        # Build initial pool; pre-exclude siblings of context-pinned labels
        remaining = {t: True for t in item_vocab}
        for ctx_item in context_items:
            if ctx_item.startswith(f"{name}="):
                val = ctx_item.split("=", 1)[1]
                if val in dim_groups:
                    for sibling in dim_groups[val]:
                        if sibling != val:
                            remaining.pop(sibling, None)

        temperature = 1.0 / adherence if adherence > 0 else 1.0
        chosen = []

        # Truly sequential: re-query rules after each pick
        for i in range(max_count):
            if not remaining:
                break

            rule_probs = generator.rule_engine.query_context(context_items)

            # Score each candidate: base + context boost + rule boost
            scores = {}
            for item in remaining:
                score = 0.1
                if f"{name}={item}" in context_items:
                    score += 1.0
                score += rule_probs.get(f"{name}={item}", 0.0)
                scores[item] = score

            # Early stopping: stop after min_count once rule support dries up
            if i >= min_count and max(scores.values()) <= generator.item_confidence_threshold:
                break

            vals = list(scores.keys())
            s = np.array(list(scores.values()), dtype=float)
            s = s - np.max(s)
            probs = np.exp(s / temperature)
            probs = probs / probs.sum()
            pick = np.random.choice(vals, p=probs)
            chosen.append(pick)
            del remaining[pick]
            context_items.add(f"{name}={pick}")

            # Hard-exclude all dimension siblings of the chosen item
            if pick in dim_groups:
                for sibling in dim_groups[pick]:
                    remaining.pop(sibling, None)

        output[name] = chosen
