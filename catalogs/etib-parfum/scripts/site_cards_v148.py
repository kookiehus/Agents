"""«Новинки»-style fragrance cards for the staff website (kookiehus/etibparfum-catalog), first built for catalogue v147/v148.
Writes <site>/cards.js (window.CARDS) and copies photos to <site>/img/notes and <site>/img/bottles.
Texts: the 6 novelties are taken word for word from the owner's PDF «Маркетинговое описание»; the rest are drafts built
from the pyramid, groups and the «Как продать» tips (ok:false until checked).
Usage: python3 site_cards_v148.py <site dir> <picks.json> <pins dir> <pdf images dir> <cutouts dir> <choices.json>"""
import sys, os, json, re, math, shutil
from PIL import Image
SITE, PICKS, PINS, PDFI, CUT, CHO = sys.argv[1:7]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import site_texts_v149 as TX
ZOOM = float(os.environ.get('NOTE_ZOOM', '1.25'))
CP = json.load(open(os.environ['CARD_PHOTOS'], encoding='utf-8')) if os.environ.get('CARD_PHOTOS') else {}   # crop closer: the note fills the frame
s = open(f'{SITE}/catalog.html', encoding='utf-8').read()
base = json.loads(s[s.index('/*DATA_START*/') + 14:s.index('/*DATA_END*/')])
t = open(f'{SITE}/tips.js', encoding='utf-8').read(); tips = json.loads(t[t.index('window.TIPS=') + 12:].rstrip().rstrip(';'))
picks = json.load(open(PICKS, encoding='utf-8'))
choices = json.load(open(CHO, encoding='utf-8'))          # theme -> list of chosen pin files (in PINS)
nm = lambda d: re.sub(r'\s*-\s*unisex$', '', d['name'], flags=re.I)

BRANDS = ['Avril Lavigne', 'Armand Basi', 'Ariana Grande', 'Givenchy', 'Antonio Banderas', 'Britney Spears', 'Byredo', 'ETIB', 'Etib', 'Bvlgari',
          'Carolina Herrera', 'Chanel', 'Calvin Klein', 'Christian Dior', 'Dior', 'Dolce&Gabbana', 'Dolce & Gabbana', 'D&G', 'Donna Karan', 'Escada',
          'Giorgio Armani', 'Gucci', 'Hugo Boss', 'Jo Malone', 'Jean Paul Gaultier', 'Juliette Has A Gun', 'Juliette Has a Gun', 'Kayali', 'Kenzo',
          'Lancome', 'Lacoste', 'Lanvin', 'Montale', 'Marc Jacobs', 'Moschino', 'Parfums de Marly', 'Parfums De Marly', 'Paco Rabanne',
          "Victoria's Secret", 'Salvatore Ferragamo', 'Trussardi', 'Versace', 'Yves Saint Laurent', 'Zadig & Voltaire', 'Alfred Dunhill', 'Clinique',
          'Hermes', 'Montblanc', 'Attar Collection', 'Amouage', 'Marc-Antoine Barrois', 'Ex Nihilo', 'Essential Parfums', 'Hormone Paris',
          'Louis Vuitton', 'Narcosis', 'By Richard White', 'Vilhelm Parfumerie', 'Zarkoperfume', 'Zielinski & Rozen', 'Clive Christian', 'Creed',
          'Haute Fragrance Company', 'Maison Francis Kurkdjian', 'By Kilian', 'Kilian', 'Le Labo', 'Escentric Molecules', 'Mancera', 'Nishane',
          'Nasomatto', 'Sospiro Perfumes', 'Tom Ford', 'Thomas Kosmala', 'Tiziana Terenzi']
FIX_BRAND = {'Etib': 'ETIB', 'Dolce & Gabbana': 'Dolce&Gabbana', 'D&G': 'Dolce&Gabbana', 'Dior': 'Christian Dior', 'By Kilian': 'Kilian',
             'Parfums De Marly': 'Parfums de Marly', 'Juliette Has a Gun': 'Juliette Has A Gun'}
def brand(n):
    for b in BRANDS:
        if b in n: return FIX_BRAND.get(b, b)
    return ''
