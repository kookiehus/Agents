import json, os, re, sys, io
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab import rl_config
import pypdf
rl_config.useA85 = 0
D, FONTS, SRC, OUT = sys.argv[1:5]
W, H = 841.89, 1190.55
for f in ('Montserrat-Regular','Montserrat-Medium','Montserrat-SemiBold','CormorantGaramond-Medium','CormorantGaramond-MediumItalic'):
    pdfmetrics.registerFont(TTFont(f, f'{FONTS}/{f}.ttf'))
sw = pdfmetrics.stringWidth
R, M, SB, CG = 'Montserrat-Regular','Montserrat-Medium','Montserrat-SemiBold','CormorantGaramond-Medium'

SEC = {  # accent, title
 'ЖЕНСКИЕ АРОМАТЫ': dict(acc=(0.45,0.27,0.31), title='Женские ароматы'),
 'МУЖСКИЕ АРОМАТЫ': dict(acc=(0.20,0.26,0.34), title='Мужские ароматы'),
 'УНИСЕКС':         dict(acc=(0.40,0.37,0.24), title='Унисекс'),
 'ПРЕМИУМ':         dict(acc=(0.30,0.23,0.23), title='Премиум'),
}
GROUP = {}
for col, names in {
 (0.66,0.36,0.47): 'Цветочные',
 (0.72,0.47,0.20): 'Фруктовые Цитрусовые',
 (0.22,0.50,0.52): 'Водные Акватические Ароматные Спокойные',
 (0.45,0.34,0.60): 'Восточные Пряные',
 (0.36,0.44,0.30): 'Древесные Шипровые Фужерные Табачные Кожаные Терпкие',
 (0.58,0.42,0.24): 'Гурманские Ванильные',
 (0.44,0.45,0.58): 'Мускусные Пудровые'}.items():
    for n in names.split(): GROUP[n] = col
DROP = {'Сладкие','Сладковатые','Свежие'}   # now expressed by the fresh-sweet scale
SCALE = {'Свежий': 0.10, 'Свежий/сладкий': 0.5, 'Сладкий': 0.90}
mix = lambda a, b, t: tuple(a[i]*(1-t)+b[i]*t for i in range(3))

def parse(card):
    t = card['texts']
    name = ' '.join(x['t'].strip() for x in sorted([x for x in t if x['f']==SB and x['c'][0]<0.5], key=lambda x: x['y']))
    ru = ' '.join(x['t'].strip() for x in sorted([x for x in t if x['f']==R and x['x']<150], key=lambda x: x['y']))
    typ = ' '.join(x['t'].strip() for x in t if x['f']==M and abs(x['s']-9)<.3)
    tiers = []; cur = None
    for x in sorted([x for x in t if x['f']==R and x['x']>150], key=lambda x: x['y']):
        if x['c'][0] > 0.4: cur = [x['t'].strip(), []]; tiers.append(cur)
        elif cur: cur[1].append(x['t'].strip())
    b = card['bottle']; os.makedirs(f"{D}/small", exist_ok=True); sm = f"{D}/small/{os.path.basename(b['file'])}"
    if not os.path.exists(sm):
        im = Image.open(f"{D}/{b['file']}"); th = int(b['h']/72*300)
        if im.height > th: im = im.resize((max(1, round(im.width*th/im.height)), th), Image.LANCZOS)
        im.save(sm)
    return dict(code=card['code'], name=name, ru=ru, type=typ, tags=card['tags'], notes=[(h, ' '.join(l)) for h, l in tiers],
                img=(f"{D}/small/{os.path.basename(b['file'])}", b['x'], b['y'], b['w'], b['h']))

BASE = 0.756
def styled_bottle(src, refl=0.46, tint=1.0, shade=0.62, tag=""):
    """Cut-out bottle -> bottle + soft contact shadow + fading reflection (same structure as the existing images)."""
    from PIL import ImageChops, ImageFilter
    out = src.replace('.png', f'_styled2{tag}.png')
    if os.path.exists(out): return out
    im = Image.open(src).convert('RGBA'); im = im.crop(im.getchannel('A').point(lambda v: 255 if v > 150 else 0).getbbox())
    k = 660 / im.height; im = im.resize((round(im.width*k), 660), Image.LANCZOS)
    bw, bh = im.size; th = round(bh / BASE); pad = round(bw*0.04)
    cv = Image.new('RGBA', (bw + 2*pad, th), (0, 0, 0, 0))
    rf = im.transpose(Image.FLIP_TOP_BOTTOM); end = round(th*0.94) - bh
    if tint != 1.0:   # darken the mirror image so pale bottles still read on a light page
        r_, g_, b_, a_ = rf.split(); rf = Image.merge('RGBA', (r_.point(lambda v: int(v*tint)), g_.point(lambda v: int(v*tint)), b_.point(lambda v: int(v*tint)), a_))
    ramp = Image.new('L', (1, bh)); ramp.putdata([int(255*refl*max(0.0, 1 - y/end)**1.35) for y in range(bh)])
    rf.putalpha(ImageChops.multiply(rf.getchannel('A'), ramp.resize((bw, bh))))
    cv.alpha_composite(rf.crop((0, 0, bw, th-bh)), (pad, bh))
    foot = im.getchannel('A').crop((0, bh - round(bh*0.05), bw, bh)).resize((bw, 1), Image.BOX).point(lambda v: 255 if v > 20 else 0)
    sh = Image.new('L', cv.size, 0); band = round(th*0.016)
    sh.paste(foot.resize((bw, 2*band)), (pad, bh - band))
    sh = sh.filter(ImageFilter.GaussianBlur(th*0.013)).point(lambda v: int(v*shade))
    shadow = Image.new('RGBA', cv.size, (12, 10, 10, 0)); shadow.putalpha(sh)
    cv.alpha_composite(shadow); cv.alpha_composite(im, (pad, 0)); cv.save(out)
    return out
def styled(src):
    path = styled_bottle(src)
    im = Image.open(path); s = min(112/im.width, 158/im.height); w, h = im.width*s, im.height*s
    return (path, 76-w/2, 233.45+h*(1-BASE)-h, w, h)
