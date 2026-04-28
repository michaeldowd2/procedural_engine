import json
import os
from typing import List, Dict, Any

class PatternRuleEngine:
    def __init__(self, dataset_path: str):
        self.rules = []
        self.dictionaries = {}
        self.base_dir = os.path.dirname(dataset_path)
        
        with open(dataset_path, 'r') as f:
            self.config = json.load(f)
            
        self._load_pattern_rules()

    def _load_pattern_rules(self):
        pattern_config = self.config.get("pattern_rules", [])
        if isinstance(pattern_config, dict) and "file" in pattern_config:
            file_path = os.path.join(self.base_dir, pattern_config["file"])
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    self.rules = data.get("rules", [])
                    self.dictionaries = data.get("dictionaries", {})
                print(f"[pattern_rules] Loaded {len(self.rules)} rules and {len(self.dictionaries)} dictionaries from {pattern_config['file']}")
            else:
                print(f"[pattern_rules] File not found: {file_path}")
        else:
            print("[pattern_rules] No external pattern_rules file specified in dataset.")

    def get_active_constraints(self, context_items: List[str], target_property: str) -> List[Dict[str, Any]]:
        active = []
        context_set = set(context_items)
        for rule in self.rules:
            if rule.get("target_property") != target_property:
                continue
                
            trigger = set(rule.get("context_trigger", []))
            if trigger.issubset(context_set):
                # Format into constraint
                constraint = {
                    "type": rule["type"],
                    "condition": rule.get("condition", "True")
                }
                
                action = rule.get("action", {})
                if rule["type"] == "state_weights":
                    constraint["weights"] = action.get("weights", {})
                elif rule["type"] == "adjacency":
                    constraint["state_1"] = action.get("state_1")
                    constraint["state_2"] = action.get("state_2")
                    constraint["offset"] = action.get("offset", [1])
                    
                active.append(constraint)
                
        return active

    def get_active_dictionary(self, dict_name: str, context_items: List[str]) -> Dict[str, Any]:
        context_set = set(context_items)
        # Search through dictionaries (if it's a list) or check if dict_name is a group of dicts
        target_dicts = []
        if isinstance(self.dictionaries, list):
            target_dicts = [d for d in self.dictionaries if d.get("name") == dict_name]
        elif isinstance(self.dictionaries, dict):
            # If it's a dict, maybe dict_name is a key to a list of options
            val = self.dictionaries.get(dict_name)
            if isinstance(val, list):
                target_dicts = val
            elif isinstance(val, dict):
                target_dicts = [val]
                
        for dict_config in target_dicts:
            trigger = set(dict_config.get("context_trigger", []))
            if trigger.issubset(context_set) or not trigger:
                return dict_config.get("mapping", {})
            
        return {}
