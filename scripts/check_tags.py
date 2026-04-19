import sys
sys.path.insert(0, '.')
from engine.generator import Generator

g = Generator('models/song/schema.json', 'models/song/dataset.json')

DIMS = {
    'energy': ['energy_low', 'energy_medium', 'energy_high'],
    'mood':   ['mood_dark', 'mood_neutral', 'mood_happy'],
    'tempo':  ['tempo_slow', 'tempo_moderate', 'tempo_fast', 'tempo_very_fast'],
}

ok = True
for seed in [1, 2, 3, 4, 5, 42, 99]:
    song = g.generate(seed=seed, adherence=0.8)
    tags = song['tags']
    violations = []
    for dim, labels in DIMS.items():
        found = [l for l in labels if l in tags]
        if len(found) > 1:
            violations.append(f'{dim}: {found}')
    status = 'FAIL ' + str(violations) if violations else 'OK'
    if violations:
        ok = False
    print(f'seed={seed:3d}  tempo={song["tempo"]:3d}  tags={tags}')
    print(f'         [{status}]')

print()
print('All seeds PASS!' if ok else 'FAILURES DETECTED')