def N(code, sec, p, name, ru, typ, tags, top, mid, base):
    return dict(code=code, section=sec, name=name, ru=ru, type=typ, tags=tags, img=styled(f'{D}/new/p{p}_bottle.png'),
                notes=[('ВЕРХНИЕ НОТЫ', top), ('НОТЫ СЕРДЦА', mid), ('БАЗОВЫЕ НОТЫ', base)])
NEW = [
 N('K9','ПРЕМИУМ',1,'BY KILIAN APPLE BRANDY ON THE ROCKS','Килиан Эппл Бренди он зе Рокс','Свежий/сладкий',['Фруктовые','Древесные','Пряные'],'бергамот, ананас, кардамон','яблоко, ром, бренди, ананас, ваниль, мох','кедр, амброксан'),
 N('H2','УНИСЕКС',2,'HORMONE PARIS GABA','Гормон Пари Габа','Свежий',['Цитрусовые','Цветочные','Мускусные'],'итальянский мандарин, апельсин, лаванда','османтус, жасмин самбак','амброксан, акигалавуд, мускус'),
 N('C3','ЖЕНСКИЕ АРОМАТЫ',3,'CAROLINA HERRERA LA BOMBA','Каролина Эррера Ла Бомба','Сладкий',['Цветочные','Фруктовые','Восточные'],'питахайя (драконий фрукт)','пион, красный франжипани','ваниль, пачули'),
 N('J7','МУЖСКИЕ АРОМАТЫ',4,'JEAN PAUL GAULTIER LE MALE ELIXIR','Жан Поль Готье Ле Маль Эликсир','Сладкий',['Восточные','Фужерные','Сладкие'],'лаванда, мята','ваниль, бензоин','мёд, бобы тонка, табак'),
 N('L22','УНИСЕКС',5,'LOUIS VUITTON SYMPHONY','Луи Виттон Симфони','Свежий',['Цитрусовые','Пряные','Фужерные','Свежие'],'грейпфрут, бергамот','имбирь','мускус'),
 N('J6','ЖЕНСКИЕ АРОМАТЫ',6,'JULIETTE HAS A GUN POWDER LOVE','Джульетт Хэз Э Ган Паудер Лав','Сладкий',['Сладкие','Мускусные','Пудровые'],'сахарная вата, малина','маршмеллоу, цветок апельсина','миндаль, мускус, амброксан, бобы тонка'),
]
OVERRIDE = {('E25', 'ЖЕНСКИЕ АРОМАТЫ'): f'{D}/override/E25.png', ('Z1', 'ЖЕНСКИЕ АРОМАТЫ'): f'{D}/override/Z1.png', ('V20', 'МУЖСКИЕ АРОМАТЫ'): f'{D}/override/V20.png'}   # replaced bottle pictures
FEATURE = {('V20', 'МУЖСКИЕ АРОМАТЫ'), ('Z1', 'ЖЕНСКИЕ АРОМАТЫ')}                              # shown on its own feature page instead of a grid card
def codekey(c): m = re.match(r'([A-Z]+)(\d+)', c); return (m.group(1), int(m.group(2)))
raw = [c for c in json.load(open(f'{D}/cards.json')) if c['code'] != 'Z2']
def section(sec):
    it = []
    for c in raw:
        if c['section'] != sec or (c['code'], sec) in FEATURE: continue
        p = parse(c)
        if (c['code'], sec) in OVERRIDE: p['img'] = styled(OVERRIDE[(c['code'], sec)])
        it.append(p)
    it += [n for n in NEW if n['section'] == sec]
    return sorted(it, key=lambda x: codekey(x['code']))

def wrap_words(text, font, size, width):
    lines = []; cur = ''
    for w in text.split(' '):
        t = (cur+' '+w).strip()
        if sw(t, font, size) <= width or not cur: cur = t
        else: lines.append(cur); cur = w
    return lines + ([cur] if cur else [])
def wrap_notes(text, size, width):
    """Break only after a comma; a single over-long note falls back to word wrapping."""
    notes = [n.strip() for n in text.split(',') if n.strip()]; lines = []; cur = ''
    for i, n in enumerate(notes):
        tok = n + (',' if i < len(notes)-1 else '')
        t = (cur+' '+tok).strip()
        if sw(t, R, size) <= width: cur = t
        else:
            if cur: lines.append(cur)
            if sw(tok, R, size) <= width: cur = tok
            else:
                ws = wrap_words(tok, R, size, width); lines += ws[:-1]; cur = ws[-1]
    return lines + ([cur] if cur else [])
def balance(name, size, width):
    ws = name.split(' '); best = None
    for i in range(1, len(ws)):
        a, b = ' '.join(ws[:i]), ' '.join(ws[i:])
        wa, wb = sw(a, SB, size), sw(b, SB, size)
        if wa <= width and wb <= width and (best is None or abs(wa-wb) < best[0]): best = (abs(wa-wb), [a, b])
    return best[1] if best else wrap_words(name, SB, size, width)

def rr(c, x0, top, x1, bottom, fill=None, stroke=None, r=None, lw=0.5):
    r = (bottom-top)/2 if r is None else r
    if fill: c.setFillColorRGB(*fill)
    if stroke: c.setStrokeColorRGB(*stroke); c.setLineWidth(lw)
    c.roundRect(x0, H-bottom, x1-x0, bottom-top, r, stroke=1 if stroke else 0, fill=1 if fill else 0)

