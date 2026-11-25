"""Pick 3 photo themes (one per pyramid tier when possible) for each fragrance on the staff site.
Usage: python3 site_pick_notes.py <site repo dir> <out json>"""
import sys, json, collections, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from site_notes_map import theme, SCORE
SITE, OUT = sys.argv[1:3]
s = open(f'{SITE}/catalog.html', encoding='utf-8').read()
base = json.loads(s[s.index('/*DATA_START*/') + 14:s.index('/*DATA_END*/')])
res = {}
for d in base:
    tiers = [[n.strip() for n in t.split(',') if n.strip()] for _, t in (d.get('pyr') or [['all', d['composition']]])]
    cand = [(ti, i, theme(n), n) for ti, t in enumerate(tiers) for i, n in enumerate(t) if theme(n)]
    best = lambda pool, used: max((c for c in pool if c[2] not in used), key=lambda c: (SCORE[c[2]], -c[1]), default=None)
    used, pick = set(), []
    if len(tiers) >= 3:
        for ti in range(3):
            c = best([c for c in cand if c[0] == ti], used)
            if c: pick.append(c); used.add(c[2])
    while len(pick) < 3:
        c = best(cand, used)
        if not c: break
        pick.append(c); used.add(c[2])
    for k, c in enumerate(pick):                  # swap abstract picks for a better note of any tier
        if SCORE[c[2]] <= 2:
            alt = best([x for x in cand if SCORE[x[2]] >= 3], used)
            if alt: pick[k] = alt; used.add(alt[2])
    res[d['category'] + '|' + d['number']] = [[c[2], c[3]] for c in pick]
json.dump(res, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
cnt = collections.Counter(t for v in res.values() for t, _ in v)
print(len(res), 'fragrances,', len(cnt), 'themes'); print(cnt.most_common())
print('short:', [k for k, v in res.items() if len(v) < 3])
