import json, os, re, sys, hashlib
from PIL import Image, ImageFilter, ImageDraw
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
import pypdf
from reportlab import rl_config
rl_config.useA85 = 0

D, FONTS, SRC, OUT = sys.argv[1:5]
W, H = 841.89, 1190.55
for f in ('Montserrat-Regular','Montserrat-Medium','Montserrat-SemiBold','CormorantGaramond-Medium'):
    pdfmetrics.registerFont(TTFont(f, f'{FONTS}/{f}.ttf'))
sw = pdfmetrics.stringWidth
cards = json.load(open(f'{D}/cards.json'))
cards = [c for c in cards if c['code'] != 'Z2']
PYR = [s for s in cards[0]['shapes'] if s['n'] == 5]
TAGC = {'Цветочные':(0.62,0.397,0.496),'Фруктовые':(0.62,0.446,0.26),'Сладковатые':(0.589,0.372,0.434),'Восточные':(0.434,0.341,0.589),'Сладкие':(0.589,0.341,0.465),'Мускусные':(0.446,0.446,0.589),'Гурманские':(0.527,0.384,0.26),'Свежие':(0.31,0.527,0.527),'Древесные':(0.484,0.384,0.279),'Цитрусовые':(0.589,0.527,0.248),'Пряные':(0.589,0.341,0.248),'Пудровые':(0.558,0.465,0.527),'Фужерные':(0.341,0.527,0.403)}
DARK=(0.17,0.13,0.14); GRAY=(0.47,0.43,0.44); TYPEC=(0.52,0.36,0.31); HEADC=(0.5,0.4,0.38)

NEW = [
 dict(code='K9', section='ПРЕМИУМ', name='BY KILIAN APPLE BRANDY ON THE ROCKS', ru='Килиан Эппл Бренди он зе Рокс', type='Свежий/сладкий', tags=['Фруктовые','Древесные','Пряные'], p=1,
      notes=[('ВЕРХНИЕ НОТЫ','бергамот, ананас, кардамон'),('НОТЫ СЕРДЦА','яблоко, ром, бренди, ананас, ваниль, мох'),('БАЗОВЫЕ НОТЫ','кедр, амброксан')]),
 dict(code='H2', section='УНИСЕКС', name='HORMONE PARIS GABA', ru='Гормон Пари Габа', type='Свежий', tags=['Цитрусовые','Цветочные','Мускусные'], p=2,
      notes=[('ВЕРХНИЕ НОТЫ','итальянский мандарин, апельсин, лаванда'),('НОТЫ СЕРДЦА','османтус, жасмин самбак'),('БАЗОВЫЕ НОТЫ','амброксан, акигалавуд, мускус')]),
 dict(code='C3', section='ЖЕНСКИЕ АРОМАТЫ', name='CAROLINA HERRERA LA BOMBA', ru='Каролина Эррера Ла Бомба', type='Сладкий', tags=['Цветочные','Фруктовые','Восточные'], p=3,
      notes=[('ВЕРХНИЕ НОТЫ','питахайя (драконий фрукт)'),('НОТЫ СЕРДЦА','пион, красный франжипани'),('БАЗОВЫЕ НОТЫ','ваниль, пачули')]),
 dict(code='J7', section='МУЖСКИЕ АРОМАТЫ', name='JEAN PAUL GAULTIER LE MALE ELIXIR', ru='Жан Поль Готье Ле Маль Эликсир', type='Сладкий', tags=['Восточные','Фужерные','Сладкие'], p=4,
      notes=[('ВЕРХНИЕ НОТЫ','лаванда, мята'),('НОТЫ СЕРДЦА','ваниль, бензоин'),('БАЗОВЫЕ НОТЫ','мёд, бобы тонка, табак')]),
 dict(code='L22', section='УНИСЕКС', name='LOUIS VUITTON SYMPHONY', ru='Луи Виттон Симфони', type='Свежий', tags=['Цитрусовые','Пряные','Фужерные','Свежие'], p=5,
      notes=[('ВЕРХНИЕ НОТЫ','грейпфрут, бергамот'),('НОТЫ СЕРДЦА','имбирь'),('БАЗОВЫЕ НОТЫ','мускус')]),
 dict(code='J6', section='ЖЕНСКИЕ АРОМАТЫ', name='JULIETTE HAS A GUN POWDER LOVE', ru='Джульетт Хэз Э Ган Паудер Лав', type='Сладкий', tags=['Сладкие','Мускусные','Пудровые'], p=6,
      notes=[('ВЕРХНИЕ НОТЫ','сахарная вата, малина'),('НОТЫ СЕРДЦА','маршмеллоу, цветок апельсина'),('БАЗОВЫЕ НОТЫ','миндаль, мускус, амброксан, бобы тонка')]),
]

