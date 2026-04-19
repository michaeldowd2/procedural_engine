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

    def _load_manual_rules(self):
        manual = self.config.get("manual_rules", [])
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

    def query_context(self, current_context_tags):
        # current_context_tags is a set of strings, e.g., {"style=pop", "emotion=happy"}
        matched_consequents = {}
        for rule in self.rules:
            if rule['antecedents'].issubset(current_context_tags):
                for cons in rule['consequents']:
                    if cons not in matched_consequents:
                        matched_consequents[cons] = []
                    matched_consequents[cons].append(rule['confidence'])
        
        # Soft voting / max
        result = {}
        for cons, confs in matched_consequents.items():
            result[cons] = max(confs)
            
        return result
