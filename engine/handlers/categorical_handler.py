from .base_handler import PropertyHandler

class CategoricalHandler(PropertyHandler):
    def handle(self, prop, context_items, output, generator, adherence):
        name = prop["name"]
        rule_probs = generator.rule_engine.query_context(context_items)
        options = {v: 0.1 for v in prop["values"]}
        for r_cons, conf in rule_probs.items():
            if r_cons.startswith(f"{name}="):
                val = r_cons.split("=", 1)[1]
                if val in options:
                    options[val] += conf
        chosen = generator._sample_with_adherence(options, adherence)
        output[name] = chosen
        context_items.add(f"{name}={chosen}")
