import sys
sys.path.insert(0, '.')
from engine.generator import Generator

g = Generator('models/song/schema.json', 'models/song/dataset.json')

DIMS = {
    'energy': ['low_energy', 'medium_energy', 'high_energy'],
    'mood':   ['dark_mood', 'neutral_mood', 'happy_mood'],
    'tempo':  ['tempo_slow', 'tempo_moderate', 'tempo_fast', 'tempo_very_fast'],
}

ok = True
for seed in [1, 2, 3, 4, 5, 42, 99]:
    song = g.generate(seed=seed, adherence=0.8)
    items = song.get('tags', song.get('items', [])) # Fallback if schema was updated
    violations = []
    for dim, labels in DIMS.items():
        found = [l for l in labels if l in items]
        if len(found) > 1:
            violations.append(f'{dim}: {found}')
    status = 'FAIL ' + str(violations) if violations else 'OK'
    if violations:
        ok = False
    print(f'seed={seed:3d}  tempo={song["tempo"]:3d}  items={items}')
    print(f'         [{status}]')

print()
print('All seeds PASS!' if ok else 'FAILURES DETECTED')