def card(c, it, gx, gt, sec):
    dark = False; acc = SEC[sec]['acc']
    c.drawImage(f'{D}/Glass1.png', gx, H-gt-284, 280.63, 284, mask='auto')
    if dark: rr(c, gx+15.5, gt+14.5, gx+265.5, gt+269.5, fill=(0.125,0.105,0.095), stroke=(0.78,0.63,0.38), r=13, lw=0.6)
    INK = (0.96,0.93,0.87) if dark else (0.17,0.13,0.14)
    SUB = (0.70,0.66,0.60) if dark else (0.40,0.36,0.37)
    def T(x, y, s, f, sz, col, cs=0):
        t = c.beginText(gx+x, H-(gt+y)); t.setFont(f, sz); t.setFillColorRGB(*col); t.setCharSpace(cs); t.textOut(s); t.setCharSpace(0); c.drawText(t)
    # --- fixed header zone -------------------------------------------------
    rr(c, gx+26, gt+23.8, gx+62, gt+42.2, fill=acc)
    T(44-sw(it['code'], SB, 11)/2, 36.8, it['code'], SB, 11, (0.13,0.10,0.09) if dark else (1,1,1))
    NW = 184
    for sz in (11, 10.5, 10, 9.5):
        if sw(it['name'], SB, sz) <= NW: lines, size = [it['name']], sz; break
    else: lines, size = balance(it['name'], 10, NW), 10
    y = 36.6
    for ln in lines[:2]: T(76, y, ln, SB, size, INK); y += 12
    ru = it['ru']; rs = 8
    while sw(ru, R, rs) > NW and rs > 6.5: rs -= 0.25
    T(76, y, ru, R, rs, SUB); y += 11.5
    # fresh <-> sweet scale
    lab = 6.3; x0 = 76 + sw('свежий', M, lab) + 5; bw = 62
    T(76, y+0.2, 'свежий', M, lab, (0.20,0.50,0.52) if not dark else (0.45,0.75,0.76))
    for i in range(31):
        c.setFillColorRGB(*mix((0.25,0.60,0.62), (0.74,0.30,0.42), i/30)); c.rect(gx+x0+i*bw/31, H-(gt+y-0.4), bw/31+0.3, 2.6, stroke=0, fill=1)
    px = x0 + bw*SCALE.get(it['type'], 0.5)
    c.setFillColorRGB(*((0.125,0.105,0.095) if dark else (1,1,1))); c.circle(gx+px, H-(gt+y-1.7), 4.1, stroke=0, fill=1)
    c.setFillColorRGB(*mix((0.25,0.60,0.62), (0.74,0.30,0.42), SCALE.get(it['type'], 0.5))); c.circle(gx+px, H-(gt+y-1.7), 2.9, stroke=0, fill=1)
    T(x0+bw+5, y+0.2, 'сладкий', M, lab, (0.74,0.30,0.42) if not dark else (0.90,0.55,0.63))
    y += 6.5
    # chips: muted, grouped palette, max 2 rows
    tags = [t for t in it['tags'] if t not in DROP]; x = 76; row = 0; shown = 0
    for i, tag in enumerate(tags):
        w = sw(tag, M, 6.6) + 12
        if x + w > 262:
            if row == 1: T(x+2, y+8.3, f'+{len(tags)-i}', M, 6.6, SUB); break
            x = 76; y += 13.6; row = 1
        col = GROUP.get(tag, (0.5,0.45,0.45))
        if dark: rr(c, gx+x, gt+y, gx+x+w, gt+y+11.4, stroke=mix(col, (1,1,1), 0.35), lw=0.5); tc = mix(col, (1,1,1), 0.55)
        else: rr(c, gx+x, gt+y, gx+x+w, gt+y+11.4, fill=mix(col, (1,1,1), 0.82)); tc = mix(col, (0,0,0), 0.25)
        T(x+6, y+8.0, tag, M, 6.6, tc); x += w + 3
    # hairline between header and body zones
    c.setStrokeColorRGB(*(mix(acc, (0,0,0), 0.45) if dark else (0.84,0.81,0.81))); c.setLineWidth(0.4); c.line(gx+28, H-(gt+108.5), gx+253, H-(gt+108.5))
    # --- body: bottle + honest pyramid --------------------------------------
    p, bx, by, bw_, bh = it['img']
    c.drawImage(p, gx+bx, H-(gt+by+bh), bw_, bh, mask='auto')
    TOP, BOT, TX, TW = 116.0, 262.0, 168.0, 91.0
    fs = 8.0
    while True:
        blocks = [(h, wrap_notes(t, fs, TW)) for h, t in it['notes']]; lh = fs*1.2
        need = sum(9.5 + len(b)*lh for _, b in blocks) + 5*(len(blocks)-1)
        if need <= BOT-TOP or fs <= 6.6: break
        fs -= 0.2
    gap = (BOT-TOP - sum(9.5 + len(b)*lh for _, b in blocks)) / max(1, len(blocks)-1) if len(blocks) > 1 else 0
    gap = min(gap, 26); total = sum(9.5 + len(b)*lh for _, b in blocks) + gap*(len(blocks)-1)
    tops = []; yy = TOP
    for h, b in blocks: tops.append(yy); yy += 9.5 + len(b)*lh + gap
    end = BOT if len(blocks) > 1 else BOT
    bounds = [TOP] + [tops[i] - gap/2 for i in range(1, len(blocks))] + [BOT]
    base = acc if not dark else (0.78,0.63,0.38)
    shades = [mix(base, (1,1,1), 0.62), mix(base, (1,1,1), 0.30), base] if len(blocks) == 3 else ([mix(base, (1,1,1), 0.30)] if len(blocks) == 1 else [mix(base, (1,1,1), 0.5), base])
    if dark: shades = [mix(s, (0.125,0.105,0.095), 0.0) for s in shades]
    CX = 151.0; half = lambda yv: 0.6 + 11.0*(yv-TOP)/(BOT-TOP)
    for i in range(len(blocks)):
        a, b_ = bounds[i] + (0.9 if i else 0), bounds[i+1]
        c.setFillColorRGB(*shades[min(i, len(shades)-1)]); pth = c.beginPath()
        pth.moveTo(gx+CX-half(a), H-(gt+a)); pth.lineTo(gx+CX+half(a), H-(gt+a)); pth.lineTo(gx+CX+half(b_), H-(gt+b_)); pth.lineTo(gx+CX-half(b_), H-(gt+b_)); pth.close()
        c.drawPath(pth, stroke=0, fill=1)
    for i, (h, b) in enumerate(blocks):
        yy = tops[i] + 6.2
        hc = mix(shades[min(i, len(shades)-1)], (0,0,0), 0.35) if not dark else mix(shades[min(i, len(shades)-1)], (1,1,1), 0.15)
        T(TX, yy, h, M, 6.6, hc, cs=0.7); yy += 3.3
        for ln in b: yy += lh; T(TX, yy, ln, R, fs, INK)

