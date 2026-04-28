from ..wfc_solver import WFCSolver
from typing import Any, Dict

class WFCHandler:
    def handle(self, prop: Dict[str, Any], context_items: set, output: Dict[str, Any], generator: Any, adherence: float):
        dimensions = prop.get("dimensions", [16])
        domain = prop.get("domain", [])
        
        if not domain:
            print(f"[WFCHandler] Warning: No domain specified for {prop['name']}. Skipping.")
            return

        pattern_engine = getattr(generator, "pattern_rule_engine", None)
        constraints = []
        dictionary = {}
        
        if pattern_engine:
            constraints = pattern_engine.get_active_constraints(list(context_items), prop["name"])
            
            dict_map = prop.get("dictionary_map")
            if dict_map:
                dictionary = pattern_engine.get_active_dictionary(dict_map, list(context_items))

        # Initialize solver
        solver = WFCSolver(dimensions, domain)
        
        # Add constraints
        for c in constraints:
            solver.add_constraint(c)
            
        # Solve
        result_dict = solver.solve(max_attempts=20, adherence=adherence)
        
        if result_dict is None:
            print(f"[WFCHandler] Warning: WFC failed to solve for {prop['name']} without contradictions.")
            return
            
        # Format output
        result_list = solver.to_nested_list(result_dict)
        
        # Apply dictionary mapping if applicable
        if dictionary:
            result_list = self._apply_dictionary(result_list, dictionary)
            
        output[prop["name"]] = result_list
        
        # We generally do not inject full WFC grids into context_items as it pollutes the context 
        # unless specifically instructed, so we just return.
        
    def _apply_dictionary(self, data, dictionary):
        if isinstance(data, list):
            return [self._apply_dictionary(item, dictionary) for item in data]
        else:
            # Map if string form of data is in dict, else map data directly, else keep data
            if str(data) in dictionary:
                return dictionary[str(data)]
            return dictionary.get(data, data)
