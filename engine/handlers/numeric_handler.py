import random
from .base_handler import PropertyHandler

class NumericHandler(PropertyHandler):
    def handle(self, prop, context_items, output, generator, adherence):
        name = prop["name"]
        min_v, max_v = prop["range"]

        # Pass 2: check if an item already in context narrows the range
        constrained = generator._item_to_numeric_range(name, context_items)
        if constrained:
            lo, hi = constrained
            lo = max(int(lo), int(min_v))
            hi = min(int(hi), int(max_v))
        else:
            lo, hi = int(min_v), int(max_v)

        value = random.randint(lo, hi)
        output[name] = value
        context_items.add(f"{name}={value}")

        # Pass 1b: discretize the freshly sampled numeric value and inject item
        d_conf_for_prop = generator.preprocessing.get(name, {})
        if d_conf_for_prop.get("inject_on_sample", True) is not False:
            result = generator._discretize_value(name, value)
            if result:
                target_prop, label = result
                context_items.add(f"{target_prop}={label}")
                # Auto-inject into the target list if it was already generated or is pre-filled
                if target_prop in output and isinstance(output[target_prop], list):
                    if label not in output[target_prop]:
                        output[target_prop].append(label)
