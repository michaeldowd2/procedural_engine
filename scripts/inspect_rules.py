import json

with open('models/song/model_data/learned_rules.json') as f:
    rules = json.load(f)

print(f'Total rules: {len(rules)}')

# Show top rules by support
tag_tag = [r for r in rules
           if all(a.startswith('tags=') for a in r['antecedents'])
           and all(c.startswith('tags=') for c in r['consequents'])]
print(f'TagTag rules: {len(tag_tag)}')

print('\nTop 10 by support:')
for r in sorted(rules, key=lambda x: -x['support'])[:10]:
    print(f"  {sorted(r['antecedents'])} -> {sorted(r['consequents'])}  conf={r['confidence']:.2f} sup={r['support']:.4f}")

# Check: are there rules fired when context contains a single tag?
print('\nRules with antecedent = {tags=rock}:')
for r in rules:
    if r['antecedents'] == {'tags=rock'}:
        print(f"  -> {sorted(r['consequents'])}  conf={r['confidence']:.2f} sup={r['support']:.4f}")