SEX = {'ЖЕНСКИЕ': 'женский', 'МУЖСКИЕ': 'мужской', 'УНИСЕКС': 'унисекс'}
SEX_P = {'C15': 'мужской', 'L3': 'мужской', 'H1': 'женский', 'K5': 'женский'}
ADJ = {'Цветочные': 'цветочное', 'Свежие': 'свежее', 'Древесные': 'древесное', 'Сладкие': 'сладкое', 'Пряные': 'пряное', 'Сладковатые': 'сладкое',
       'Фруктовые': 'фруктовое', 'Восточные': 'восточное', 'Пудровые': 'пудровое', 'Гурманские': 'гурманское', 'Восточные выраженные': 'восточное',
       'Ягодные': 'ягодное', 'Фужерные': 'фужерное', 'Цитрусовые': 'цитрусовое', 'Горькие/терпкие': 'терпкое', 'Ванильные': 'ванильное',
       'Шипровые': 'шипровое', 'Восточные сладкие и гурманские': 'гурманское', 'Свежие древесные': 'древесное', 'Терпкие': 'терпкое',
       'Зеленые/травянистые': 'зелёное', 'Чистые, мускусные, воздушные': 'мускусное', 'Терпкие/горькие': 'терпкое',
       'Восточные древесные/пряные': 'восточное', 'Восточные древесные и амбровые': 'амбровое', 'Свежие цитрусовые': 'цитрусовое',
       'Запах чистоты': 'мускусное'}
NOTE_ADJ = [('морск', 'морское'), ('водн', 'водное'), ('амбр', 'амбровое'), ('мускус', 'мускусное'), ('кож', 'кожаное'), ('табак', 'табачное'),
            ('кофе', 'кофейное'), ('уд', 'древесное'), ('ладан', 'смолистое'), ('ром', 'алкогольное'), ('коньяк', 'алкогольное'), ('бренди', 'алкогольное')]
def direction(d):
    out = []
    for f in d.get('families', []):
        a = ADJ.get(f.split('|')[-1])
        if a and a not in out: out.append(a)
    if len(out) < 3:
        comp = d['composition'].lower()
        for w, a in NOTE_ADJ:
            if w in comp and a not in out: out.append(a)
            if len(out) >= 3: break
    if not out: out = ['свежее' if d['type'] == 'Свежий' else 'сладкое']
    return ' · '.join(out[:3])

def season(d):
    tp, fam = d['type'], ' '.join(d.get('families', []))
    if tp == 'Свежий': return 'весна, лето' + (', тёплые вечера' if 'Цветочные' in fam else '')
    if tp == 'Сладкий': return 'осень, зима, прохладные вечера'
    return 'весна, осень, круглый год'
def occasion(d):
    tp, fam = d['type'], ' '.join(d.get('families', []))
    if 'На вечер' in fam or 'Восточные выраженные' in fam: return 'вечерний выход, свидание, праздник'
    if tp == 'Свежий': return 'повседневный, офис, отдых' + (', спорт' if d['category'] == 'МУЖСКИЕ' else '')
    if tp == 'Сладкий': return 'свидание, вечерний выход, праздник'
    return 'повседневный, офис, свидание'
VERB = {'любят': 'любит', 'хотят': 'хочет', 'ценят': 'ценит', 'ищут': 'ищет', 'предпочитают': 'предпочитает', 'выбирают': 'выбирает'}
def style(tip):
    w = (tip.get('whom') or '').split('. ')[0].rstrip('.')
    m = re.match(r'Для [^,]+, (?:которые|кто) (\S+)(.*)', w)
    if not m: return w[:1].lower() + w[1:] if w else ''
    return 'для тех, кто ' + VERB.get(m.group(1), m.group(1)) + m.group(2)
def tiers(d):
    return {k: [n.strip() for n in v.split(',') if n.strip()] for k, v in (d.get('pyr') or [])}
def lst(xs):
    xs = xs[:3]
    return xs[0] if len(xs) == 1 else ', '.join(xs[:-1]) + ' и ' + xs[-1]
def sound(d):
    p = tiers(d)
    if 'all' in p or not p:
        txt = f"Аромат строится вокруг нот: {lst(p.get('all') or [n.strip() for n in d['composition'].split(',')])}."
    else:
        parts = []
        if p.get('top'): parts.append(f"В начале звучат {lst(p['top'])}.")
        if p.get('heart'): parts.append(f"Затем раскрываются {lst(p['heart'])}.")
        if p.get('base'): parts.append(f"В шлейфе остаются {lst(p['base'])}.")
        txt = ' '.join(parts)
    tail = {'Свежий': 'Звучит легко, чисто и прозрачно.', 'Сладкий': 'Звучит тепло, мягко и обволакивающе.'}.get(d['type'], 'Баланс свежести и мягкой сладости.')
    return txt + ' ' + tail
