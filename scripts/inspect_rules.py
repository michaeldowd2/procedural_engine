"""
Inspect mined association rules for a model.

Mines rules inline using the Generator (same path as normal generation).
Run from the project root:
    python scripts/inspect_rules.py
"""
import sys
sys.path.insert(0, '.')
from engine.generator import Generator

gen = Generator('models/song/schema.json', 'models/song/dataset.json')
rules = gen.rule_engine.rules

print(f'Total rules: {len(rules)}')

tag_tag = [r for r in rules
           if all(a.startswith('tags=') for a in r['antecedents'])
           and all(c.startswith('tags=') for c in r['consequents'])]
print(f'Tag→tag rules: {len(tag_tag)}')

print('\nTop 10 by confidence:')
for r in sorted(rules, key=lambda x: -x['confidence'])[:10]:
    print(f"  {sorted(r['antecedents'])} -> {sorted(r['consequents'])}  conf={r['confidence']:.2f}")

print('\nRules fired by {tags=rock}:')
for r in rules:
    if r['antecedents'] == {'tags=rock'}:
        print(f"  -> {sorted(r['consequents'])}  conf={r['confidence']:.2f}")