def chrome(c, sec, codes, pno, total, title=None):
    acc = SEC[sec]['acc'] if sec else (0.30,0.23,0.23)
    c.setFillColorRGB(0.965,0.957,0.961); c.rect(0,0,W,H,stroke=0,fill=1)
    c.drawImage(f'{D}/BgHead.png', 0, H-80, W, 80)
    c.drawImage(f'{D}/logo.png', 42, H-60, 38, 40, mask='auto')
    t = c.beginText(96, 1143.5); t.setFont(CG, 24); t.setFillColorRGB(0.97,0.93,0.85); t.setCharSpace(2.0); t.textOut('ETIB PARFUM'); t.setCharSpace(0); c.drawText(t)
    title = title or SEC[sec]['title']; c.setFillColorRGB(0.23,0.165,0.135); c.setFont(CG, 25)
    c.drawRightString(798, 1147, title); tw = sw(title, CG, 25)
    rng = (f'{codes[0]} — {codes[-1]}' if len(codes) > 1 else codes[0]) if codes else ''
    t = c.beginText(798 - sw(rng, M, 8) - 1.2*(len(rng)-1), 1132.5); t.setFont(M, 8); t.setFillColorRGB(0.36,0.27,0.23); t.setCharSpace(1.2); t.textOut(rng); t.setCharSpace(0); c.drawText(t)
    c.setStrokeColorRGB(0.7,0.5,0.3); c.setLineWidth(0.6); c.line(330, H-39.8, 798-tw-18, H-39.8)
    # section tab on the outer edge
    idx = list(SEC).index(sec) if sec else -9; c.setFillColorRGB(*acc); c.roundRect(W-8, H-(150+idx*90)-60, 14, 60, 4, stroke=0, fill=1)
    # footer: clean line, disclaimer, page number
    c.setStrokeColorRGB(0.80,0.74,0.70); c.setLineWidth(0.5); c.line(42, 34, W-42, 34)
    s = 'ВСЕ ФЛАКОНЫ АРОМАТОВ ИЗГОТОВЛЕНЫ В ФИРМЕННОМ СТИЛЕ ETIB PARFUM'
    t = c.beginText((W - sw(s, R, 7) - 1.6*(len(s)-1))/2, 18); t.setFont(R, 7); t.setFillColorRGB(0.36,0.29,0.27); t.setCharSpace(1.6); t.textOut(s); t.setCharSpace(0); c.drawText(t)
    c.setFont(M, 8); c.setFillColorRGB(*acc); c.drawString(42, 18, title.upper())

