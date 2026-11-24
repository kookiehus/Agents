"""Updates the staff website (kookiehus/etibparfum-catalog) from catalogue v58 (first written for v50):
fragrance photos (bottle on the dark warm panel, scripts/site_card_photos.py), note pyramids, fresh/sweet type,
corrected names; new fragrances of the catalogue are added; the trainer's top/heart/base notes follow the pyramids.
Usage: python3 update_site_catalog.py <site repo dir> <site_card_photos out dir>"""
import sys, os, re, json, io, base64, time, glob
from PIL import Image
SITE, CARDS = sys.argv[1:3]
items = json.load(open(f'{CARDS}/items.json', encoding='utf-8'))
pngs = sorted(glob.glob(f'{CARDS}/png/p-*.png'))
assert len(pngs) == len(items)
SEC = {'ЖЕН': 'ЖЕНСКИЕ', 'МУЖ': 'МУЖСКИЕ', 'УНИ': 'УНИСЕКС', 'ПРЕ': 'ПРЕМИУМ'}
LAB = {'ВЕРХНИЕ НОТЫ': 'top', 'НОТЫ СЕРДЦА': 'heart', 'БАЗОВЫЕ НОТЫ': 'base', 'НОТЫ': 'all'}
def typ(pos): return None if pos is None else ('Свежий' if pos < 0.4 else ('Сладкий' if pos > 0.62 else 'Свежий/Сладкий'))
def webp(path):
    b = io.BytesIO(); Image.open(path).convert('RGB').save(b, 'WEBP', quality=82, method=6)
    return 'data:image/webp;base64,' + base64.b64encode(b.getvalue()).decode()
def title(n):
    small = {'DE', 'DI', 'DU', 'LA', 'LE', 'ON', 'THE', 'AND', 'BY', 'OF'}
    w = [x if x in {'D&G', 'CH', 'VIP', 'ETIB', 'XS', 'MFK'} else (x.lower() if i and x in small else x.capitalize()) for i, x in enumerate(n.split())]
    return ' '.join(w).replace("'S ", "'s ")
NAMES = {('T2', 'ЖЕНСКИЕ'): 'Donna Trussardi 1994', ('T15', 'ЖЕНСКИЕ'): 'Trussardi Donna 2011', ('C3', 'ЖЕНСКИЕ'): 'Carolina Herrera La Bomba',
         ('J7', 'МУЖСКИЕ'): 'Jean Paul Gaultier Le Male Elixir', ('D18', 'МУЖСКИЕ'): 'Alfred Dunhill Desire Blue', ('H2', 'УНИСЕКС'): 'Hormone Paris GABA',
         ('C15', 'ПРЕМИУМ'): 'Creed Aventus', ('H1', 'ПРЕМИУМ'): "Haute Fragrance Company Devil's Intrigue 2018",
         ('K5', 'ПРЕМИУМ'): 'Kilian Good Girl Gone Bad', ('L3', 'ПРЕМИУМ'): 'Louis Vuitton Imagination'}   # v124: no (men)/(women)

# ---- catalog.html
p = f'{SITE}/catalog.html'; s = open(p, encoding='utf-8').read()
a = s.index('/*DATA_START*/') + 14; b = s.index('/*DATA_END*/')
base = json.loads(s[a:b])
pa = s.index('/*PH_START*/') + 12; pb = s.index('/*PH_END*/')
photos = json.loads(s[pa:pb])
GROUPS = json.JSONDecoder().raw_decode(s[s.index('const GROUPS=') + 13:])[0]
byk = {(d['number'], d['category']): d for d in base}
added = []
for it, png in zip(items, pngs):
    cat = SEC[it['sec']]; k = (it['code'], cat)
    pyr = [[LAB[h], t] for h, t in it['notes']]
    comp = ', '.join(t for _, t in it['notes'])
    d = byk.get(k)
    if d is None:
        fam = [f'{cat}|{g}' for g in it['tags'] if g in GROUPS.get(cat, [])]
        d = dict(number=it['code'], name=title(it['name']), category=cat, type='Свежий/Сладкий', composition=comp, ph='', families=fam)
        base.append(d); byk[k] = d; added.append(k)
    d['composition'] = comp; d['pyr'] = pyr
    t = typ(it.get('pos'))
    if t: d['type'] = t
    if k in NAMES: d['name'] = NAMES[k]
    key = d.get('ph') or ('e' + it['code'] + it['sec'][0])
    if key.startswith('u'): key = 'e' + it['code'] + it['sec'][0]          # never overwrite a photo uploaded by an admin key
    d['ph'] = key; photos[key] = webp(png)
# keep file order: by category as on the site, then number
order = ['ЖЕНСКИЕ', 'МУЖСКИЕ', 'УНИСЕКС', 'ПРЕМИУМ']
num = lambda n: (n[0], int(re.sub(r'\D', '', n) or 0))
base.sort(key=lambda d: (order.index(d['category']) if d['category'] in order else 9, num(d['number'])))
used = {d['ph'] for d in base if d.get('ph')}
photos = {k: v for k, v in photos.items() if k in used}
s = s[:a] + json.dumps(base, ensure_ascii=False, separators=(',', ':')) + s[b:]
pa = s.index('/*PH_START*/') + 12; pb = s.index('/*PH_END*/')
s = s[:pa] + json.dumps(photos, separators=(',', ':')) + s[pb:]
s = re.sub(r"const VER='\d+'", "const VER='%d'" % int(time.time()*1000), s, count=1)
open(p, 'w', encoding='utf-8').write(s)
print('catalog:', len(base), 'fragrances,', len(photos), 'photos, added', added)

# ---- trainer-data.js: top / heart / base from the pyramids
p = f'{SITE}/trainer-data.js'; t = open(p, encoding='utf-8').read(); i = t.index('window.TR=') + 10
tr = json.loads(t[i:].rstrip().rstrip(';')); byt = {(x['n'], x['c']): x for x in tr}
for d in base:
    k = (d['number'], d['category']); pyr = dict(d.get('pyr') or [])
    if not pyr: continue
    sp = lambda x: [n.strip() for n in x.split(',') if n.strip()]
    top, heart, bas = sp(pyr.get('top', '')), sp(pyr.get('heart', pyr.get('all', ''))), sp(pyr.get('base', ''))
    x = byt.get(k)
    if x is None:
        x = {'c': d['category'], 'n': d['number'], 'nm': d['name'].replace(' - unisex', ''), 't': d['type']}; tr.append(x); byt[k] = x
    x.update(top=top, heart=heart, base=bas, t=d['type'])
    x['nm'] = re.sub(r'\s*-\s*unisex$', '', d['name'], flags=re.I)   # v147: trainer names follow the catalogue
tr.sort(key=lambda x: (order.index(x['c']) if x['c'] in order else 9, num(x['n'])))
open(p, 'w', encoding='utf-8').write(t[:i] + json.dumps(tr, ensure_ascii=False, separators=(',', ':')) + ';\n')
print('trainer:', len(tr))