# ---------- photo library (from the new-items file) ----------
LIB = {
 'brandy':   ('p1_ph1', 'ром бренди коньяк виски корица кофе какао шоколад пралине карамел ликер шампанск вино каштан орех'),
 'apple':    ('p1_ph2', 'яблок груш айв киви дын зелен личи бамбук ревень огур арбуз'),
 'pineapple':('p1_ph3', 'ананас манго маракуй тропич персик кокос банан папай абрикос нектарин слив'),
 'osmanthus':('p2_ph1', 'османтус мимоз иланг нарцисс фрези жимолост цветочн липа липов'),
 'mandarin': ('p2_ph2', 'мандарин апельсин танжерин клементин петитгрейн цитрус'),
 'jasmine':  ('p2_ph3', 'жасмин тубероз гардени магноли ландыш лили лотос камели'),
 'peony':    ('p3_ph1', 'пион роз фиалк ирис гелиотроп цикламен гиацинт сирен'),
 'vanilla':  ('p3_ph2', 'ванил тонка сандал древесн кедр кашемир гуаяк дерев берез'),
 'frangip':  ('p3_ph3', 'франжипани орхиде гибискус смородин клубник вишн гранат ягод ежевик питахай клюкв'),
 'honey':    ('p4_ph1', 'мед мёд амбр бензоин смол ладан мирр лабданум шафран амброксан amberwood амбретт'),
 'vanflower':('p4_ph2', 'ванил орхиде молок сливк крем'),
 'tobacco':  ('p4_ph3', 'табак кож уд пачули ветивер мох чай замш дым'),
 'ginger':   ('p5_ph1', 'имбир кардамон перец мускатн гвоздик кориандр тмин элеми можжевел специ'),
 'grapefr':  ('p5_ph2', 'грейпфрут лимон бергамот лайм помело юдзу цедр'),
 'blossom':  ('p5_ph3', 'мускус альдегид лаванд нероли шалфей мята герань розмарин морск водян озон акватич базилик'),
 'marshm':   ('p6_ph1', 'маршмеллоу сахар пудр миндал пирожн зефир конфет'),
 'orblossom':('p6_ph2', 'апельсиновый цветок флердоранж нероли'),
 'cotton':   ('p6_ph3', 'вата малин карамел'),
}
TAGPH = {'Цветочные':['peony','jasmine','osmanthus'],'Фруктовые':['pineapple','apple','frangip'],'Сладковатые':['marshm','cotton'],'Сладкие':['cotton','marshm','honey'],
 'Гурманские':['brandy','marshm','honey'],'Восточные':['honey','vanilla','tobacco'],'Мускусные':['blossom'],'Свежие':['grapefr','blossom','apple'],'Древесные':['vanilla','tobacco'],
 'Цитрусовые':['grapefr','mandarin'],'Водные':['blossom','apple'],'Акватические':['blossom','grapefr'],'Шипровые':['tobacco','grapefr'],'Терпкие':['tobacco','ginger'],'Пряные':['ginger','brandy'],
 'Ванильные':['vanflower','vanilla'],'Пудровые':['marshm','peony'],'Фужерные':['blossom','ginger'],'Спокойные':['blossom'],'Табачные':['tobacco'],'Кожаные':['tobacco'],'Ароматные':['blossom','ginger']}
