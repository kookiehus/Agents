import pdfplumber, pypdf, json, sys, io, os, hashlib
from PIL import Image
SRC, OUT = sys.argv[1], sys.argv[2]
pdf = pdfplumber.open(SRC); rd = pypdf.PdfReader(SRC)
SECT = {}
cards = []; saved = {}
def save_img(pageno, name):
    xo = rd.pages[pageno].get('/Resources')['/XObject']
    key = '/' + name
    obj = xo[key]
    ref = obj.indirect_reference.idnum if hasattr(obj,'indirect_reference') and obj.indirect_reference else None
    data = obj.get_data() if False else None
    from pypdf.generic import StreamObject
    im = None
    for i in rd.pages[pageno].images:
        if i.name.split('.')[0] == name.split('.')[0] and (name in i.name or i.name.startswith(name)):
            im = i; break
    return im
for pi, pg in enumerate(pdf.pages):
    chars = pg.chars
    cidx = {(round(c['x0'],1), round(c['top'],1)): c for c in chars}
    words = pg.extract_words(extra_attrs=["fontname","size","non_stroking_color"], keep_blank_chars=True, x_tolerance=4)
    glass = [im for im in pg.images if im['name'].startswith('Glass')]
    if not glass: continue
    # section title: Cormorant 13 chars
    title = ''.join(c['text'] for c in chars if 'Cormorant' in c['fontname'] and abs(c['size']-13)<.5)
    pimgs = {i.name: i for i in rd.pages[pi].images}
    for g in glass:
        gx, gt = g['x0'], g['top']
        inb = lambda o: o['x0']>=gx+10 and o['x1']<=gx+275 and o['top']>=gt+10 and o['bottom']<=gt+275
        card = {'page': pi+1, 'section': title.strip(), 'texts': [], 'shapes': [], 'bottle': None}
        for w in words:
            if not inb(w): continue
            c = cidx[(round(w['x0'],1), round(w['top'],1))]
            base = pg.height - c['matrix'][5]
            card['texts'].append({'x': w['x0']-gx, 'y': base-gt, 'w': w['x1']-w['x0'], 't': w['text'], 'f': w['fontname'].split('+')[1], 's': round(w['size'],2), 'c': list(w['non_stroking_color'])})
        for cv in pg.curves:
            if not inb(cv): continue
            card['shapes'].append({'bbox': [cv['x0']-gx, cv['top']-gt, cv['x1']-gx, cv['bottom']-gt], 'c': list(cv['non_stroking_color']), 'n': len(cv['pts']), 'pts': [[x-gx, y-gt] for x,y in cv['pts']]})
        for im in pg.images:
            if im['name'].startswith('Glass') or not inb(im): continue
            # find pypdf image
            cand = [k for k in pimgs if k.rsplit('.',1)[0] == im['name'] or k.startswith(im['name'])]
            pim = pimgs[cand[0]]
            h = hashlib.md5(pim.data).hexdigest()[:12]
            fn = f'bottles/{h}.png'
            if h not in saved:
                pim.image.save(os.path.join(OUT, fn)); saved[h] = 1
            card['bottle'] = {'file': fn, 'x': im['x0']-gx, 'y': im['top']-gt, 'w': im['x1']-im['x0'], 'h': im['bottom']-im['top']}
        t = card['texts']
        code = [x for x in t if x['f']=='Montserrat-SemiBold' and x['c'][0]>0.9]
        card['code'] = code[0]['t'].strip() if code else '?'
        card['name'] = ' '.join(x['t'].strip() for x in t if x['f']=='Montserrat-SemiBold' and x['c'][0]<0.5)
        card['tags'] = [x['t'].strip() for x in t if x['f']=='Montserrat-Medium' and abs(x['s']-7)<.3]
        card['type'] = ' '.join(x['t'].strip() for x in t if x['f']=='Montserrat-Medium' and abs(x['s']-9)<.3)
        card['notes'] = ' '.join(x['t'].strip() for x in t if x['f']=='Montserrat-Regular' and x['c'][0]<0.3)
        cards.append(card)
json.dump(cards, open(os.path.join(OUT,'cards.json'),'w'), ensure_ascii=False)
# chrome images
for nm in ('BgHead','FootFade','Glass1'):
    for i in rd.pages[0].images:
        if i.name.startswith(nm+'.') or i.name==nm: i.image.save(os.path.join(OUT, nm+'.png')); print(nm, i.image.size, i.image.mode)
from collections import Counter
print(len(cards), Counter(c['section'] for c in cards))
for c in cards: print(c['page'], c['section'][:4], c['code'], '|', c['name'], '|', c['type'], '|', c['tags'], '|', bool(c['bottle']))
