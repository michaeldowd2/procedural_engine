import random
import numpy as np
from .base_handler import PropertyHandler

class ItemListHandler(PropertyHandler):
    def handle(self, prop, context_items, output, generator, adherence):
        name = prop["name"]
        count = random.randint(prop.get("min_items", 1), prop.get("max_items", 4))
        lib = prop.get("item_library")
        lib_items = generator.embeddings_manager.get_library_items(lib)
        if not lib_items:
            output[name] = []
            return
        count = min(count, len(lib_items))

        # Query rule probabilities from the rule engine
        rule_probs = generator.rule_engine.query_context(context_items)

        # Extract all values from the current context items for faster metadata matching
        ctx_vals = set()
        for ctx in context_items:
            if "=" in ctx:
                ctx_vals.add(ctx.split("=", 1)[1].lower())

        scores = {}
        for item_id in lib_items:
            score = 0.1  # base probability
            
            # Rule boost
            score += rule_probs.get(f"{name}={item_id}", 0.0)

            # Metadata overlap boost
            metadata = generator.embeddings_manager.get_item_metadata(lib, item_id)
            if metadata:
                for k, v in metadata.items():
                    if k in ("id", "name", "description", "note"):
                        continue
                    if isinstance(v, list):
                        for val in v:
                            if str(val).lower() in ctx_vals:
                                score += 1.0
                    elif isinstance(v, str):
                        if str(v).lower() in ctx_vals:
                            score += 1.0
            
            scores[item_id] = score

        # Apply temperature-scaled softmax
        temperature = 1.0 / adherence if adherence > 0 else 1.0
        vals = list(scores.keys())
        s = np.array(list(scores.values()), dtype=float)
        s = s - np.max(s)
        probs = np.exp(s / temperature)
        probs = probs / probs.sum()

        chosen = np.random.choice(vals, size=count, p=probs, replace=False).tolist()
        output[name] = chosen
        for c in chosen:
            context_items.add(f"{name}={c}")