def marketing(tip):
    h = tip.get('hooks') or []
    return ' '.join([tip.get('how', '')] + h[:2]).strip()

# ---- the owner's PDF (6 novelties): exact texts and photos
PDF = {
 'ПРЕМИУМ|K9': dict(dir='алкогольное · фруктовое · древесное', brand='Kilian', sex='унисекс', season='осень, зима, прохладные вечера',
   occ='свидание, бар, ужин, вечерний выход', style='для тех, кто хочет алкогольный аромат, но без тяжёлой сладости',
   top='бергамот, ананас, кардамон', heart='яблоко, ром, бренди, ананас, ваниль, мох', base='кедр, амброксан',
   sound='«Яблочный бренди со льдом» — холодное фруктовое начало с бергамотом и ананасом, затем раскрывается яблочно-алкогольная середина с ромом и ванилью, а в базе остаётся чистый древесный амброксан. Не приторный, с ощущением прохлады.',
   mkt='Ночь, лёд и яблочный бренди в одном флаконе. Ледяной старт бергамота и ананаса, тёплое сердце из яблока, рома и ванили, древесный шлейф кедра и амброксана. Аромат для тех, кто хочет быть в центре вечера — дерзкий, свежий, алкогольный, без приторной сладости. Раскрывается на коже теплом, идеален для осени, зимы и незабываемых свиданий.',
   img=[4, 1, 0], col='green'),
 'УНИСЕКС|H2': dict(dir='цитрусовое · цветочное · мускусное', brand='Hormone Paris', sex='унисекс', season='весна, лето, тёплые вечера',
   occ='повседневный, офис, отдых', style='для тех, кто ищет современный молекулярный аромат с минеральной прохладой',
   top='итальянский мандарин, апельсин, лаванда', heart='османтус, жасмин самбак', base='амброксан, акигалавуд, мускус',
   sound='Яркий цитрусовый старт с мандарином и апельсином, смягчённый прохладной лавандой. В сердце нежный османтус с абрикосовым оттенком и чистый жасмин. База минеральная, с амброксаном и древесным акигалавудом, оставляющая лёгкий мускусный шлейф.',
   mkt='Свежий фужерный аромат с ярким фруктовым стартом мандарина и маракуйи, цветочным сердцем из фрезии, жасмина и ландыша и тёплой амброво-мшистой базой. Унисекс, стойкий и универсальный — он одинаково хорош в офисе, на прогулке и на вечернем свидании. Для тех, кто хочет звучать свежо, элегантно и уверенно каждый день.',
   img=[6, 7, 5], col='yellow'),
 'ЖЕНСКИЕ|C3': dict(dir='цветочное · фруктовое · амбровое', brand='Carolina Herrera', sex='женский', season='весна',
   occ='повседневный, свидание, вечерний выход, праздник', style='для тех, кто любит яркие фруктово-цветочные ароматы с тёплой амбровой базой и хочет звучать смело и жизнерадостно',
   top='питахайя (драконий фрукт)', heart='пион, красный франжипани', base='ваниль, пачули',
   sound='Сочная экзотическая питахайя, яркая и мгновенно привлекающая внимание. В сердце раскрывается пышный пион с вишнёвым оттенком и солнечный красный франжипани. База — гладкая тёплая ваниль с лёгкой мшистостью пачули, оставляющая мягкий, обволакивающий шлейф.',
   mkt='Взрывная цветочно-фруктовая композиция с экзотической питахайей, пышным пионом и тёплой солнечной ванилью. Для женщин, которые живут громко, свободно и не боятся быть в центре внимания — от повседневных дней до ярких вечеров.',
   img=[11, 12, 10], col='pink'),
 'МУЖСКИЕ|J7': dict(dir='восточное · фужерное · амбровое', brand='Jean Paul Gaultier', sex='мужской', season='осень, зима, прохладные вечера',
   occ='свидание, вечерний выход, праздник, холодная погода', style='для тех, кто любит сладкие, медово-табачные ароматы с мощной амбровой базой и хочет звучать чувственно и уверенно',
   top='лаванда, мята', heart='ваниль, бензоин', base='мёд, бобы тонка, табак',
   sound='Прохладная лаванда и мята, освежающий и бодрящий старт. В сердце раскрывается густая сладкая ваниль с бальзамическим бензоином, который придаёт глубину и смолистую теплоту. База — насыщенный мёд, миндально-пудровые бобы тонка и дымный табак, создающие обволакивающий, чувственный шлейф.',
   mkt='Концентрат мужского обаяния: свежая лаванда и мята открывают композицию, а затем она погружается в густую медово-табачную сладость с ванилью и бензоином. Мощный, стойкий и чувственный — для холодных вечеров, свиданий и выходов, где нужно произвести впечатление.',
   img=[16, 17, 15], col='brown'),
 'УНИСЕКС|L22': dict(dir='цитрусовое · свежее пряное · фужерное', brand='Louis Vuitton', sex='унисекс', season='весна, лето, жаркая погода',
   occ='повседневный, офис, отдых, путешествия', style='для тех, кто ищет стойкий цитрусовый аромат с прозрачным, минеральным звучанием и не боится, что он «слетит» за час',
   top='грейпфрут, бергамот', heart='имбирь', base='мускус',
   sound='Искрящийся грейпфрут с лёгкой горчинкой бергамота, затем раскрывается пряный имбирь, придающий композиции тепло и пикантность. Звучание линейное, без резких переходов: свежий, чистый цитрус с минеральной текстурой, который держится неожиданно долго для этого направления.',
   mkt='Цитрусовый унисекс-аромат с грейпфрутом, бергамотом и пряным имбирём, который дарит ощущение чистой, прозрачной свежести без сладости. Технически выдающийся: стойкий и шлейфовый, он сохраняет натуральное звучание цитрусовой кожуры на протяжении многих часов. Для тех, кто ценит простоту, элегантность и хочет свежий аромат, который не исчезнет к обеду.',
   img=[21, 22, 20], col='mauve'),
 'ЖЕНСКИЕ|J6': dict(dir='сладкое · мускусное · пудровое', brand='Juliette Has A Gun', sex='женский', season='весна, лето, прохладная осень',
   occ='повседневный, выходной, свидание, расслабленное настроение', style='для тех, кто любит сахарную пудру, малиновую нежность и интимный мускусный шлейф',
   top='сахарная вата, малина', heart='маршмеллоу, цветок апельсина', base='миндаль, мускус, амброксан, бобы тонка',
   sound='Нежная малиновая сахарная вата с лёгкой припудренностью, почти невесомая и кокетливая. Через 20–30 минут раскрывается кремовая середина с маршмеллоу и цветком апельсина, а база уходит в мягкий мускус с амброксаном и миндально-пудровыми бобами тонка. Звучит тихо и интимно.',
   mkt='Облако розовой сахарной ваты и маршмеллоу, припудренное нежнейшей малиной и сливочным мускусом. Кокетливый, сладкий, но не приторный аромат для тех, кто любит пудровые гурманские композиции с интимным шлейфом. Идеален для повседневной нежности и весеннего настроения.',
   img=[26, 27, 25], col='pink')}