TYPEPH = {'Сладкий':['honey','peony','marshm'],'Свежий':['grapefr','blossom','apple'],'Свежий/сладкий':['mandarin','jasmine','vanilla']}

def score(text, key):
    t = text.lower().replace('апельсиновый цвет','апельсиновый цветок').replace('цветок апельсина','апельсиновый цветок')
    s = 0
    for kw in LIB[key][1].split(' '):
        if kw == 'апельсиновый': continue
        if kw in ('цветок','флердоранж'): kw = 'апельсиновый цветок' if kw=='цветок' else kw
        n = t.count(kw)
        if key == 'mandarin' and kw == 'апельсин': n -= t.count('апельсиновый цветок')
        s += max(n,0)
    return s

def pick_photos(tiers, tags, typ, code):
    seed = int(hashlib.md5(code.encode()).hexdigest(), 16)
    chosen = []
    def best(text):
        sc = sorted(((score(text,k), -((seed>>i)&7), k) for i,k in enumerate(LIB) if k not in chosen), reverse=True)
        return sc[0][2] if sc and sc[0][0] > 0 else None
    texts = [t for _, t in tiers]
    for t in texts[:3]:
        k = best(t)
        if k: chosen.append(k)
    alltxt = ' '.join(texts)
    while len(chosen) < 3:
        k = best(alltxt)
        if not k: break
        chosen.append(k)
    for src in [p for t in tags for p in TAGPH.get(t, [])] + TYPEPH.get(typ.split()[0] if typ else '', []) + ['peony','vanilla','grapefr','jasmine']:
        if len(chosen) >= 3: break
        if src not in chosen: chosen.append(src)
    return chosen[:3]

os.makedirs(f'{D}/collage', exist_ok=True)
PW, PH = 110.0, 152.0   # panel size, pt
def collage(files):
    key = hashlib.md5('|'.join(files).encode()).hexdigest()[:12]
    fn = f'{D}/collage/{key}.jpg'
    if os.path.exists(fn): return fn
    sc = 3.2; w, h = int(PW*sc), int(PH*sc)
    out = Image.new('RGB', (w, h), 'white'); g = 3
    sw_ = (w - 2*g) // 3
    for i, f in enumerate(files):
        im = Image.open(f'{D}/new/{f}.jpg').convert('RGB')
        r = max(sw_/im.width, h/im.height) * 1.0
        # keep a bit more of the subject: scale so height fits, centre crop width
        im = im.resize((max(sw_, int(im.width*r)), max(h, int(im.height*r))), Image.LANCZOS)
        x = (im.width - sw_)//2; y = (im.height - h)//2
        out.paste(im.crop((x, y, x+sw_, y+h)), (i*(sw_+g), 0))
    out.save(fn, quality=88)
    return fn

def tiers_of(card):
    tiers = []; cur = None
    for t in sorted([t for t in card['texts'] if t['f']=='Montserrat-Regular' and t['x'] > 150], key=lambda t: t['y']):
        if t['c'][0] > 0.4: cur = [t['t'].strip(), '']; tiers.append(cur)
        elif cur: cur[1] += ' ' + t['t']
    return [(a, b) for a, b in tiers]

def codekey(code):
    m = re.match(r'([A-Z]+)(\d+)', code); return (m.group(1), int(m.group(2)))

# ---------- drawing ----------
def rrect(c, x0, top, x1, bottom, col, r=None):
    r = (bottom-top)/2 if r is None else r
    c.setFillColorRGB(*col); c.roundRect(x0, H-bottom, x1-x0, bottom-top, r, stroke=0, fill=1)

def panel(c, gx, gt, files):
    x, top = 21.0, 112.0
    c.saveState()
    p = c.beginPath(); p.roundRect(gx+x, H-(gt+top+PH), PW, PH, 9); c.clipPath(p, stroke=0, fill=0)
    c.drawImage(collage(files), gx+x, H-(gt+top+PH), PW, PH)
    c.restoreState()