XS = [16.0, 280.5, 545.0]; YS = [78.0, 344.0, 610.0, 876.0]
def grid_page(c, sec, items, pno, total, tail=False, inline=None, deco=False):
    chrome(c, sec, [i['code'] for i in items] + ([inline[0]['code']] if inline else []), pno, total)
    below = YS[(len(items)-1)//3] + 284 if items else 80
    if deco and len(items) % 3 == 1:   # a lone last card: a flower laid across the page, its stem passing under the glass card, plus a leaf
        from PIL import ImageFilter, ImageDraw
        import numpy as np
        px = 3.0; top = YS[(len(items)-1)//3]; band_top, band_bot, x_left = top + 21.0, 1150.0, 30.0
        im = Image.open(f'{D}/notes/anthurium.png').convert('RGBA'); al = np.array(im.getchannel('A')) > 128
        first = np.where(al.any(axis=0), al.argmax(axis=0), 10**6); xs = int(first.argmin())          # column of the stem's highest point
        s_ = (band_bot - band_top) / im.height
        col = al[:, xs]; t_px = int(col.sum()); y_mid = float(np.where(col)[0].mean())
        rgb = np.array(im.convert('RGB'))[:, xs][col]; stem_col = tuple(int(v) for v in np.median(rgb, axis=0))
        head = im.crop((0, 0, xs, im.height)).resize((round(xs*s_*px), round(im.height*s_*px)), Image.LANCZOS)
        cw_, ch_ = round((W + 4 - x_left)*px), head.height; fl = Image.new('RGBA', (cw_, ch_), (0, 0, 0, 0)); fl.paste(head, (0, 0))
        # the photo's stem ends at the frame, so the rest is drawn: a thin tapering curve to the right page edge
        x0, y0 = head.width - 2.0, y_mid*s_*px; x3, y3 = float(cw_), ch_*0.40; w0 = t_px*s_*px
        P = [(x0, y0), (x0 + (x3-x0)*0.30, y0 - ch_*0.01), (x0 + (x3-x0)*0.62, y3 - ch_*0.30), (x3, y3)]
        bez = lambda t: tuple(sum(c_*p_[k] for c_, p_ in zip(((1-t)**3, 3*t*(1-t)**2, 3*t*t*(1-t), t**3), P)) for k in (0, 1))
        up, dn = [], []
        for i in range(121):
            t = i/120; (xa, ya), (xb, yb) = bez(max(0, t-0.004)), bez(min(1, t+0.004)); dx, dy = xb-xa, yb-ya; n = (dx*dx+dy*dy)**0.5 or 1
            hw = w0*(1 - 0.62*t)/2; xm, ym = bez(t); up.append(((xm - dy/n*hw)*2, (ym + dx/n*hw)*2)); dn.append(((xm + dy/n*hw)*2, (ym - dx/n*hw)*2))
        mk = Image.new('L', (cw_*2, ch_*2), 0); ImageDraw.Draw(mk).polygon(up + dn[::-1], fill=255)
        mk = mk.resize((cw_, ch_), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.7))
        stem = Image.new('RGBA', (cw_, ch_), stem_col + (0,)); stem.putalpha(mk); base = Image.new('RGBA', (cw_, ch_), (0, 0, 0, 0)); base.alpha_composite(stem); base.alpha_composite(fl)
        def with_shadow(img, out, pad=60):
            cv = Image.new('RGBA', (img.width + 2*pad, img.height + 2*pad), (0, 0, 0, 0))
            sh = Image.new('L', cv.size, 0); sh.paste(img.getchannel('A'), (pad + 10, pad + 24)); sh = sh.filter(ImageFilter.GaussianBlur(16)).point(lambda v: int(v*0.20))
            shadow = Image.new('RGBA', cv.size, (60, 55, 40, 0)); shadow.putalpha(sh); cv.alpha_composite(shadow); cv.alpha_composite(img, (pad, pad)); cv.save(out); return cv, pad
        cv, pad = with_shadow(base, f'{D}/notes/anthurium_deco.png')
        c.drawImage(f'{D}/notes/anthurium_deco.png', x_left - pad/px, H - band_bot - pad/px, cv.width/px, cv.height/px, mask='auto')
        lf = Image.open(f'{D}/notes/callaleaf.png').convert('RGBA').transpose(Image.FLIP_LEFT_RIGHT)      # leaf: stalk from the right edge
        lw_ = 236.0; lf = lf.resize((round(lw_*px), round(lw_*px*lf.height/lf.width)), Image.LANCZOS); cv, pad = with_shadow(lf, f'{D}/notes/callaleaf_deco.png')
        c.drawImage(f'{D}/notes/callaleaf_deco.png', W + 2 - lw_ - pad/px, H - 1152 - pad/px, cv.width/px, cv.height/px, mask='auto')
        i_ = len(items) - 1; gx_ = XS[i_ % 3] + 264.5; gt_ = YS[i_//3]            # frosted backing: the stem stays visible through the glass, softly
        c.setFillAlpha(0.62); rr(c, gx_ + 15.5, gt_ + 14.5, gx_ + 265.5, gt_ + 269.5, fill=(0.955,0.947,0.951), r=13); c.setFillAlpha(1)
    for i, it in enumerate(items):
        rowlen = min(3, len(items) - (i//3)*3); off = (3-rowlen)*264.5/2 if (tail or deco) else 0   # centre an incomplete row above the tail photo / between the twigs
        card(c, it, XS[i%3]+off, YS[i//3], sec)
    if inline: feature_block(c, inline[0], inline[1], below + 8, H - 44)
    if tail:
        top = below + 10
        fn = f'{D}/store_feather.png'; im = Image.open(fn); avail = (H-34-70) - top; h = avail; w = h*im.width/im.height
        if w > W-60: w = W-60; h = w*im.height/im.width
        c.drawImage(fn, (W-w)/2, H-top-h, w, h, mask='auto')
        c.setFillColorRGB(0.42,0.33,0.30); c.setFont(CG, 22); c.drawCentredString(W/2, 58, 'Твой аромат — твоё настроение')
    c.showPage()

def opener(path, sec, n, codes):
    c = canvas.Canvas(path, pagesize=(W, H))
    cream = (0.97,0.93,0.85); gold = (0.80,0.62,0.38)
    s = 'ETIB PARFUM  ·  КОЛЛЕКЦИЯ'
    t = c.beginText((W - sw(s, M, 11) - 4*(len(s)-1))/2, H-470); t.setFont(M, 11); t.setFillColorRGB(*cream); t.setCharSpace(4); t.textOut(s); t.setCharSpace(0); c.drawText(t)
    c.setFillColorRGB(*cream); c.setFont(CG, 96); c.drawCentredString(W/2, H-580, SEC[sec]['title'].split()[0])
    if len(SEC[sec]['title'].split()) > 1: c.drawCentredString(W/2, H-670, SEC[sec]['title'].split()[1])
    yl = H-720; c.setStrokeColorRGB(*gold); c.setLineWidth(0.8); c.line(W/2-150, yl, W/2+150, yl)
    c.setFillColorRGB(*gold); p = c.beginPath(); p.moveTo(W/2-5, yl); p.lineTo(W/2, yl+5); p.lineTo(W/2+5, yl); p.lineTo(W/2, yl-5); p.close(); c.drawPath(p, stroke=0, fill=1)
    s = f'{n} АРОМАТОВ   ·   {codes[0]} — {codes[-1]}'
    t = c.beginText((W - sw(s, M, 12) - 3*(len(s)-1))/2, yl-34); t.setFont(M, 12); t.setFillColorRGB(*cream); t.setCharSpace(3); t.textOut(s); t.setCharSpace(0); c.drawText(t)
    c.showPage(); c.save()

def para(c, x, y, text, font, size, width, lead, col, bold_prefix=None, draw=True):
    """Left-aligned paragraph; optional bold lead-in ('Сезон:'). Returns y after the last line."""
    words = text.split(' '); line = []; first = True
    def flush(ws, yy):
        if not draw: return
        xx = x
        if first and bold_prefix:
            c.setFont(SB, size); c.setFillColorRGB(*col); c.drawString(xx, H-yy, bold_prefix); xx += sw(bold_prefix + ' ', SB, size)
        c.setFont(font, size); c.setFillColorRGB(*col); c.drawString(xx, H-yy, ' '.join(ws))
    for wd in words:
        pre = sw(bold_prefix + ' ', SB, size) if (first and bold_prefix) else 0
        if pre + sw(' '.join(line + [wd]), font, size) > width and line:
            flush(line, y); y += lead; line = [wd]; first = False
        else: line.append(wd)
    if line: flush(line, y); y += lead
    return y

def cover_img(path, w, h, scale=3):
    im = Image.open(path).convert('RGB'); tw, th = int(w*scale), int(h*scale)
    r = max(tw/im.width, th/im.height); im = im.resize((max(tw, round(im.width*r)), max(th, round(im.height*r))), Image.LANCZOS)
    x, y = (im.width-tw)//2, (im.height-th)//2; out = path.rsplit('.', 1)[0] + f'_{tw}x{th}.jpg'
    im.crop((x, y, x+tw, y+th)).save(out, quality=88); return out

def feature_block(c, card, f, top, bot):
    """Single-fragrance block in the style of the new-arrivals sheets: photo collage, big code, notes, description panel.
    Fills the page width between y=top and y=bot (top-down coordinates); sizes scale with the available height."""
    k = (bot-top)/1060.0; INK = (0.13,0.10,0.10); ch = 440.0*k; cw = W/3
    for i, ph in enumerate(f['photos']):
        c.drawImage(cover_img(ph, cw, ch, 2), i*cw, H-top-ch, cw+0.5, ch)
    gfn = f'{D}/topfade.png'   # soft darkening behind the title
    g = Image.new('RGBA', (1, 256)); g.putdata([(0, 0, 0, int(255*0.50*(1-i/255)**1.5)) for i in range(256)]); g.save(gfn)
    c.drawImage(gfn, 0, H-top-250*k, W, 250*k, mask='auto')
    y = top + 92*k
    for ln in f['title']:
        t = c.beginText(44, H-y); t.setFont(SB, 58*k); t.setFillColorRGB(1,1,1); t.setCharSpace(-2.6*k); t.textOut(ln); t.setCharSpace(0); c.drawText(t); y += 56*k
    b = card['bottle']; bh = 400.0*k; ov = OVERRIDE.get((card['code'], card['section']))
    if ov:
        big = styled_bottle(ov, **f.get('bottle_style', {})); iw, ih = Image.open(big).size; bw = bh*iw/ih
    else:
        bw = bh*b['w']/b['h']; big = f"{D}/feature_{card['code']}.png"; Image.open(f"{D}/{b['file']}").resize((round(bw*3), round(bh*3)), Image.LANCZOS).save(big)
    c.drawImage(big, W/2-bw/2, H-(top+ch-175*k)-bh, bw, bh, mask='auto')
    fs, ld = max(11.5, 15*k), max(16.0, 21*k)
    y0 = top + ch + 92*k
    t = c.beginText(44, H-y0); t.setFont(SB, 92*k); t.setFillColorRGB(*INK); t.setCharSpace(-3*k); t.textOut(card['code']); t.setCharSpace(0); c.drawText(t)
    y = y0 + 40*k
    for kk, v in f['facts']: y = para(c, 44, y, v, R, fs, 285, ld, INK, bold_prefix=kk + ':')
    y = y0 - 30*k
    for kk, v in f['notes']: y = para(c, 560, y, v, R, fs, 250, ld, INK, bold_prefix=kk + ':') + 2
    pt = top + 712*k; hs = 20*k; bs, bl = max(10.5, 13.5*k), max(14.5, 19.5*k)
    for draw in (False, True):   # first pass measures the text so the panel hugs it
        if draw: c.setFillColorRGB(*f['panel']); c.roundRect(34, H-pb, W-68, pb-pt, 18, stroke=0, fill=1)
        if draw: c.setFillColorRGB(*INK); c.setFont(SB, hs); c.drawString(64, H-(pt+44*k), 'КОМУ ПОДОЙДЁТ'); c.drawString(400, H-(pt+44*k), 'КАК ЗВУЧИТ')
        y = pt + 74*k
        for kk, v in f['who']: y = para(c, 64, y, v, R, bs, 300, bl, INK, bold_prefix=kk + ':', draw=draw)
        y2 = para(c, 400, pt+74*k, f['sound'], R, bs, 390, bl, INK, draw=draw)
        y = max(y, y2) + 22*k
        if draw: c.setFont(SB, hs); c.setFillColorRGB(*INK); c.drawCentredString(W/2, H-y, 'МАРКЕТИНГОВОЕ ОПИСАНИЕ')
        ye = para(c, 80, y+30*k, f['promo'], R, bs, W-160, bl, INK, draw=draw)
        pb = min(bot - 6, ye + 14*k)

V20 = dict(
 inline=False, photos=[f'{D}/v20/lime.jpg', f'{D}/v20/cardamom.jpg', f'{D}/v20/amber.jpg'], title=['Versace Man', 'Eau Fraîche'], panel=(0.84,0.90,0.87),
 facts=[('Направление', 'древесное · акватическое · цитрусовое'), ('Производитель', 'Versace'), ('Пол', 'мужской'), ('Парфюмер', 'Оливье Кресп, 2006')],
 notes=[('Верхние', 'лимон, бергамот, карамбола, розовое дерево, кардамон'), ('Средние', 'эстрагон, шалфей, кедр, перец'), ('Базовые', 'амбра, мускус, шафран, платан')],
 who=[('Сезон', 'весна, лето, жаркая погода'), ('Случай', 'повседневный, офис, отдых, спорт, путешествия'),
      ('Стиль', 'для тех, кто любит чистую морскую свежесть без сладости и хочет лёгкий, ненавязчивый аромат на каждый день')],
 sound='Сочный старт с лимоном, бергамотом и кисло-сладкой карамболой, слегка подогретый кардамоном и розовым деревом. В сердце раскрываются зелёные травы — эстрагон и шалфей — с кедром и щепоткой перца. База тёплая и чистая: амбра, мускус и светлая древесина платана.',
 promo='Средиземноморское утро во флаконе: солёный бриз, цитрусы и прогретое солнцем дерево. Свежий древесно-акватический аромат для мужчин, которые ценят лёгкость и уверенность без лишних слов. Универсален — от офиса до отпуска, и особенно хорош в жару.',
)

Z1 = dict(
 inline=True, bottle_style=dict(refl=0.85, tint=0.80, shade=0.75, tag='_pale'), photos=[f'{D}/z1/chestnut.jpg', f'{D}/z1/flower.jpg', f'{D}/z1/cream.jpg'], title=['Zadig & Voltaire', 'This is Her!'], panel=(0.93,0.89,0.84),
 facts=[('Направление', 'цветочное · древесное · гурманское'), ('Производитель', 'Zadig & Voltaire'), ('Пол', 'женский'), ('Год выпуска', '2016')],
 notes=[('Верхние', 'розовый перец'), ('Средние', 'цветок шёлкового дерева, жасмин самбак'), ('Базовые', 'взбитые сливки, ваниль, каштан, сандал, кашемировое дерево')],
 who=[('Сезон', 'осень, зима, прохладные вечера'), ('Случай', 'повседневный, свидание, вечерний выход'),
      ('Стиль', 'для тех, кто любит тёплые сливочно-древесные ароматы с характером — нежные, но не приторные')],
 sound='Короткая искра розового перца быстро уступает место белым цветам — жасмину самбак и цветку шёлкового дерева. Затем аромат становится сливочным и тёплым: взбитые сливки, ваниль и жареный каштан на мягкой подложке из сандала и кашемирового дерева.',
 promo='Белая футболка и кожаная куртка в одном флаконе: нежность жасмина и взбитых сливок с рок-характером сандала и каштана. Уютный, обволакивающий и при этом дерзкий аромат для тех, кто не выбирает между мягкостью и свободой.',
)
FEATURES = {('V20', 'МУЖСКИЕ АРОМАТЫ'): V20, ('Z1', 'ЖЕНСКИЕ АРОМАТЫ'): Z1}
TAIL_PHOTO = 'УНИСЕКС'   # the shop photo goes under the last cards of this section

def spaced(c, x, y, text, font, size, col, cs, align='c'):
    w_ = sw(text, font, size) + cs*(len(text)-1)
    x0 = x - w_/2 if align == 'c' else (x - w_ if align == 'r' else x)
    t = c.beginText(x0, H-y); t.setFont(font, size); t.setFillColorRGB(*col); t.setCharSpace(cs); t.textOut(text); t.setCharSpace(0); c.drawText(t)

def centred_lines(c, x, y, text, font, size, width, lead, col):
    for ln in wrap_words(text, font, size, width):
        c.setFont(font, size); c.setFillColorRGB(*col); c.drawCentredString(x, H-y, ln); y += lead
    return y

def awards_page(c):
    """Medals across the whole page + award facts as a small infographic."""
    cream = (0.97,0.93,0.85); gold = (0.88,0.71,0.44); ink = (0.19,0.13,0.10); bronze = (0.52,0.35,0.16)
    c.drawImage(f'{D}/awards/bg_new.jpg', 0, 0, W, H)
    c.drawImage(f'{D}/logo.png', W/2-55, H-178, 110, 115, mask='auto')
    spaced(c, W/2, 232, 'ETIB PARFUM', CG, 44, cream, 11)
    c.setFillColorRGB(*cream); c.setFont(CG, 84); c.drawCentredString(W/2, H-318, 'Победитель')
    c.setFillColorRGB(*gold); c.setFont('CormorantGaramond-MediumItalic', 46); c.drawCentredString(W/2, H-368, 'международных премий')
    med = Image.open(f'{D}/awards/medals.png'); mw = W - 36; mh = mw*med.height/med.width; mt = 398
    c.drawImage(f'{D}/awards/medals.png', 18, H-mt-mh, mw, mh, mask='auto')
    cx = [18 + mw*f for f in (0.168, 0.497, 0.826)]; ty = mt + mh + 50
    # frosted panel so the background's gold curves never cross the text
    c.setFillColorRGB(0.985,0.965,0.935); c.setFillAlpha(0.88); c.setStrokeColorRGB(*gold); c.setLineWidth(0.8)
    c.roundRect(36, H-(ty+398), W-72, 446, 24, stroke=1, fill=1); c.setFillAlpha(1)
    c.setStrokeColorRGB(*bronze); c.setLineWidth(0.9); c.line(cx[0], H-ty, cx[2], H-ty)
    data = [('2025', 'НОМЕР ОДИН', 'Бренд парфюмерии белорусского производства №1'),
            ('2025', 'НАРОДНЫЙ ВЫБОР', 'Магазин парфюмерной косметики'),
            ('2026', 'НАРОДНЫЙ ВЫБОР', 'Магазин парфюмерной косметики')]
    for x, (yr, prize, nom) in zip(cx, data):
        c.setStrokeColorRGB(*bronze); c.setLineWidth(0.9); c.line(x, H-(ty-28), x, H-ty)
        c.setFillColorRGB(*bronze); p = c.beginPath(); r = 6
        p.moveTo(x-r, H-ty); p.lineTo(x, H-ty+r); p.lineTo(x+r, H-ty); p.lineTo(x, H-ty-r); p.close(); c.drawPath(p, stroke=0, fill=1)
        c.setFillColorRGB(*ink); c.setFont(CG, 72); c.drawCentredString(x, H-(ty+68), yr)
        spaced(c, x, ty+106, prize, SB, 13.5, bronze, 3.2)
        spaced(c, x, ty+127, 'НОМИНАЦИЯ', M, 7.5, ink, 2.6)
        centred_lines(c, x, ty+148, nom, M, 12.5, 215, 18, ink)
    fy = ty + 222; c.setStrokeColorRGB(*bronze); c.setLineWidth(0.5); c.line(90, H-fy, W-90, H-fy)
    figs = [('3', 'международные награды'), ('№1', 'бренд парфюмерии белорусского производства'), ('2', 'года подряд — «Народный выбор»')]
    for x, (big_, cap) in zip(cx, figs):
        c.setFillColorRGB(*bronze); c.setFont(CG, 88); c.drawCentredString(x, H-(fy+84), big_)
        centred_lines(c, x, fy+130, cap.upper(), SB, 9.5, 200, 15, ink)
    c.showPage()

def collection_page(c, counts):
    """Brand page: large note-photo strip on top, one curved row of bottles with shadows and reflections, catalog figures."""
    INK = (0.17,0.13,0.14); acc = (0.45,0.27,0.31); ch = 430.0
    c.setFillColorRGB(0.965,0.957,0.961); c.rect(0, 0, W, H, stroke=0, fill=1)
    photos = ['notes/lime', 'notes/lavender', 'notes/jasmine', 'notes/amber', 'notes/rosemary', 'notes/vanilla']; cw = W/len(photos)
    for i, ph in enumerate(photos): c.drawImage(cover_img(f'{D}/{ph}.jpg', cw, ch, 2), i*cw, H-ch, cw+0.5, ch)
    g = Image.new('RGBA', (1, 256)); g.putdata([(0, 0, 0, int(255*0.55*(1-i/255)**1.5)) for i in range(256)]); g.save(f'{D}/topfade.png')
    c.drawImage(f'{D}/topfade.png', 0, H-260, W, 260, mask='auto')
    for i, ln in enumerate(('Твой аромат —', 'твоё настроение')):
        t = c.beginText(44, H-(96+i*56)); t.setFont(SB, 58); t.setFillColorRGB(1,1,1); t.setCharSpace(-2.6); t.textOut(ln); t.setCharSpace(0); c.drawText(t)
    # one row on a gentle arc: the centre bottle stands closest (largest, lowest), the sides step back
    row = [('new/p5_bottle', 262, -44), ('new/p2_bottle', 304, -18), ('new/p4_bottle', 340, 0), ('new/p6_bottle', 304, -18), ('new/p1_bottle', 226, -44)]
    floor = 868.0; gap = 14.0; items = []
    for name, bh, dy in row:
        fn = styled_bottle(f'{D}/{name}.png', refl=0.62, shade=0.8, tag='_show'); iw, ih = Image.open(fn).size; h = bh/BASE
        items.append([fn, h*iw/ih, h, dy])
    x = (W - sum(i[1] for i in items) - gap*(len(items)-1)) / 2
    for it in items: it.append(x + it[1]/2); x += it[1] + gap
    # floor shadow: one soft band that follows the arc under every bottle
    sc = 2; sh = Image.new('L', (int(W*sc), int(260*sc)), 0); from PIL import ImageDraw, ImageFilter; d = ImageDraw.Draw(sh)
    pts = [(it[4], it[3]) for it in items]
    for i in range(len(pts)-1):
        (x0, y0), (x1, y1) = pts[i], pts[i+1]
        for t in range(0, 41):
            xx = x0 + (x1-x0)*t/40; yy = y0 + (y1-y0)*t/40 + 130
            d.ellipse(((xx-70)*sc, (yy-9)*sc, (xx+70)*sc, (yy+9)*sc), fill=120)
    for it in items: d.ellipse(((it[4]-it[1]*0.55)*sc, (it[3]+130-11)*sc, (it[4]+it[1]*0.55)*sc, (it[3]+130+11)*sc), fill=150)
    sh = sh.filter(ImageFilter.GaussianBlur(13*sc)); band = Image.new('RGBA', sh.size, (60, 45, 40, 0)); band.putalpha(sh.point(lambda v: int(v*0.55)))
    band.save(f'{D}/floor_band.png'); c.drawImage(f'{D}/floor_band.png', 0, H-(floor-130+6)-260, W, 260, mask='auto')
    for fn, w, h, dy, cx_ in sorted(items, key=lambda r: r[3]):
        c.drawImage(fn, cx_-w/2, H-(floor + dy + h*(1-BASE)), w, h, mask='auto')
    fy = 1010.0; total = sum(counts.values())
    c.setStrokeColorRGB(0.80,0.74,0.70); c.setLineWidth(0.5); c.line(60, H-fy, W-60, H-fy)
    c.setFillColorRGB(*acc); c.setFont(CG, 96); c.drawString(60, H-(fy+88), str(total))
    spaced(c, 64, fy+134, 'АРОМАТОВ В КОЛЛЕКЦИИ', M, 10, INK, 3, align='l')
    for x, (sec, n) in zip([330, 455, 580, 705], counts.items()):
        c.setFillColorRGB(*INK); c.setFont(CG, 58); c.drawString(x, H-(fy+72), str(n))
        spaced(c, x+2, fy+110, SEC[sec]['title'].split()[0].upper(), M, 9, SEC[sec]['acc'], 2.4, align='l')
        f_ = 96*n/max(counts.values())
        c.setFillColorRGB(*SEC[sec]['acc']); c.rect(x+2, H-(fy+126), f_, 3, stroke=0, fill=1)
        c.setFillColorRGB(0.88,0.85,0.84); c.rect(x+2+f_, H-(fy+126), 96-f_, 3, stroke=0, fill=1)
    c.showPage()

ORDER = list(SEC)
plan = []   # (kind, section, payload)
for sec in ORDER:
    items = section(sec); pages = [items[i:i+12] for i in range(0, len(items), 12)]
    feats = [(next(c for c in raw if c['code'] == code and c['section'] == fs), FEATURES[(code, fs)]) for code, fs in sorted(FEATURES) if fs == sec]
    inl = [f for f in feats if f[1]['inline']]
    for i, pg in enumerate(pages):
        last = i == len(pages)-1
        plan.append(('grid', sec, dict(items=pg, tail=last and sec == TAIL_PHOTO, deco=last and sec == ORDER[-1], inline=inl[0] if last and inl and len(pg) <= 3 else None)))
    for f in feats:
        if not f[1]['inline']: plan.append(('feature', sec, f))
    if sec == ORDER[0]: plan += [('awards', sec, None), ('collection', sec, None)]
total = len(plan)
tmp = f'{D}/v3_cards.pdf'; c = canvas.Canvas(tmp, pagesize=(W, H), pageCompression=1); c.setTitle('ETIB PARFUM catalog')
for n, (kind, sec, pl) in enumerate(plan, 1):
    if kind == 'grid': grid_page(c, sec, pl['items'], n, total, tail=pl['tail'], inline=pl['inline'], deco=pl['deco'])
    elif kind == 'feature':
        chrome(c, sec, [pl[0]['code']], n, total); feature_block(c, pl[0], pl[1], 80, H - 44); c.showPage()
    elif kind == 'awards': awards_page(c)
    elif kind == 'collection': collection_page(c, {s_: len(section(s_)) + sum(1 for k_ in FEATURES if k_[1] == s_) for s_ in ORDER})
c.save()
src = pypdf.PdfReader(SRC); gen = iter(pypdf.PdfReader(tmp).pages); w = pypdf.PdfWriter()
for kind, sec, pl in plan: w.add_page(src.pages[pl] if kind == 'src' else next(gen))
from pypdf.generic import NameObject
seen = set()
for pg in w.pages:   # flate RGB images -> JPEG (alpha masks stay lossless)
    xo = pg['/Resources'].get('/XObject', {})
    for k in xo:
        o = xo[k].get_object()
        if id(o) in seen or o.get('/Subtype') != '/Image': continue
        seen.add(id(o)); flt = o.get('/Filter'); flt = [flt] if not isinstance(flt, list) else list(flt)
        if flt != ['/FlateDecode'] or o.get('/ColorSpace') != '/DeviceRGB' or o.get('/BitsPerComponent') != 8 or '/DecodeParms' in o: continue
        rawd = o.get_data(); wd, ht = o['/Width'], o['/Height']
        if len(rawd) != wd*ht*3: continue
        buf = io.BytesIO(); Image.frombytes('RGB', (wd, ht), rawd).save(buf, 'JPEG', quality=90, subsampling=0)
        o._data = buf.getvalue(); o[NameObject('/Filter')] = NameObject('/DCTDecode')
w.write(OUT)
print('pages', total, os.path.getsize(OUT)//1024, 'KB')
