import random
import numpy as np
from .base_handler import PropertyHandler

class EntityListHandler(PropertyHandler):
    def handle(self, prop, context_items, output, generator, adherence):
        name = prop["name"]
        
        # Abstract parsing from a string if source_property is provided
        source_prop = prop.get("source_property")
        if source_prop and source_prop in output:
            source_val = output[source_prop]
            delimiter = prop.get("delimiter", "-")
            entities = [p for p in str(source_val).split(delimiter) if p]
        else:
            # Fallback or independent count-based generation
            count = prop.get("count", 1)
            entities = ["entity"] * count

        output[name] = []

        for e in entities:
            entity_dict = {"entity_type": e}
            sub_schema = prop.get("entity_schema", {}).get("properties", [])
            local_context = set(context_items)
            local_context.add(f"entity_type={e}")

            for sub_prop in sub_schema:
                s_name = sub_prop["name"]
                if s_name == "entity_type":
                    continue

                # Pass to appropriate handler if it exists
                handler = generator.get_handler(sub_prop["type"])
                if handler:
                    # We pass entity_dict as the output so it populates locally
                    handler.handle(sub_prop, local_context, entity_dict, generator, adherence)
            output[name].append(entity_dict)