def small(fn, hpt):
    """Downsample a bottle cut-out to ~300 dpi at its printed size."""
    os.makedirs(f'{D}/small', exist_ok=True)
    out = f"{D}/small/{os.path.basename(fn)}"
    if not os.path.exists(out):
        im = Image.open(fn); th = int(hpt/72*300)
        if im.height > th: im = im.resize((max(1, round(im.width*th/im.height)), th), Image.LANCZOS)
        im.save(out, optimize=True)
    return out

def draw_glass(c, gx, gt):
    c.drawImage(f'{D}/Glass1.png', gx, H-gt-284, 280.63, 284, mask='auto')

def draw_old(c, card, gx, gt):
    draw_glass(c, gx, gt)
    panel(c, gx, gt, [LIB[k][0] for k in pick_photos(tiers_of(card), card['tags'], card['type'], card['code'])])
    for s in card['shapes']:
        if s['n'] == 10: rrect(c, gx+s['bbox'][0], gt+s['bbox'][1], gx+s['bbox'][2], gt+s['bbox'][3], s['c'])
        else:
            c.setFillColorRGB(*s['c']); p = c.beginPath()
            p.moveTo(gx+s['pts'][0][0], H-(gt+s['pts'][0][1]))
            for a, b in s['pts'][1:]: p.lineTo(gx+a, H-(gt+b))
            p.close(); c.drawPath(p, stroke=0, fill=1)
    b = card['bottle']
    if b: c.drawImage(small(f"{D}/{b['file']}", b['h']), gx+b['x'], H-(gt+b['y']+b['h']), b['w'], b['h'], mask='auto')
    for t in card['texts']:
        c.setFillColorRGB(*t['c']); c.setFont(t['f'], t['s']); c.drawString(gx+t['x'], H-(gt+t['y']), t['t'])

def wrap(text, font, size, width):
    lines = []; cur = ''
    for w in text.split(' '):
        t = (cur + ' ' + w).strip()
        if sw(t, font, size) <= width or not cur: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def draw_new(c, n, gx, gt):
    draw_glass(c, gx, gt)
    panel(c, gx, gt, [f"p{n['p']}_ph{i}" for i in (1,2,3)])
    T = lambda x, y, s, f, sz, col: (c.setFillColorRGB(*col), c.setFont(f, sz), c.drawString(gx+x, H-(gt+y), s))
    rrect(c, gx+26, gt+23.8, gx+62, gt+42.2, (0.3,0.23,0.23))
    T(44 - sw(n['code'],'Montserrat-SemiBold',11)/2, 36.8, n['code'], 'Montserrat-SemiBold', 11, (1,1,1))
    if sw(n['name'], 'Montserrat-SemiBold', 11) <= 186: size, lines, y = 11, [n['name']], 36.6
    else: size, lines, y = 10, wrap(n['name'], 'Montserrat-SemiBold', 10, 186), 37.0
    for ln in lines: T(76, y, ln, 'Montserrat-SemiBold', size, DARK); y += 12.5
    T(76, y, n['ru'], 'Montserrat-Regular', 8, GRAY); y += 13
    T(76, y, n['type'], 'Montserrat-Medium', 9, TYPEC); y += 5.7
    x = 76
    for tag in n['tags']:
        w = sw(tag, 'Montserrat-Medium', 7) + 14
        if x + w > 262: x = 76; y += 14.5
        rrect(c, gx+x, gt+y, gx+x+w, gt+y+12.3, TAGC[tag]); T(x+7, y+8.6, tag, 'Montserrat-Medium', 7, (1,1,1)); x += w + 3.2
    for s in PYR:
        c.setFillColorRGB(*s['c']); p = c.beginPath(); p.moveTo(gx+s['pts'][0][0], H-(gt+s['pts'][0][1]))
        for a, b in s['pts'][1:]: p.lineTo(gx+a, H-(gt+b))
        p.close(); c.drawPath(p, stroke=0, fill=1)
    blocks = [(h, wrap(t, 'Montserrat-Regular', 8, 96)) for h, t in n['notes']]
    nlines = sum(1+len(b) for _, b in blocks)
    gap = (258.0 - 121.6 - (nlines-1)*9.2 + (len(blocks)-1)*9.2) / (len(blocks)-1) - 9.2 + 9.2
    gap = ((258.0-121.6) - (nlines-len(blocks))*9.2) / (len(blocks)-1)
    y = 121.6
    for h, ls in blocks:
        yy = y
        T(167, yy, h, 'Montserrat-Regular', 8, HEADC)
        for ln in ls: yy += 9.2; T(167, yy, ln, 'Montserrat-Regular', 8, DARK)
        y += len(ls)*9.2 + gap
    im = Image.open(f"{D}/new/p{n['p']}_bottle.png"); bb = im.getchannel('A').getbbox()
    cf = f"{D}/new/p{n['p']}_bottle_crop.png"; im.crop(bb).save(cf)
    iw, ih = bb[2]-bb[0], bb[3]-bb[1]; s = min(104/iw, 150/ih); w, h = iw*s, ih*s
    c.drawImage(small(cf, h), gx+76-w/2, H-(gt+266), w, h, mask='auto')