NEW = ['ЖЕНСКИЕ|C3', 'ЖЕНСКИЕ|J6', 'МУЖСКИЕ|J7', 'УНИСЕКС|H2', 'УНИСЕКС|L22', 'ПРЕМИУМ|K9']
COL = {'Свежий': ['green', 'yellow', 'mauve'], 'Сладкий': ['pink', 'brown', 'mauve'], 'Свежий/Сладкий': ['yellow', 'pink', 'green']}

os.makedirs(f'{SITE}/img/notes', exist_ok=True); os.makedirs(f'{SITE}/img/bottles', exist_ok=True)
def harmonize(im):
    import numpy as np
    a = np.asarray(im, np.float32) / 255; L = (a @ [.2126, .7152, .0722]); m = float(L.mean())
    g = min(1.45, max(.75, np.log(.30) / np.log(max(m, .02))))           # one common depth: mean lightness ~ .30
    a = a ** g; L = a @ [.2126, .7152, .0722]
    sat = float((a.max(-1) - a.min(-1)).mean()); k = min(1.0, .42 / max(sat, 1e-3))   # no candy-bright tiles
    a = L[..., None] + (a - L[..., None]) * k
    a = a * [1.03, 1.0, .95]                                            # one warm tone over the whole set
    h, w = L.shape; yy, xx = np.mgrid[0:h, 0:w]; r = ((xx / w - .5) ** 2 + (yy / h - .5) ** 2) ** .5
    a = a * (1 - .28 * np.clip(r - .25, 0, 1)[..., None])              # soft vignette
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype('uint8'))
GRADE = os.environ.get('NOTE_GRADE', '0') == '1'
def put_note(src, name, zoom=1.0, grade=None):
    grade = GRADE if grade is None else grade
    out = f'{SITE}/img/notes/{name}.webp'
    if not os.path.exists(out):
        im = Image.open(src).convert('RGB'); W, H = 300, 480; k = max(W / im.width, H / im.height) * zoom
        im = im.resize((math.ceil(im.width * k), math.ceil(im.height * k)), Image.LANCZOS)
        x, y = (im.width - W) // 2, (im.height - H) // 2; im = im.crop((x, y, x + W, y + H))
        if grade: im = harmonize(im)
        im.save(out, 'WEBP', quality=76, method=6)
    return f'img/notes/{name}.webp'
