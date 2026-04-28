import json
import os

class RuleEngine:
    def __init__(self, dataset_path, inline_rules=None):
        self.rules = []
        self.base_dir = os.path.dirname(dataset_path)
        with open(dataset_path, 'r') as f:
            self.config = json.load(f)

        self._load_manual_rules()
        if inline_rules is not None:
            for r in inline_rules:
                self.rules.append({
                    'antecedents': set(r['antecedents']),
                    'consequents': set(r['consequents']),
                    'confidence': r['confidence']
                })
        else:
            self._load_learned_rules()
        print(f"[rule_engine] Total rules loaded: {len(self.rules)}")

        self.synonyms = {}
        # Load item synonyms for generic abstract matching
        synonym_list = self.config.get("item_synonyms", [])
        for group in synonym_list:
            group_set = set(group)
            for item in group_set:
                self.synonyms.setdefault(item, set()).update(group_set)

    def _load_manual_rules(self):
        manual_config = self.config.get("manual_rules", [])
        if isinstance(manual_config, dict):
            file_path = os.path.join(self.base_dir, manual_config["file"])
            with open(file_path, 'r') as f:
                manual = json.load(f)
            print(f"[manual_rules] Loaded {len(manual)} rules from {manual_config['file']}")
        else:
            manual = manual_config
            if manual:
                print(f"[manual_rules] Loaded {len(manual)} inline rules")
        for r in manual:
            self.rules.append({
                'antecedents': set(r['antecedent']),
                'consequents': set(r['consequent']),
                'confidence': r['confidence']
            })

    def _load_learned_rules(self):
        learned_rules_path = os.path.join(self.base_dir, "model_data", "learned_rules.json")
        if os.path.exists(learned_rules_path):
            with open(learned_rules_path, 'r') as f:
                learned = json.load(f)
                for r in learned:
                    self.rules.append({
                        'antecedents': set(r['antecedents']),
                        'consequents': set(r['consequents']),
                        'confidence': r['confidence']
                    })

    def query_context(self, current_context_items):
        # Expand current context items with any defined synonyms
        expanded_context = set(current_context_items)
        for item in current_context_items:
            if item in self.synonyms:
                expanded_context.update(self.synonyms[item])

        matched_consequents = {}
        for rule in self.rules:
            if rule['antecedents'].issubset(expanded_context):
                for cons in rule['consequents']:
                    if cons not in matched_consequents:
                        matched_consequents[cons] = []
                    matched_consequents[cons].append(rule['confidence'])
        
        # Soft voting / max
        result = {}
        for cons, confs in matched_consequents.items():
            result[cons] = max(confs)
            
        return result