def chrome(c, title):
    c.setFillColorRGB(0.965,0.957,0.961); c.rect(0,0,W,H,stroke=0,fill=1)
    c.drawImage(f'{D}/BgHead.png', 0, H-80, W, 80)
    c.drawImage(f'{D}/logo.png', 42, H-62, 42, 44, mask='auto')
    c.setFillColorRGB(0.97,0.93,0.85); c.setFont('CormorantGaramond-Medium', 28)
    t = c.beginText(106, 1142.1); t.setCharSpace(2.2); t.textOut('ETIB PARFUM'); t.setCharSpace(0); c.drawText(t)
    tw = sw(title, 'CormorantGaramond-Medium', 13) + 3.9*(len(title)-1)
    x0 = 798 - tw
    c.setStrokeColorRGB(0.7,0.5,0.3); c.setLineWidth(0.6); c.line(346, H-39.8, x0-14, H-39.8)
    for r, col in ((3.2,(0.7,0.5,0.3)),(1.2,(0.97,0.93,0.85))):
        c.setFillColorRGB(*col); p = c.beginPath(); cx, cy = 460.4, H-39.8
        p.moveTo(cx-r,cy); p.lineTo(cx,cy+r); p.lineTo(cx+r,cy); p.lineTo(cx,cy-r); p.close(); c.drawPath(p, stroke=0, fill=1)
    c.setFillColorRGB(0.27,0.19,0.17); c.setFont('CormorantGaramond-Medium', 13)
    t = c.beginText(x0, 1146.9); t.setCharSpace(3.9); t.textOut(title); t.setCharSpace(0); c.drawText(t)

def footer(c):
    c.drawImage(f'{D}/FootFade.png', 0, 0, W, 63.5, mask='auto')
    c.setFillColorRGB(0.27,0.19,0.17); c.setFont('Montserrat-Regular', 8)
    s = 'ВСЕ ФЛАКОНЫ АРОМАТОВ ИЗГОТОВЛЕНЫ В ФИРМЕННОМ СТИЛЕ ETIB PARFUM'
    t = c.beginText(217.7, 12.2); t.setCharSpace((624.4-217.7-sw(s,'Montserrat-Regular',8))/(len(s)-1)); t.textOut(s); t.setCharSpace(0); c.drawText(t)