cut = {(c['sec'], c['code']): c['file'] for c in json.load(open(f'{CUT}/list.json'))}
rot = {}
cards = {}
for i, d in enumerate(base):
    k = d['category'] + '|' + d['number']; tip = tips.get(k, {}); p = tiers(d)
    if k in PDF:
        x = PDF[k]; c = dict(dir=x['dir'], brand=x['brand'], sex=x['sex'], season=x['season'], occ=x['occ'], style=x['style'],
                             pyr=[['top', x['top']], ['heart', x['heart']], ['base', x['base']]], sound=x['sound'], mkt=x['mkt'], col=x['col'], ok=True,
                             ph=[put_note(f'{PINS}/{f}', os.path.splitext(os.path.basename(f))[0], grade=False) for f in CP[k]['files']] if k in CP else [put_note(f'{PDFI}/im-{j:03d}.png', f'pdf{j:03d}', grade=False) for j in x['img']])
    else:
        ph = []
        if k in CP:
            ph = [put_note(f'{PINS}/{f}', os.path.splitext(f)[0].replace('/', '_'), ZOOM) for f in CP[k]['files']]
        for th, note in ([] if k in CP else picks.get(k, [])):
            files = choices.get(th) or []
            if not files: continue
            n = rot.get(th, 0); rot[th] = n + 1; f = files[n % len(files)]
            ph.append(put_note(f'{PINS}/{f}', os.path.splitext(f)[0].replace('/', '_'), ZOOM))
        sx = SEX.get(d['category']) or SEX_P.get(d['number'], 'унисекс'); bd = brand(nm(d))
        c = dict(dir=TX.direction(d), brand=TX.FIX_BRAND.get(bd, bd), sex=sx, season=TX.season(d), occ=TX.occasion(d),
                 style=TX.style(d), pyr=d.get('pyr') or [], sound=TX.sound(d), mkt=TX.marketing(d, sx), col=TX.colour(d), ok=False, ph=ph)
    c.update(TX.OVERRIDE.get(k, {}))
    f = cut.get((d['category'][:3], d['number']))
    if f:
        shutil.copy(f'{CUT}/{f}', f'{SITE}/img/bottles/{f}'); c['bt'] = f'img/bottles/{f}'
    c['notes'] = CP[k]['notes'] if (k in CP and k not in PDF) else [n for th, n in picks.get(k, [])]
    if k in NEW: c['new'] = True
    cards[k] = c
open(f'{SITE}/cards.js', 'w', encoding='utf-8').write(
    '/* Карточки ароматов в стиле «Новинки»: фото нот, направление, кому подойдёт, как звучит, маркетинговое описание.\n'
    '   ok:true — текст из документа владельца, ok:false — черновик по нотам. Собирается scripts/site_cards_v148.py. */\n'
    'window.CARDS=' + json.dumps(cards, ensure_ascii=False, separators=(',', ':')) + ';\n')
print(len(cards), 'cards;', sum(len(c['ph']) == 3 for c in cards.values()), 'with 3 photos;', len(os.listdir(f'{SITE}/img/notes')), 'note photos')
