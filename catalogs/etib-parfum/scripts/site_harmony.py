"""Harmonious note-photo triples for the site cards: for each fragrance pick 3 notes (one per pyramid tier when possible)
and one photo per note so that neighbouring tiles differ in colour and lightness (no tiles that merge), the middle tile
contrasts with both sides, and the same photo is not reused too often.
Usage: python3 site_harmony.py <site dir> <photo root> <choices.json> <out cardphotos.json>"""
import sys, os, json, itertools, re, numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from site_notes_map import theme, SCORE
SITE, ROOT, CHO, OUT = sys.argv[1:5]
cho = json.load(open(CHO))
s = open(f'{SITE}/catalog.html', encoding='utf-8').read()
base = json.loads(s[s.index('/*DATA_START*/') + 14:s.index('/*DATA_END*/')])
def lab(rgb):
    a = rgb / 255.0; a = np.where(a > .04045, ((a + .055) / 1.055) ** 2.4, a / 12.92)
    xyz = a @ np.array([[.4124, .3576, .1805], [.2126, .7152, .0722], [.0193, .1192, .9505]]).T / np.array([.9505, 1, 1.089])
    f = np.where(xyz > .008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)
FEAT = {}
for files in cho.values():
    for f in files:
        im = Image.open(f'{ROOT}/{f}').convert('RGB'); im.thumbnail((120, 120))
        L = lab(np.asarray(im, np.float32)).reshape(-1, 3); FEAT[f] = L.mean(0)
def dE(a, b): return float(np.linalg.norm((FEAT[a] - FEAT[b]) * np.array([1.4, 1, 1])))
use = {}; res = {}
for d in base:
    k = d['category'] + '|' + d['number']
    tiers = [[n.strip() for n in t.split(',') if n.strip()] for _, t in (d.get('pyr') or [['all', d['composition']]])]
    cand = []
    for ti, t in enumerate(tiers):
        for i, n in enumerate(t):
            th = theme(n)
            if th and th in cho and th not in [c[1] for c in cand]: cand.append((ti, th, n, i))
    for th, n in (('musk', 'мускус'), ('woods', 'древесные ноты'), ('amber', 'амбра')):
        if len(cand) < 3 and th not in [c[1] for c in cand]: cand.append((9, th, n, 9))
    cand = cand[:9]; best = None
    for trio in itertools.combinations(cand, 3):
        tiers_ok = len({c[0] for c in trio}); imp = sum(SCORE[c[1]] for c in trio) - .15 * sum(c[3] for c in trio)
        for fs in itertools.product(*[cho[c[1]] for c in trio]):
            for perm in ((0, 1, 2),):
                a, b, c = fs
                d1, d2, d3 = dE(a, b), dE(b, c), dE(a, c)
                Ls = [FEAT[f][0] for f in fs]
                harm = min(min(d1, d2), 45) + .2 * min(d3, 45) - (40 if min(d1, d2) < 18 else 0) - 1.2 * max(0, max(Ls) - min(Ls) - 40)
                reuse = sum(use.get(f, 0) ** 1.3 for f in fs)
                sc = harm + 6 * imp + 12 * tiers_ok - 6 * reuse - (10 if any(c[1] == 'musk' for c in trio) else 0)
                if best is None or sc > best[0]: best = (sc, trio, fs)
    _, trio, fs = best
    pairs = sorted(zip(trio, fs), key=lambda p: p[0][0])        # top → heart → base, left to right
    if min(dE(pairs[0][1], pairs[1][1]), dE(pairs[1][1], pairs[2][1])) < 18:   # never let neighbours merge
        pairs = max(itertools.permutations(pairs), key=lambda q: min(dE(q[0][1], q[1][1]), dE(q[1][1], q[2][1])))
    for _, f in pairs: use[f] = use.get(f, 0) + 1
    res[k] = {'files': [f for _, f in pairs], 'notes': [c[2] for c, _ in pairs]}
json.dump(res, open(OUT, 'w'), ensure_ascii=False, indent=0)
mins = [min(dE(v['files'][0], v['files'][1]), dE(v['files'][1], v['files'][2])) for v in res.values()]
print(len(res), 'cards; neighbour ΔE min/median', round(min(mins)), round(float(np.median(mins))), '; under 18:', sum(m < 18 for m in mins))