def store_photo(c, top):
    """Shop photo + tagline under the last row of women's cards, feathered into the page."""
    fn = f'{D}/store_feather.png'
    im = Image.open(f'{D}/p8bg.png').convert('RGB')
    cy0, cy1 = int(im.height*0.30), int(im.height*0.90)
    im = im.crop((0, cy0, im.width, cy1))
    m = Image.new('L', im.size, 255); d = ImageDraw.Draw(m); f = 150
    for i in range(f):
        a = int(255*i/f); d.line([(i,0),(i,im.height)], fill=a); d.line([(im.width-1-i,0),(im.width-1-i,im.height)], fill=a)
    mt = Image.new('L', im.size, 255); d = ImageDraw.Draw(mt)
    for i in range(f):
        a = int(255*i/f); d.line([(0,i),(im.width,i)], fill=a); d.line([(0,im.height-1-i),(im.width,im.height-1-i)], fill=a)
    from PIL import ImageChops
    im.putalpha(ImageChops.multiply(m, mt)); im.save(fn)
    avail = (H-63.5-44) - top
    h = avail; w = h*im.width/im.height
    if w > W-60: w = W-60; h = w*im.height/im.width
    c.drawImage(fn, (W-w)/2, H-top-h, w, h, mask='auto')
    c.setFillColorRGB(0.42,0.33,0.30); c.setFont('CormorantGaramond-Medium', 22)
    c.drawCentredString(W/2, 63.5+16, 'Твой аромат — твоё настроение')

ORDER = ['ЖЕНСКИЕ АРОМАТЫ','МУЖСКИЕ АРОМАТЫ','УНИСЕКС','ПРЕМИУМ']
XS = [16.0, 280.5, 545.0]; YS = [78.0, 344.0, 610.0, 876.0]
report = []
def build(section, path):
    items = [('old', c) for c in cards if c['section']==section] + [('new', n) for n in NEW if n['section']==section]
    items.sort(key=lambda it: codekey(it[1]['code']))
    codes = [it[1]['code'] for it in items]; assert len(set(codes)) == len(codes), codes
    report.append((section, codes))
    c = canvas.Canvas(path, pagesize=(W,H), pageCompression=1); c.setTitle('ETIB PARFUM catalog')
    for p0 in range(0, len(items), 12):
        chunk = items[p0:p0+12]
        chrome(c, section)
        if section == ORDER[0] and p0+12 >= len(items) and len(chunk) <= 6:
            store_photo(c, YS[(len(chunk)-1)//3] + 284 + 6)
        for i, (kind, it) in enumerate(chunk):
            (draw_old if kind=='old' else draw_new)(c, it, XS[i%3], YS[i//3])
        footer(c); c.showPage()
    c.save(); return len(range(0, len(items), 12))

src = pypdf.PdfReader(SRC); w = pypdf.PdfWriter()
for sec in ORDER:
    p = f'{D}/sec_{ORDER.index(sec)}.pdf'; build(sec, p)
    for pg in pypdf.PdfReader(p).pages: w.add_page(pg)
    if sec == ORDER[0]:
        w.add_page(src.pages[8]); w.add_page(src.pages[9])
# Re-encode flate RGB images (bottle cut-outs, card glass) as JPEG; alpha masks stay lossless.
import io
from pypdf.generic import NameObject
seen = set()
for pg in w.pages:
    xo = pg['/Resources'].get('/XObject', {})
    for k in xo:
        o = xo[k].get_object()
        if id(o) in seen or o.get('/Subtype') != '/Image': continue
        seen.add(id(o))
        flt = o.get('/Filter'); flt = [flt] if not isinstance(flt, list) else list(flt)
        if flt != ['/FlateDecode'] or o.get('/ColorSpace') != '/DeviceRGB' or o.get('/BitsPerComponent') != 8 or '/DecodeParms' in o: continue
        raw = o.get_data(); wd, ht = o['/Width'], o['/Height']
        if len(raw) != wd*ht*3: continue
        buf = io.BytesIO(); Image.frombytes('RGB', (wd, ht), raw).save(buf, 'JPEG', quality=90, subsampling=0)
        o._data = buf.getvalue(); o[NameObject('/Filter')] = NameObject('/DCTDecode')
w.write(OUT)
for s, codes in report: print(s, len(codes), ' '.join(codes))
print('pages', len(w.pages), os.path.getsize(OUT)//1024, 'KB')
