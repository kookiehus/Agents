"""Beautiful note-photo triples for the site cards, chosen from every photo set (bright v1, moody v2, close-up v3).
Rules: no near-black tiles; the three tiles share lightness and differ in colour without clashing; the right tile sits
behind the bottle, so it must be calm (little detail) and contrast with the bottle's colour. A photo may repeat.
For the owner's 6 novelties the PDF photos are kept, only ordered so the calmest one is behind the bottle.
Usage: python3 site_beauty.py <site dir> <photo root> <pool.json> <cutouts dir> <out cardphotos.json>"""
import sys, os, json, itertools, re, numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from site_notes_map import theme, SCORE
SITE, ROOT, POOL, CUT, OUT = sys.argv[1:6]
pool = json.load(open(POOL))
s = open(f'{SITE}/catalog.html', encoding='utf-8').read()
base = json.loads(s[s.index('/*DATA_START*/') + 14:s.index('/*DATA_END*/')])
def lab(rgb):
    a = rgb / 255.0; a = np.where(a > .04045, ((a + .055) / 1.055) ** 2.4, a / 12.92)
    xyz = a @ np.array([[.4124, .3576, .1805], [.2126, .7152, .0722], [.0193, .1192, .9505]]).T / np.array([.9505, 1, 1.089])
    f = np.where(xyz > .008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)
F = {}
def feat(f):
    if f not in F:
        im = Image.open(f'{ROOT}/{f}').convert('RGB'); W, H = 150, 240; k = max(W / im.width, H / im.height) * 1.25
        im = im.resize((int(im.width * k) + 1, int(im.height * k) + 1)); x, y = (im.width - W) // 2, (im.height - H) // 2
        a = np.asarray(im.crop((x, y, x + W, y + H)), np.float32); L = lab(a)
        g = np.abs(np.diff(L[..., 0], axis=0)).mean() + np.abs(np.diff(L[..., 0], axis=1)).mean()
        F[f] = dict(lab=L.reshape(-1, 3).mean(0), L=float(L[..., 0].mean()), busy=float(g), chroma=float(np.hypot(L[..., 1], L[..., 2]).mean()))
    return F[f]
def dE(a, b): return float(np.linalg.norm(feat(a)['lab'] - feat(b)['lab']))
def quality(f):
    x = feat(f); q = 0
    q -= max(0, 30 - x['L']) * 2.2          # not too dark
    q -= max(0, x['L'] - 72) * 1.5          # not washed out
    q -= max(0, x['chroma'] - 48) * .8      # not candy
    return q
for k_, v in list(pool.items()):
    for f in v: feat(f)
    pool[k_] = sorted(v, key=lambda f: -quality(f))[:6]          # best 6 per note
BT = {}
for c in json.load(open(f'{CUT}/list.json')):
    a = np.asarray(Image.open(f"{CUT}/{c['file']}").convert('RGBA'), np.float32); m = a[..., 3] > 200
    BT[(c['sec'], c['code'])] = lab(a[..., :3][m]).mean(0) if m.any() else np.array([50, 0, 0])
def trio_score(fs, bottle):
    a, b, c = fs; Ls = [feat(f)['L'] for f in fs]
    sc = sum(quality(f) for f in fs)
    for x, y in ((a, b), (b, c)):
        d = dE(x, y); sc += min(d, 40) - (30 if d < 14 else 0) - max(0, d - 75) * .6
    sc -= max(0, max(Ls) - min(Ls) - 28) * 1.2                 # one lightness family
    r = feat(c); sc -= max(0, r['busy'] - 5) * 5.0              # calm behind the bottle
    sc += min(float(np.linalg.norm(r['lab'] - bottle)), 45) * .7  # bottle stands out
    return sc
PDF = {'ПРЕМИУМ|K9': [4, 1, 0], 'УНИСЕКС|H2': [6, 7, 5], 'ЖЕНСКИЕ|C3': [11, 12, 10], 'МУЖСКИЕ|J7': [16, 17, 15], 'УНИСЕКС|L22': [21, 22, 20], 'ЖЕНСКИЕ|J6': [26, 27, 25]}
FIXED = {'ЖЕНСКИЕ|C3': [11, 10, 12]}   # peony, frangipani, vanilla behind the pink bottle
use = {}; res = {}
for d in base:
    k = d['category'] + '|' + d['number']; bottle = BT.get((d['category'][:3], d['number']), np.array([50, 0, 0]))
    if k in PDF:
        fs = [f'pdfimg/im-{j:03d}.png' for j in PDF[k]]
        best = max(itertools.permutations(fs), key=lambda t: trio_score(t, bottle))
        if k in FIXED: best = [f'pdfimg/im-{j:03d}.png' for j in FIXED[k]]
        res[k] = {'files': list(best), 'notes': [], 'pdf': True}; continue
    tiers = [[n.strip() for n in t.split(',') if n.strip()] for _, t in (d.get('pyr') or [['all', d['composition']]])]
    cand = []
    for ti, t in enumerate(tiers):
        for i, n in enumerate(t):
            th = theme(n)
            if th and th in pool and th not in [c[1] for c in cand]: cand.append((ti, th, n, i))
    for th, n in (('woods', 'древесные ноты'), ('amber', 'амбра'), ('musk', 'мускус')):
        if len(cand) < 3 and th not in [c[1] for c in cand]: cand.append((9, th, n, 9))
    cand = cand[:6]; best = None
    for trio in itertools.combinations(cand, 3):
        imp = sum(SCORE[c[1]] for c in trio) - .15 * sum(c[3] for c in trio) + 8 * len({c[0] for c in trio}) - (12 if any(c[1] == 'musk' for c in trio) else 0)
        for perm in itertools.permutations(trio):
            for fs in itertools.product(*[pool[c[1]] for c in perm]):
                sc = trio_score(fs, bottle) + 4 * imp - 2.5 * sum(use.get(f, 0) for f in fs)
                if best is None or sc > best[0]: best = (sc, perm, fs)
    _, perm, fs = best
    for f in fs: use[f] = use.get(f, 0) + 1
    res[k] = {'files': list(fs), 'notes': [c[2] for c in perm]}
json.dump(res, open(OUT, 'w'), ensure_ascii=False, indent=0)
Ls = [feat(f)['L'] for v in res.values() for f in v['files']]
print(len(res), 'cards; tile lightness min/median', round(min(Ls)), round(float(np.median(Ls))), '; right-tile busy median', round(float(np.median([feat(v['files'][2])['busy'] for v in res.values()])), 1))
