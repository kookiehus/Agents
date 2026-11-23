"""ETIB PARFUM catalog — editorial style (white pages, bold grotesque, dark warm frames).
Usage: python3 build_editorial_v1.py <copy of assets/data> <assets/fonts> none <out.pdf>
Data logic (sections, new items, replaced bottles, note wrapping, shop cut-outs) is reused from build_v47.py."""
import sys, os
SRC_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build_v47.py')
code = open(SRC_SCRIPT).read(); code = code[:code.index('ORDER = list(SEC)')]
OUT_REAL = sys.argv[4]
exec(compile(code, SRC_SCRIPT, 'exec'))
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fragrance_review.py'), encoding='utf-8').read())
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fragrantica_notes.py'), encoding='utf-8').read())
def wrap_notes(text, size, width):
    """v47: even note lines. Breaks go after a comma by preference; a two-word note may be split between its words
    only when that saves a large gap at the end of a line (dynamic programming over all break points)."""
    words = text.split(); n = len(words)
    if not n: return []
    sp = sw(' ', R, size); ww = [sw(w, R, size) for w in words]
    INF = float('inf'); best = [INF]*(n + 1); nxt = [n]*(n + 1); best[n] = 0.0
    for i in range(n - 1, -1, -1):
        L = -sp
        for j in range(i, n):
            L += sp + ww[j]
            if L > width and j > i: break
            last = j == n - 1
            slack = 0.0 if last else (width - L)/width
            inner = 0.0 if last or words[j].endswith(',') else 0.18   # splitting inside a note
            c = slack*slack + inner + best[j + 1]
            if c < best[i]: best[i], nxt[i] = c, j + 1
    lines, i = [], 0
    while i < n: lines.append(' '.join(words[i:nxt[i]])); i = nxt[i]
    return lines
   # v42: pyramids as on Fragrantica
_section0 = section
SITE = json.load(open(f'{D}/bottles_site/index.json'))       # bottles cut from the site catalogue photos (scripts/cut_site_bottles.py)
SITE_SKIP = {'B10', 'A17', 'V23', 'C36', 'T1', 'N2', 'M1', 'M2', 'T2', 'T6'}   # previous cut-outs kept (dark edges on the black photos, or the owner preferred the old picture)
def styled_heel(src):
    """Shoe bottle: every column is mirrored from its own lowest point (the heel tip and the toe each stand on their reflection),
    soft contact shadow only under the toe and the heel tip. Same layout as styled_bottle (bottle = top BASE of the image)."""
    out = src.replace('.png', '_heel.png')
    if not os.path.exists(out):
        im = Image.open(src).convert('RGBA'); im = im.crop(im.getchannel('A').point(lambda v: 255 if v > 150 else 0).getbbox())
        k = 660/im.height; im = im.resize((round(im.width*k), 660), Image.LANCZOS)
        a = np.array(im).astype(float); bh, bw = a.shape[:2]; th = round(bh/BASE); R = th - bh; pad = round(bw*0.04)
        al = a[..., 3] > 128; has = al.any(axis=0); yb = np.where(has, bh - 1 - np.argmax(al[::-1], axis=0), 0)
        cv = np.zeros((th, bw + 2*pad, 4))
        for x in np.where(has)[0]:
            b = int(yb[x]); n = min(R + (bh - 1 - b), b + 1)
            col = a[b - n + 1:b + 1, x][::-1].copy(); d = np.arange(n)
            col[:, 3] *= 0.46*np.clip(1 - d/(R*0.94), 0, 1)**1.35
            y0 = b + 1; y1 = min(th, y0 + n); cv[y0:y1, x + pad] = col[:y1 - y0]
        sh = np.zeros((th, bw + 2*pad)); low = yb[has].max()
        for x in np.where(has & (yb >= low - bh*0.03))[0]: sh[yb[x] - 6:yb[x] + 4, x + pad] = 1
        shi = Image.fromarray((sh*255).astype('uint8')).filter(ImageFilter.GaussianBlur(th*0.012)).point(lambda v: int(v*0.6))
        img = Image.new('RGBA', (bw + 2*pad, th), (12, 10, 10, 0)); img.putalpha(shi)
        img.alpha_composite(Image.fromarray(cv.astype('uint8'), 'RGBA')); img.alpha_composite(im, (pad, 0)); img.save(out)
    im = Image.open(out); s = min(112/im.width, 158/im.height); w, h = im.width*s, im.height*s
    return (out, 76 - w/2, 233.45 + h*(1 - BASE) - h, w, h)
def styled_lit(src, refl=0.85, lift=(1.9, 62), tag='_v57lit'):
    """Black bottle: the mirror image is lightened (v*a + b) so the reflection reads as grey glass on the dark panel."""
    base = src.replace('.png', f'{tag}_src.png')
    if not os.path.exists(base):
        im = Image.open(src).convert('RGBA'); im.save(base)
    out = styled_bottle(base, refl=refl, tag=tag)
    if not os.path.exists(out.replace('.png', '_lit.png')):
        from PIL import ImageChops
        im = Image.open(base).convert('RGBA'); im = im.crop(im.getchannel('A').point(lambda v: 255 if v > 150 else 0).getbbox())
        k = 660/im.height; im = im.resize((round(im.width*k), 660), Image.LANCZOS)
        bw, bh = im.size; th = round(bh/BASE); pad = round(bw*0.04); end = round(th*0.94) - bh
        rf = im.transpose(Image.FLIP_TOP_BOTTOM); a_, b_ = lift
        r, g, b, al = rf.split(); rf = Image.merge('RGBA', tuple(ch.point(lambda v: min(255, int(v*a_ + b_))) for ch in (r, g, b)) + (al,))
        ramp = Image.new('L', (1, bh)); ramp.putdata([int(255*refl*max(0.0, 1 - y/end)**1.35) for y in range(bh)])
        rf.putalpha(ImageChops.multiply(rf.getchannel('A'), ramp.resize((bw, bh))))
        cv = Image.open(out).convert('RGBA'); top = cv.crop((0, 0, cv.width, bh))        # bottle part from the standard styling
        low = Image.new('RGBA', (cv.width, cv.height - bh), (0, 0, 0, 0)); low.alpha_composite(rf.crop((0, 0, bw, th - bh)), (pad, 0))
        shadow = cv.crop((0, bh, cv.width, cv.height))                                    # keep the contact shadow under the base
        sh_only = Image.new('RGBA', shadow.size, (12, 10, 10, 0)); sh_only.putalpha(shadow.getchannel('A').point(lambda v: v if v < 200 else 200))
        res = Image.new('RGBA', cv.size, (0, 0, 0, 0)); res.alpha_composite(top, (0, 0))
        res.alpha_composite(low, (0, bh)); res.save(out.replace('.png', '_lit.png'))
    path = out.replace('.png', '_lit.png')
    im = Image.open(path); s_ = min(112/im.width, 158/im.height); w, h = im.width*s_, im.height*s_
    return (path, 76 - w/2, 233.45 + h*(1 - BASE) - h, w, h)
NEW74 = {('МУЖ', 'A17'), ('ЖЕН', 'K2'), ('УНИ', 'E33'), ('МУЖ', 'D18'), ('МУЖ', 'A1'), ('ЖЕН', 'L8'), ('ЖЕН', 'D9')}
CLEAN73 = {'ЖЕН': ('C4', 'D1', 'D3', 'E10', 'G2', 'G4', 'H4', 'H14', 'L8', 'V23', 'Z1'), 'МУЖ': ('T1', 'K23'), 'УНИ': ('L10',), 'ПРЕ': ('N10', 'T14', 'L4', 'K5')}
SCALE73 = {('ЖЕН', 'G4'): 0.88, ('ПРЕ', 'T14'): 0.86, ('ПРЕ', 'T20'): 0.88, ('МУЖ', 'C36'): 0.90, ('МУЖ', 'C10'): 0.92, ('ПРЕ', 'K4'): 0.92}   # very wide bottles brought in line with their row
def rescale(img, f):
    p, x, y, w, h = img; w2, h2 = w*f, h*f
    return (p, 76 - w2/2, 233.45 + h2*(1 - BASE) - h2, w2, h2)
NAME73 = {('ЖЕН', 'A10'): ('GIVENCHY ANGE OU DEMON LE SECRET', 'Живанши Анж у Демон Ле Секрет'),
          ('ЖЕН', 'V9'): ("VICTORIA'S SECRET BOMBSHELL 2", None), ('ЖЕН', 'V11'): ("VICTORIA'S SECRET BOMBSHELL 3", None),
          ('ЖЕН', 'E10'): ("LANVIN ECLAT D'ARPÈGE", "Ланвин Эклат д'Арпеж"),
          ('МУЖ', 'K23'): ("KENZO L'EAU PAR KENZO POUR HOMME", 'Кензо Ло Пар Кензо Пур Хомм'),
          ('МУЖ', 'D18'): ('ALFRED DUNHILL DESIRE BLUE', 'Альфред Данхилл Дизайр Блю'),
          ('МУЖ', 'L17'): ('LACOSTE L.12.12 WHITE', 'Лакост Л.12.12 Уайт'),
          ('ПРЕ', 'K4'): ("BY KILIAN ANGELS' SHARE", 'Бай Килиан Энджелс Шер'),
          ('ПРЕ', 'B9'): ('MARC-ANTOINE BARROIS TILIA 2024', None)}
RU73 = [(r"Л'Эндерди", "Л'Энтерди"), (r'Кензо Ле Пар', 'Кензо Ло Пар'), (r'\bГермес\b', 'Эрмес'), (r'\bМэйсон\b', 'Мезон'),
        (r'Хэз Э Ган', 'Хэз э Ган'), (r'Джульетта Хэз', 'Джульетт Хэз'), (r'\bЭТИБ\b', 'Этиб'), (r'Жан Поль Готье', 'Жан-Поль Готье'),
        (r'\bХом\b', 'Хомм')]
YO74 = [(r'(?<![а-яё])черн(?=(ый|ая|ое|ые|ого|ой|ую|ым|ых|ом)(?![а-яё]))', 'чёрн'), (r'(?<![а-яё])зелен(?=(ый|ая|ое|ые|ого|ой|ую|ым|ых|ом)(?![а-яё]))', 'зелён'),
        (r'(?<![а-яё])желт(?=(ый|ая|ое|ые|ого|ой|ую|ым|ых|ом)(?![а-яё]))', 'жёлт'), (r'(?<![а-яё])берез', 'берёз'), (r'ликер', 'ликёр'), (r'(?<![а-яё])мед(?![а-яё])', 'мёд')]
NOTE73 = [(r'пачули из Индонезии, пачули', 'индонезийские пачули'), (r'индонезийский пачули', 'индонезийские пачули'),
          (r'гурьюнский бальзам', 'бальзам гурджун'), (r'вирджинск', 'виргинск'), (r'цеталокс \(cetalox\)', 'цеталокс'), (r'\bлед\b', 'лёд')]
def polish_text(s3, it):
    """v73 proofreading fixes (names, transliterations, notes)."""
    import re as _r
    nm = NAME73.get((s3, it['code']))
    if nm:
        it['name'] = nm[0]
        if nm[1]: it['ru'] = nm[1]
    for a_, b_ in RU73: it['ru'] = _r.sub(a_, b_, it.get('ru', ''))
    for k_ in ('name', 'ru'):                                                       # v74: 'F. 09 2018' / 'ф. 2012' / 'M. 2014' -> just the year
        it[k_] = _r.sub(r'\s[FMФМфм]\.\s(?:\d{2}\s)?(\d{4})', r' \1', it[k_])
    it['ru'] = it['ru'].replace('СК Ол', 'Си Кей Олл').replace('СН Куинс', 'Си Эйч Куинс')
    it['notes'] = [(h_, _r.sub(r'(?<!\w)лед(?!\w)', 'лёд', _polish_note(t_))) for h_, t_ in it['notes']]
def _polish_note(t_):
    import re as _r
    for a_, b_ in NOTE73[:-1]: t_ = _r.sub(a_, b_, t_)
    for a_, b_ in YO74: t_ = _r.sub(a_, b_, t_)                                     # v74: ё in the notes, as in the rest of the catalogue
    return t_
def section(sec):
    items = apply_fragrantica(SEC_KEY[sec], apply_review(sec, _section0(sec)))
    for it in items:
        k = f"{it['code']}|{sec[:3]}"
        if k in SITE and it['code'] not in SITE_SKIP:
            it['img'] = styled(f"{D}/bottles_site/{it['code']}_{sec[:3]}.png", tag='_site'); it['site'] = True
        if it['code'] == 'C7' and k in SITE: it['img'] = styled_heel(f"{D}/bottles_site/C7_ЖЕН.png")
        v23 = f"{D}/bottles_v27/{it['code']}_{sec[:3]}.png"                   # v25 cut-outs + exact outlines (scripts/fix_bottles_v26.py)
        if os.path.exists(v23): it['img'] = styled(v23, tag='_v23')
        if it['code'] == 'A2' and sec[:3] == 'ЖЕН': it['img'] = styled(f"{D}/bottles_v35/A2_ЖЕН.png", refl=0.26, tag='_v40')   # owner's photo (scripts/prepare_bottles_v35.py)
        if it['code'] == 'A20' and sec[:3] == 'ЖЕН': it['img'] = styled(f"{D}/bottles_v43/A20_ЖЕН.png", refl=0.22, tag='_v43')   # owner's photo (scripts/prepare_bottles_v43.py)
        if sec[:3] == 'МУЖ' and it['code'] in ('D24', 'P17', 'T12'): it['img'] = styled(f"{D}/bottles_v49/{it['code']}_МУЖ.png", refl=0.22, tag='_v49')   # owner's photos (scripts/prepare_bottles_v49.py)
        if it['code'] == 'G10' and sec[:3] == 'ЖЕН': it['img'] = styled(f"{D}/bottles_v50/G10_ЖЕН.png", refl=0.22, tag='_v50')   # owner's photo (scripts/prepare_bottles_v50.py)
        if sec[:3] == 'ЖЕН' and it['code'] in ('E9', 'E22', 'E25', 'V25', 'S2', 'V15'): it['img'] = styled(f"{D}/bottles_v53/{it['code']}_ЖЕН.png", refl=0.22, tag='_v53')   # owner's photos, S2 bottom cleaned, glow-free edges, E25 clean seam (scripts/prepare_bottles_v53.py)
        if sec[:3] == 'ЖЕН' and it['code'] in ('B18', 'E2', 'E20', 'S7'): it['img'] = styled(f"{D}/bottles_v55/ETIB_white.png", refl=0.22, tag='_v55')   # owner's new ETIB PARFUM house bottle, whiter (scripts/prepare_bottles_v54.py + v55.py)
        if sec[:3] == 'ПРЕ' and it['code'] in ('E3', 'E4'): it['img'] = styled_lit(f"{D}/bottles_v56/ETIB_black.png")   # owner's new black ETIB PARFUM house bottle, lighter reflection (scripts/prepare_bottles_v56.py)
        if sec[:3] == 'ПРЕ' and it['code'] == 'T20': it['img'] = styled(f"{D}/bottles_v63/T20_ПРЕ.png", refl=0.24, tag='_v63')   # owner's photo, cap top follows its arc (scripts/prepare_bottles_v63.py)
        if sec[:3] == 'ЖЕН' and it['code'] == 'C27': it['img'] = styled(f"{D}/bottles_v66/C27_ЖЕН.png", refl=0.24, tag='_v66')   # owner's photo, with the clear glass base (scripts/prepare_bottles_v65.py)
        if it['code'] == 'V23': it['img'] = styled(f"{D}/bottles_v27/V23_ЖЕН.png", refl=0.20, tag='_v34')   # pale bevelled base: softer reflection, no grey slab under it
        if it['code'] == 'V22': it['img'] = styled(f"{D}/bottles_v33/V22_ЖЕН.png", tag='_v33')   # white strip under the base removed (scripts/fix_bottles_v33.py)
        if it['code'] == 'V19': it['img'] = styled(f"{D}/bottles_v30/V19_ЖЕН.png", tag='_v30')   # owner's photo (scripts/prepare_bottles_v30.py)
        k3 = (sec[:3], it['code'])
        if k3[1] in CLEAN73.get(k3[0], ()): it['img'] = styled(f"{D}/bottles_v73/{it['code']}_{sec[:3]}.png", refl=0.20 if it['code'] == 'V23' else 0.46, tag='_v73')   # v73: outlines cleaned (scripts/clean_bottles_v73.py)
        if k3 == ('ПРЕ', 'K6'): it['img'] = styled(f"{D}/bottles_site/K6_ПРЕ.png", refl=0.22, tag='_v73k')      # softer reflection under the label block
        if k3 in NEW74: it['img'] = styled(f"{D}/bottles_v74/{it['code']}_{sec[:3]}.png", refl=0.30 if k3[1] in ('A17', 'D18') else 0.40, tag='_v74')   # v74: owner's photos (scripts/prepare_bottles_v74.py)
        if k3 == ('ЖЕН', 'G4'): it['img'] = styled(f"{D}/bottles_v75/G4_ЖЕН.png", refl=0.40, tag='_v75')   # v75: owner's photo (scripts/prepare_bottles_v75.py)
        if k3 in (('ЖЕН', 'H4'), ('ЖЕН', 'H14'), ('ЖЕН', 'G4'), ('ЖЕН', 'L8')): it['img'] = styled(f"{D}/bottles_v76/{it['code']}_ЖЕН.png", refl=0.40, tag='_v76')   # v76: exact outlines (scripts/prepare_bottles_v76.py)
        if k3 in SCALE73: it['img'] = rescale(it['img'], SCALE73[k3])
        polish_text(sec[:3], it)
    if sec[:3] == 'ЖЕН':                                                       # both Trussardi Donna in the same bottle (as T2)
        by = {it['code']: it for it in items}
        if 'T2' in by and 'T15' in by: by['T15']['img'] = by['T2']['img']
    return items
import numpy as np
from PIL import ImageFilter
from scipy import ndimage as nd
from PIL import ImageDraw
for f in ('Montserrat-ExtraBold', 'Montserrat-Bold'): pdfmetrics.registerFont(TTFont(f, f'{FONTS}/{f}.ttf'))
XB, B = 'Montserrat-ExtraBold', 'Montserrat-Bold'
INK = (0.07, 0.07, 0.07); GREY = (0.42, 0.42, 0.42); LINE = (0.82, 0.82, 0.82); WHITE = (1, 1, 1); SOFT = (0.80, 0.78, 0.76)
BLACK = (0.045, 0.04, 0.037); STONE = (0.945, 0.938, 0.925)
ML = 31.5; MR = W - 31.5
os.makedirs(f'{D}/ed', exist_ok=True)
ORDER = list(SEC)
FOOT = 'ВСЕ ФЛАКОНЫ АРОМАТОВ ИЗГОТОВЛЕНЫ В ФИРМЕННОМ СТИЛЕ ETIB PARFUM'

# ---------------------------------------------------------------- text helpers
def tw_(s, f, sz, cs=0): return sw(s, f, sz) + cs*len(s)
def txt(c, x, y, s, f, sz, col=INK, cs=0, align='l'):
    if align == 'r': x -= tw_(s, f, sz, cs) - cs
    elif align == 'c': x -= (tw_(s, f, sz, cs) - cs)/2
    t = c.beginText(x, H-y); t.setFont(f, sz); t.setFillColorRGB(*col); t.setCharSpace(cs); t.textOut(s); t.setCharSpace(0); c.drawText(t)
import re as _re
SHORT = r'(?:в|во|на|за|от|до|по|из|к|ко|с|со|о|об|у|и|а|но|не|для|без|под|над|при|про)'
def glue(text):
    """v66: short prepositions / conjunctions go to the next line with their word; a dash never starts a line."""
    text = _re.sub(r'(?<=\s)(' + SHORT + r') (?=\S)', '\\1\u00a0', text, flags=_re.I)
    text = _re.sub(r'^(' + SHORT + r') (?=\S)', '\\1\u00a0', text, flags=_re.I)
    return text.replace(' — ', '\u00a0— ')
def wrap(text, f, sz, width, cs=0):
    out, cur = [], ''
    text = glue(text)
    meas = lambda t: tw_(t.replace('\u00a0', ' '), f, sz, cs)
    for w_ in text.split(' '):
        t = (cur + ' ' + w_).strip()
        if meas(t) <= width or not cur: cur = t
        else: out.append(cur); cur = w_
    return [l_.replace('\u00a0', ' ') for l_ in out + ([cur] if cur else [])]
def para(c, x, y, text, f, sz, width, lead, col=INK, cs=0):
    for ln in wrap(text, f, sz, width, cs): txt(c, x, y, ln, f, sz, col, cs); y += lead
    return y
def hline(c, x0, x1, y, col=LINE, lw=0.4): c.setStrokeColorRGB(*col); c.setLineWidth(lw); c.line(x0, H-y, x1, H-y)
def button(c, x, y, s, fill=INK, col=WHITE, sz=6.2, pad=13, h=21, stroke=None):
    """Rectangular label 'button' (top-left x, y). Returns its width."""
    w_ = tw_(s, B, sz, 1.6) - 1.6 + 2*pad
    if fill: c.setFillColorRGB(*fill); c.rect(x, H-y-h, w_, h, stroke=0, fill=1)
    if stroke: c.setStrokeColorRGB(*stroke); c.setLineWidth(0.6); c.rect(x, H-y-h, w_, h, stroke=1, fill=0)
    txt(c, x + pad, y + h/2 + sz*0.36, s, B, sz, col, cs=1.6); return w_
def fit_size(lines, f, width, cap, cs_k=-0.03):
    sz = cap
    while max(tw_(l, f, sz, cs_k*sz) for l in lines) > width: sz -= 0.5
    return sz

# ---------------------------------------------------------------- images
def grad_img(name, a, b, wpx, hpx, glow=0.10, gcol=(1, 1, 1), gx=0.4, gy=0.55):
    out = f'{D}/ed/{name}.jpg'
    if not os.path.exists(out):
        yy, xx = np.mgrid[0:hpx, 0:wpx]; a = np.array(a); b = np.array(b)
        t = np.clip((xx/wpx)*0.45 + (yy/hpx)*0.75, 0, 1)[..., None]
        g = np.exp(-(((xx-wpx*gx)/(wpx*0.6))**2 + ((yy-hpx*gy)/(hpx*0.45))**2))[..., None]*glow
        rgb = np.clip(a*(1-t) + b*t + g*np.array(gcol), 0, 1)
        rgb += (np.random.RandomState(1).rand(hpx, wpx, 1) - 0.5)/255*1.5            # dither against banding
        Image.fromarray((np.clip(rgb, 0, 1)*255).astype('uint8')).save(out, quality=93)
    return out
def terra_bg():
    """Warm terracotta page, the colour of the wood poster: dark umber at the top, burnt orange towards the bottom."""
    out = f'{D}/ed/terra_poster.jpg'                                          # colours sampled from the poster's background
    if not os.path.exists(out):
        hh, ww = 1700, 1200; yy, xx = np.mgrid[0:hh, 0:ww]
        t = np.clip((xx/ww)*0.35 + (yy/hh)*0.85 - 0.05, 0, 1)[..., None]
        stops = np.array([[0.10, 0.012, 0.004], [0.36, 0.075, 0.028], [0.74, 0.20, 0.035], [0.92, 0.37, 0.08]]); pos = np.array([0.0, 0.30, 0.68, 1.0])
        rgb = np.stack([np.interp(t[..., 0], pos, stops[:, i]) for i in range(3)], axis=-1)
        rgb += (np.random.RandomState(2).rand(hh, ww, 1) - 0.5)/255*1.5
        Image.fromarray((np.clip(rgb, 0, 1)*255).astype('uint8')).save(out, quality=94)
    return out
def panel_img(): return grad_img('panel_graphite', (0.24, 0.225, 0.215), (0.07, 0.065, 0.06), 472, 1020)

def toned(src, wpt, hpt, tag, sat=0.7, tint=(1.0, 0.88, 0.78), gain=0.72, gamma=1.0, focus=(0.5, 0.5), dpi=150, shade_bottom=0.0, shade_top=0.0, shade_left=0.0, blur=0):
    """Cover-crop a photo to wpt x hpt and tone it into the warm dark palette."""
    out = f'{D}/ed/t_{tag}.jpg'
    if not os.path.exists(out):
        im = Image.open(src).convert('RGB'); pw, ph = round(wpt/72*dpi), round(hpt/72*dpi)
        k = max(pw/im.width, ph/im.height); im = im.resize((max(pw, round(im.width*k)), max(ph, round(im.height*k))), Image.LANCZOS)
        x = round((im.width - pw)*focus[0]); y = round((im.height - ph)*focus[1]); im = im.crop((x, y, x+pw, y+ph))
        if blur: im = im.filter(ImageFilter.GaussianBlur(blur))
        a = np.array(im).astype(float)/255; lum = a.mean(axis=2, keepdims=True)
        a = (np.clip(lum + (a - lum)*sat, 0, 1)**gamma)*np.array(tint)*gain
        yy = np.linspace(0, 1, ph)[:, None, None]; xx = np.linspace(0, 1, pw)[None, :, None]
        if shade_bottom: a *= 1 - shade_bottom*np.clip((yy - 0.35)/0.65, 0, 1)**1.3
        if shade_top: a *= 1 - shade_top*np.clip((0.30 - yy)/0.30, 0, 1)**1.5
        if shade_left: a = a*(1 - np.clip((0.22 - xx)/0.22, 0, 1)**1.4*shade_left) + np.array(BLACK)*np.clip((0.22 - xx)/0.22, 0, 1)**1.4*shade_left
        Image.fromarray((np.clip(a, 0, 1)*255).astype('uint8')).save(out, quality=90)
    return out

CLEAN = {'L10', 'C36', 'G18', 'H4', 'H14', 'N2', 'N10', 'A2', 'V21', 'V22', 'V23', 'C5'}   # cut-outs with pale fringes / jagged outline
def prep_bottle(path, code):
    """Bottle for the dark panel: slightly calmer colour, glare compressed; listed cut-outs get their pale fringe removed."""
    out = f"{D}/ed/b28_{code}_{os.path.basename(path)}"
    if os.path.exists(out): return out
    im = Image.open(path).convert('RGBA'); a = np.array(im).astype(float)/255; rgb, al = a[..., :3], a[..., 3]
    if code in CLEAN and 'bottles_site' not in path:
        s_ = im.height/440.0; solid = al > 0.5; din = nd.distance_transform_edt(solid)
        core = din >= 5*s_
        if core.any():
            idx = nd.distance_transform_edt(~core, return_distances=False, return_indices=True)
            ref = rgb[idx[0], idx[1]]; wp = rgb.min(axis=2); wr = ref.min(axis=2)
            band = (din <= 2.6*s_) & (al > 0.03)
            kill = np.clip((wp - wr - 0.14)/0.16, 0, 1)*band*(wp > 0.62)
            al = al*(1 - kill)
        sm = nd.gaussian_filter((al > 0.5).astype(float), 1.1*s_); sm = np.clip((sm - 0.35)/0.3, 0, 1)
        al = np.where(al > 0.5, np.minimum(al, np.maximum(sm, 0.0)), al)
    rgb = enhance(rgb, al, im.height)
    lum = rgb.mean(axis=2, keepdims=True); rgb = lum + (rgb - lum)*0.95
    rgb = rgb - 0.05*rgb**5
    o = np.dstack([np.clip(rgb, 0, 1), al]); Image.fromarray((o*255).astype('uint8'), 'RGBA').save(out); return out

def enhance(rgb, al, h):
    """Print clean-up for every bottle: JPEG noise removed, levels set, local contrast and crisp detail, colours kept true.
    Only the bottle itself is graded (its levels are measured on the solid pixels; the reflection follows the same curve)."""
    import cv2
    u8 = (np.clip(rgb, 0, 1)*255).astype(np.uint8)
    den = cv2.fastNlMeansDenoisingColored(u8, None, 3, 3, 5, 15)                          # gentle: JPEG blocks and grain, not detail
    x = den.astype(np.float32)/255
    solid = al > 0.9
    if solid.sum() > 500:
        L = x.mean(axis=2)[solid]; lo, hi = np.percentile(L, 0.7), np.percentile(L, 99.6)
        lo = min(lo, 0.10); hi = max(hi, 0.85)                                             # never stretch a pale or a dark bottle hard
        st = np.clip((x - lo)/(hi - lo), 0, 1); x = x*0.4 + st*0.6
    lab = cv2.cvtColor((np.clip(x, 0, 1)*255).astype(np.uint8), cv2.COLOR_RGB2LAB)
    cl = cv2.createCLAHE(clipLimit=1.6, tileGridSize=(6, 6)).apply(lab[..., 0])
    lab[..., 0] = (lab[..., 0].astype(np.float32)*0.55 + cl.astype(np.float32)*0.45).astype(np.uint8)
    x = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB).astype(np.float32)/255
    r = max(0.8, h/900.0)                                                                 # detail sharpening scaled to the picture size
    bl = cv2.GaussianBlur(x, (0, 0), 1.1*r); x = x + (x - bl)*0.55
    sat = x.max(axis=2) - x.min(axis=2); lum = x.mean(axis=2, keepdims=True)
    vib = 1 + 0.10*np.clip(1 - sat/0.45, 0, 1)[..., None]                                 # a little more life in dull colours only
    return np.clip(lum + (x - lum)*vib, 0, 1)

def shop_tile(c, name, x, top, w_, h_, bg=STONE, pad=0.07, depth=0.14, base=0.90):
    """Light stone tile with a shop cut-out standing on its floor (soft shadow + reflection)."""
    c.setFillColorRGB(*bg); c.rect(x, H-top-h_, w_, h_, stroke=0, fill=1)
    fn = staged(name, depth=depth); iw, ih = Image.open(fn).size
    k = min(w_*(1-2*pad)/iw, h_*(1-2*pad)/ih); dw, dh = iw*k, ih*k
    c.drawImage(fn, x + (w_-dw)/2, H - top - (h_ + dh)/2 - min(h_*0.02, (h_-dh)/2), dw, dh, mask='auto')

# ---------------------------------------------------------------- card
PW, PH = 118.0, 255.0
SHIFTS = []
WHOLE_SHAPE = {'C7', 'C3'}   # shoe and butterfly bottles: the whole figure is centred
_BO = {}
_BF = {}
def base_frac(path):
    """Share of the image height down to the bottle's foot (last solid row; the reflection below is semi-transparent)."""
    if path not in _BF:
        a = np.array(Image.open(path).getchannel('A')); rows = np.where(a.max(axis=1) > 235)[0]
        _BF[path] = (rows[-1] + 1)/a.shape[0] if len(rows) else 0.756
    return _BF[path]
def body_offset(path):
    """Horizontal offset (share of the image width) of the bottle's body centre from the image centre.
    The body is measured in the middle band of the bottle (between the shoulders and the base, above the reflection)."""
    if path not in _BO:
        a = np.array(Image.open(path).getchannel('A')) > 128; h_, w_ = a.shape
        rows = np.where(a.any(axis=1))[0]; top_, bot_ = rows[0], rows[0] + (rows[-1] - rows[0] + 1)*0.756   # bottle without its reflection
        f0, f1 = (0.02, 0.30) if 'V19_ЖЕН' in path else (0.55, 0.90)       # V19: centre on the cap (the tassel widens the body)
        band = a[int(top_ + (bot_ - top_)*f0):int(top_ + (bot_ - top_)*f1)]
        cols = np.where(band.any(axis=0))[0]
        _BO[path] = ((cols[0] + cols[-1])/2 - (w_ - 1)/2)/w_ if len(cols) else 0.0
    return _BO[path]
def card(c, it, gx, gt, sec):
    x0, top = gx + 15.5, gt + 14.5
    c.drawImage(panel_img(), x0, H - top - PH, PW, PH)
    p, bx, by, bw_, bh = it['img']; k = min(1.14, 106.0/bw_, 196.0/bh); bw2, bh2 = bw_*k, bh*k
    pb = prep_bottle(p, it['code']); off = 0.0 if it['code'] in WHOLE_SHAPE else body_offset(pb)*bw2   # centre the bottle's body, not its outline (asymmetric caps)
    SHIFTS.append((it['code'], sec[:3], round(off, 1)))
    fr = base_frac(pb); base_y = top + PH - 46                                # every bottle stands on the same line
    c.saveState(); cp = c.beginPath(); cp.rect(x0 + 4, H - top - PH, PW - 8, PH); c.clipPath(cp, stroke=0, fill=0)   # ribbon / bulb tails trimmed just inside the panel
    c.drawImage(pb, x0 + PW/2 - bw2/2 - off, H - (base_y + bh2*(1 - fr)), bw2, bh2, mask='auto'); c.restoreState()
    txt(c, x0 + 11, top + 29, it['code'], XB, 22, WHITE, cs=-0.5)
    tx = x0 + PW + 14; tw = 250 - PW - 16; y = top + 13
    ns = 9.6; nl = wrap(it['name'], XB, ns, tw, -0.1)
    if len(nl) > 3: ns = 8.6; nl = wrap(it['name'], XB, ns, tw, -0.1)
    for ln in nl[:4]: txt(c, tx, y + 7, ln, XB, ns, cs=-0.1); y += ns*1.21
    y += 1
    for ln in wrap(it['ru'], R, 6.3, tw)[:2]: txt(c, tx, y + 6, ln, R, 6.3, GREY); y += 8.2
    y += 7
    pos = it.get('pos', SCALE.get(it['type'], 0.5))                         # fresh <-> sweet: one thin line with a dot (checked per fragrance)
    txt(c, tx, y + 1.9, 'СВЕЖИЙ', M, 5.0, GREY, cs=0.8); l0 = tx + 33; l1 = tx + tw - 37
    c.setStrokeColorRGB(*INK); c.setLineWidth(0.5); c.line(l0, H - y, l1, H - y)
    c.setFillColorRGB(*INK); c.circle(l0 + (l1-l0)*pos, H - y, 2.7, stroke=0, fill=1)
    txt(c, l1 + 5, y + 1.9, 'СЛАДКИЙ', M, 5.0, GREY, cs=0.8); y += 13
    tags = [t for t in it['tags'] if t not in DROP]; parts = [t.upper() for t in tags]; lines = []; cur = ''
    for i, t in enumerate(parts):                                           # break only after a '/'
        tok = t + ('  /' if i < len(parts)-1 else ''); cand = (cur + '  ' + tok).strip()
        if tw_(cand, SB, 5.2, 0.9) <= tw or not cur: cur = cand
        else: lines.append(cur); cur = tok
    lines += [cur] if cur else []
    for ln in lines[:3]: txt(c, tx, y + 2, ln, SB, 5.2, cs=0.9); y += 8.5
    y += 5; hline(c, tx, tx + tw, y); y += 6
    fs = 7.8; bottom = top + PH
    while True:
        blocks = [(h, wrap_notes(t, fs, tw)) for h, t in it['notes']]; gap = 6 if fs > 7.3 else 5 if fs > 6.2 else 3.5
        need = sum(10.5 + len(b)*fs*1.22 for _, b in blocks) + gap*(len(blocks)-1)
        if need <= bottom - y or fs <= 5.4: break
        fs -= 0.2
    if need > bottom - y + 0.5: print('  ! notes overflow', sec[:3], it['code'], round(need - (bottom - y), 1))
    for i, (h, b) in enumerate(blocks):
        txt(c, tx, y + 6, f'0{i+1}', XB, 5.6); txt(c, tx + 12, y + 6, h, SB, 5.2, GREY, cs=0.9); y += 10.5
        for ln in b: txt(c, tx, y + fs*0.72, ln, R, fs); y += fs*1.22
        y += gap

# ---------------------------------------------------------------- page chrome
def topbar(c, col=INK, sub=GREY, line=INK, right='КАТАЛОГ АРОМАТОВ'):   # v58: no year
    txt(c, ML, 28, 'ETIB PARFUM', M, 10, col, cs=5.2); txt(c, MR, 27, right, M, 6, sub, cs=1.6, align='r')
    hline(c, ML, MR, 38, line, 0.6)
def footer(c, col=GREY, line=LINE):
    hline(c, ML, MR, H - 30, line); txt(c, ML, H - 16, FOOT, M, 5.6, col, cs=1.5)
def chrome(c, sec, items):
    c.setFillColorRGB(1, 1, 1); c.rect(0, 0, W, H, stroke=0, fill=1); topbar(c)
    txt(c, ML, 53, kicker(sec), B, 6.6, cs=1.6)
    txt(c, ML - 1.5, 83, SEC[sec]['title'].upper(), XB, 32, cs=-1.0)
    rng = f"{items[0]['code']} — {items[-1]['code']}" if len(items) > 1 else items[0]['code']
    txt(c, MR, 83, rng, XB, 20, cs=-0.3, align='r'); txt(c, MR, 60, 'АРТИКУЛЫ', B, 6.6, GREY, cs=1.6, align='r')
    footer(c)
YO = 6.0
def cell_box(col0, row, cols=1, rows=1):
    """Outer box of a block of card cells: x0, top, x1, bottom."""
    return XS[col0] + 15.5, YS[row] + YO + 14.5, XS[col0 + cols - 1] + 265.5, YS[row + rows - 1] + YO + 269.5
def cards(c, sec, items):
    for i, it in enumerate(items): card(c, it, XS[i % 3], YS[i//3] + YO, sec)

# ---------------------------------------------------------------- section openers
HERO = {
 'ЖЕНСКИЕ АРОМАТЫ': dict(text='Цветочные, фруктовые, пудровые — от прозрачной свежести до тёплой сладости.'),
 'МУЖСКИЕ АРОМАТЫ': dict(text='Свежие, древесные, пряные — характер,\u00a0который слышно без слов.'),
 'УНИСЕКС':         dict(text='Ароматы вне правил: их выбирают не по полу, а по настроению.'),
 'ПРЕМИУМ':         dict(text='Самые выразительные композиции коллекции — для особого случая и для тех, кто\u00a0ищет своё.'),
}
COVER_W = 'w4'
def hero_bg(sec):
    if sec == ORDER[0]:                                                        # v74: owner's new picture for the women's cover
        cw_ = os.environ.get('COVERW', COVER_W)
        return toned(f'{D}/covers/{cw_}.jpg', W, H, 'hero_' + cw_, sat=0.92, tint=(1.02, 0.95, 0.88), gain=0.92, focus=(0.5, 0.35), shade_bottom=0.80, shade_top=0.35, blur=0.3, dpi=200)
    if sec == ORDER[2]: return toned(f'{D}/notes/amber.jpg', W, H, 'hero_u2', sat=0.72, tint=(0.98, 0.76, 0.62), gain=0.66, focus=(0.5, 0.3), shade_bottom=0.75, shade_top=0.35, blur=1.2)
    if sec == ORDER[3]: return toned(f'{D}/notes/vanilla.jpg', W, H, 'hero_p', sat=0.60, tint=(0.98, 0.84, 0.72), gain=0.52, focus=(0.5, 0.3), shade_bottom=0.80, shade_top=0.40, blur=1.2)
    return toned(f'{D}/v20/cardamom.jpg', W, H, 'hero_m3', sat=0.58, tint=(1.02, 0.80, 0.62), gain=0.64, focus=(0.5, 0.3), shade_bottom=0.80, shade_top=0.40, blur=1.2)
    out = f'{D}/ed/hero_m2.jpg'                                              # (old) chess scene on a dark chocolate stage
    if not os.path.exists(out):
        pw, ph = 1754, 2480; bg = Image.open(grad_img('choc', (0.20, 0.125, 0.09), (0.035, 0.028, 0.024), pw//2, ph//2, glow=0.16, gcol=(0.9, 0.55, 0.35), gx=0.5, gy=0.30)).resize((pw, ph), Image.BICUBIC).convert('RGBA')
        ch = Image.open(f'{D}/shops/chess2.png').convert('RGBA'); w_ = round(pw*1.42); ch = ch.resize((w_, round(w_*ch.height/ch.width)), Image.LANCZOS)
        a = np.array(ch).astype(float); ramp = np.clip((ch.height*0.97 - np.arange(ch.height))/(ch.height*0.20), 0, 1)[:, None]**1.2; a[..., 3] *= ramp
        ch = Image.fromarray(a.astype('uint8'), 'RGBA'); bg.alpha_composite(ch, (-(w_ - pw)//2 - 40, 86))
        a = np.array(bg.convert('RGB')).astype(float)/255; yy = np.linspace(0, 1, ph)[:, None, None]
        a *= 1 - 0.55*np.clip((0.07 - yy)/0.07, 0, 1); Image.fromarray((np.clip(a, 0, 1)*255).astype('uint8')).save(out, quality=90)
    return out
def kicker(sec): return ['ДЛЯ НЕЁ', 'ДЛЯ НЕГО', 'ДЛЯ НЕЁ И ДЛЯ НЕГО', 'ОСОБЫЙ ВЫБОР'][ORDER.index(sec)]   # v60: no section numbers
def opener(c, sec, items):
    c.drawImage(hero_bg(sec), 0, 0, W, H); topbar(c, WHITE, SOFT, (1, 1, 1))
    lines = SEC[sec]['title'].upper().split(); sz = fit_size(lines, XB, W - 2*ML, 132); lead = sz*0.90
    yb = H - 215.0; y0 = yb - lead*(len(lines)-1)
    txt(c, ML, y0 - sz*0.80, kicker(sec), B, 8, WHITE, cs=2.2)
    txt(c, MR, y0 - sz*0.80, 'ETIB PARFUM  ·  КОЛЛЕКЦИЯ', B, 8, SOFT, cs=2.2, align='r')
    for i, ln in enumerate(lines): txt(c, ML - sz*0.045, y0 + i*lead, ln, XB, sz, WHITE, cs=-0.03*sz)
    hline(c, ML, MR, yb + 34, (1, 1, 1), 0.6)
    para(c, ML, yb + 62, HERO[sec]['text'], R, 11.5, 300, 17.5, (0.93, 0.91, 0.89))
    n = str(len(items)); txt(c, MR, yb + 96, n, XB, 62, WHITE, cs=-2, align='r')
    txt(c, MR - tw_(n, XB, 62, -2) - 12, yb + 76, 'АРОМАТОВ', B, 8, WHITE, cs=2.2, align='r')
    txt(c, MR - tw_(n, XB, 62, -2) - 12, yb + 92, 'В РАЗДЕЛЕ', B, 8, SOFT, cs=2.2, align='r')
    rng = f"{items[0]['code']} — {items[-1]['code']}"; bw = tw_(rng, B, 9, 1.6) - 1.6 + 30
    button(c, ML, yb + 118, 'АРТИКУЛЫ  ' + rng, fill=WHITE, col=INK, sz=7.5, pad=15, h=25)
    c.showPage()

# ---------------------------------------------------------------- section endings
def heading(c, x, y, label, lines, sz, col=INK, lab=GREY, lead=None):
    txt(c, x, y, label, B, 6.6, lab, cs=1.8); y += sz*0.95 + 6
    for ln in lines: txt(c, x - sz*0.04, y, ln, XB, sz, col, cs=-0.03*sz); y += lead or sz*0.98
    return y - (lead or sz*0.98)
_shop_cutout0 = shop_cutout
def shop_cutout(name):
    if name == 'island6_cut': return f'{D}/shops/island6_cut.png'     # cut from the owner's photo by scripts/cut_island6.py
    return _shop_cutout0(name)
def island_frame(wpt, hpt):
    """Dark frame with the island shop (photo from the owner: base picture, front case taken from the fuller shot)."""
    out = f'{D}/ed/island_frame.jpg'
    if not os.path.exists(out):
        ph = Image.open(f'{D}/shops/island6.png').convert('RGB'); k = ph.height/(hpt*0.90)
        cw_, ch_ = round(wpt*k), round(hpt*k); cv = np.zeros((ch_, cw_, 3)) + 3.0
        x0, y0 = cw_ - ph.width, ch_ - ph.height; a = np.array(ph).astype(float)
        ramp = 60.0; yy = np.arange(ph.height)[:, None]; xx = np.arange(ph.width)[None, :]
        m = (np.clip(xx/ramp, 0, 1)*np.clip(yy/ramp, 0, 1))[..., None]
        cv[y0:, x0:] = cv[y0:, x0:]*(1 - m) + a*m
        Image.fromarray(np.clip(cv, 0, 255).astype('uint8')).save(out, quality=92)
    return out
def staged_vis(name, depth=0.24, op=0.85, tone=0.70):
    """v67: like staged(), but the mirror image is denser and a little darker, so the white island base and the
    gold bottles visibly reflect on the white page."""
    from scipy import ndimage as nd
    out = f'{D}/shops/stgvis_{name}_{int(depth*100)}_{int(op*100)}_{int(tone*100)}.png'
    if os.path.exists(out): return out
    im = Image.open(shop_cutout(name)).convert('RGBA'); a = np.array(im).astype(float); h, w, _ = a.shape
    al = a[..., 3] > 128; has = al.any(axis=0); yb = np.where(has, h - 1 - np.argmax(al[::-1], axis=0), 0); yb = nd.median_filter(yb, size=9)
    R = int(h*depth); refl = np.zeros((h + R, w, 4))
    for x in np.where(has)[0]:
        b = int(yb[x]); n = min(R, b)
        col = a[b-n+1:b+1, x][::-1].copy(); col[:, :3] *= tone; col[:, 3] *= op*(1 - np.arange(n)/R)**1.5; refl[b+1:b+1+n, x] = col
    sh = np.zeros((h + R, w)); band = max(2, int(h*0.035))
    for x in np.where(has)[0]:
        b = int(yb[x]); sh[b-band:b+int(band*0.6), x] = 1
    shi = Image.fromarray((sh*255).astype('uint8')).filter(ImageFilter.GaussianBlur(max(3, h*0.022))).point(lambda v: int(v*0.55))
    cv = Image.new('RGBA', (w, h + R), (0, 0, 0, 0))
    shadow = Image.new('RGBA', cv.size, (45, 35, 30, 0)); shadow.putalpha(shi); cv.alpha_composite(shadow)
    cv.alpha_composite(Image.fromarray(np.clip(refl, 0, 255).astype('uint8'), 'RGBA').filter(ImageFilter.GaussianBlur(0.8)))
    cv.alpha_composite(im, (0, 0)); cv = cv.crop(cv.getchannel('A').point(lambda v: 255 if v > 6 else 0).getbbox()); cv.save(out)
    return out
def end_women(c, sec, items):
    """4 cards (row of three + Z1): reading guide beside Z1, shop photo with an invitation below."""
    chrome(c, sec, items); cards(c, sec, items)
    x0, t, x1, b = cell_box(1, 1, 2)
    y = heading(c, x0, t + 8, 'СОВЕТ', ['КАК ВЫБРАТЬ СВОЙ АРОМАТ'], 25); hline(c, x0, x1, y + 16, INK, 0.6)
    cw = (x1 - x0 - 2*20)/3; y0 = y + 46
    for i, (head, body_) in enumerate([('ПОСЛУШАЙТЕ НА КОЖЕ', 'Нанесите каплю на запястье: на коже аромат звучит по-настоящему — так, как он будет звучать на вас.'),
                                       ('ДАЙТЕ ЕМУ РАСКРЫТЬСЯ', 'Уже через несколько минут аромат начнёт раскрываться: за свежими верхними нотами появится его сердце.'),
                                       ('ВЫБЕРИТЕ ДВА', 'Один свежий — на день, другой тёплый — на вечер. Так у вас всегда будет аромат под настроение.')]):
        x = x0 + i*(cw + 20); txt(c, x, y0, f'0{i+1}', XB, 20, cs=-0.6)
        yy = y0 + 22
        for ln in wrap(head, B, 7.2, cw, 1.4): txt(c, x, yy, ln, B, 7.2, cs=1.4); yy += 11
        para(c, x, yy + 9, body_, R, 9, cw - 2, 13.5, (0.2, 0.2, 0.2))
    X0, T, X1, Bm = cell_box(0, 2, 3, 2)
    fn = staged_vis('island6_cut', depth=0.24); iw, ih = Image.open(fn).size
    wI = 585.0; k = wI/iw; xI = W - 6 - wI; yI = T + 66
    c.saveState(); p_ = c.beginPath(); p_.rect(0, 34, W, H); c.clipPath(p_, stroke=0, fill=0)
    c.drawImage(fn, xI, H - yI - ih*k, wI, ih*k, mask='auto'); c.restoreState()
    tx = X0
    y = heading(c, tx, T + 30, 'ETIB PARFUM', ['ПОСЛУШАЙТЕ', 'АРОМАТ', 'ВЖИВУЮ'], 27)
    y = para(c, tx, y + 26, 'Любой аромат из этого каталога можно попробовать прямо сейчас. Консультант поможет сравнить ароматы и подобрать ваш.', R, 9.2, 196, 14, (0.2, 0.2, 0.2))
    button(c, tx, y + 12, 'СПРОСИТЕ КОНСУЛЬТАНТА')
    c.showPage()
def end_men(c, sec, items):
    """Single last card: statement beside it, the white shop edge to edge below."""
    chrome(c, sec, items); cards(c, sec, items)
    x0, t, x1, b = cell_box(1, 0, 2)
    y = heading(c, x0, t + 8, 'ETIB PARFUM', ['АРОМАТ —', 'ПОДПИСЬ,', 'КОТОРУЮ СТАВЯТ', 'БЕЗ СЛОВ'], 43, lead=44)
    hline(c, x0, x1, b - 30, INK, 0.6); button(c, x0, b - 21, 'ВЫБЕРИТЕ СВОЮ ПОДПИСЬ')
    fn = f'{D}/shops/white_fade_hi.png'; iw, ih = Image.open(fn).size; h_ = W*ih/iw; top_ = b + (H - 40 - b - h_)/2 + 10   # v73: 2x upscale
    c.drawImage(fn, 0, H - top_ - h_, W, h_, mask='auto')
    c.setFillColorRGB(1, 1, 1); c.rect(0, 0, W, 31, stroke=0, fill=1); footer(c)
    c.showPage()
def hands_glass(top_):
    """Hands with the bottle: the clear cap and the glassy top of the bottle let the page colour through
    (the cut-out was made on white, so its glass carried white). Only bright neutral pixels change: skin, nails,
    metal and highlights stay as they were."""
    out = f'{D}/ed/hands_glass_v20.png'
    if os.path.exists(out): return out
    im = Image.open(f'{D}/hands_cut_v2.png').convert('RGBA'); a = np.array(im).astype(float)/255; C, A = a[..., :3], a[..., 3]   # original textures (the v19 retouch looked plastic)
    ih, iw = A.shape; h_ = W*ih/iw; top_img = H + 34 - h_                    # page y (from the top) of the image's first row
    g = np.array(Image.open(grad_img('terra', (0.47, 0.215, 0.14), (0.10, 0.05, 0.04), 620, 360, glow=0.20, gcol=(0.7, 0.32, 0.2), gx=0.55, gy=0.45)).convert('RGB')).astype(float)/255
    yy = top_img + np.arange(ih)*h_/ih; xx = np.arange(iw)*W/iw                # page coordinates of every pixel
    gy = np.clip(((yy - top_)/(H - top_))*(g.shape[0]-1), 0, g.shape[0]-1).astype(int); gx = np.clip(xx/W*(g.shape[1]-1), 0, g.shape[1]-1).astype(int)
    BG = g[gy][:, gx]; BG[yy < top_] = 1.0                                   # above the terracotta field the page is white
    m = Image.new('L', (iw, ih), 0)
    ImageDraw.Draw(m).polygon([(1365, 610), (1745, 610), (1745, 935), (1365, 935)], fill=255)               # the glass cap only
    metal = Image.new('L', (iw, ih), 0); ImageDraw.Draw(metal).rectangle((1468, 716, 1566, 910), fill=255)
    ImageDraw.Draw(metal).rectangle((1405, 905, 1625, 970), fill=255)                                          # sprayer and collar keep their shine
    nail = Image.new('L', (iw, ih), 0); ImageDraw.Draw(nail).polygon([(1598, 596), (1702, 596), (1692, 690), (1662, 722), (1626, 731), (1598, 714)], fill=255)
    f = lambda im_, s_: nd.gaussian_filter(np.array(im_).astype(float)/255, s_)
    zone = f(m, 4)*(1 - np.clip(f(metal, 4)*1.8, 0, 1))*(1 - np.clip(f(nail, 2.5)*1.6, 0, 1))
    mn, mx = C.min(axis=2), C.max(axis=2)
    neutral = np.clip((0.10 - (mx - mn))/0.05, 0, 1)
    t = np.clip((mn - 0.45)/0.45, 0, 1); bright = t*t*(3 - 2*t)                  # smooth, no hard steps
    k = zone*neutral*bright*0.88*np.where(mn > 0.93, 0.35, 1.0)                 # clear like v8, but the facet glints stay bright and outline the cap
    glass = BG*C                                                               # clear glass: the page shows through, tinted by the glass
    o = C*(1 - k[..., None]) + glass*k[..., None]
    capz = f(m, 3)*(1 - np.clip(f(nail, 2.5)*1.6, 0, 1))                          # crisper facet edges on the cap
    bl = np.dstack([nd.gaussian_filter(o[..., i], 2.0) for i in range(3)])
    o = np.clip(o + (o - bl)*2.1*capz[..., None], 0, 1)
    sol = A > 0.5; rim = sol & ~nd.binary_erosion(sol, iterations=3)               # thin light rim along the cap's outline, like real glass edges
    rz = Image.new('L', (iw, ih), 0); dr = ImageDraw.Draw(rz); dr.rectangle((1340, 585, 1770, 945), fill=255)
    dr.polygon([(1575, 540), (1790, 540), (1790, 705), (1705, 718), (1652, 752), (1585, 748)], fill=0)       # keep the finger and nail as they are
    rim = nd.gaussian_filter(rim.astype(float), 1.0)*f(rz, 1.5)
    o = o*(1 - 0.55*rim[..., None]) + 0.55*rim[..., None]*np.array([0.97, 0.95, 0.93])
    Image.fromarray((np.dstack([np.clip(o, 0, 1), A])*255).astype('uint8'), 'RGBA').save(out)
    return out
def end_unisex(c, sec, items):
    """Two rows of cards; below, the hands with the bottle run edge to edge over a dark terracotta field."""
    chrome(c, sec, items); cards(c, sec, items)
    top_ = 706.0; c.drawImage(grad_img('terra_hi', (0.47, 0.215, 0.14), (0.10, 0.05, 0.04), 1860, 1080, glow=0.20, gcol=(0.7, 0.32, 0.2), gx=0.55, gy=0.45), 0, 0, W, H - top_)
    fn = hands_glass(top_); iw, ih = Image.open(fn).size; h_ = W*ih/iw      # owner's new picture: hands_cut_v2 (upscaled x2, colours matched to the previous one)
    c.drawImage(fn, 0, -34, W, h_, mask='auto')
    y = heading(c, ML, top_ + 44, 'ETIB PARFUM', ['ТВОЙ АРОМАТ —', 'ТВОЁ НАСТРОЕНИЕ'], 30, WHITE, SOFT)
    tx = 598.0
    y = para(c, tx, H - 150, 'Сегодня — лёгкий и свежий, завтра — тёплый и глубокий. Выбирайте не один аромат на все случаи, а свой на\u00a0каждый\u00a0день.', R, 9.5, MR - tx, 14.5, (0.95, 0.92, 0.90))
    button(c, tx, y + 8, 'ВЫБЕРИТЕ АРОМАТ ПОД НАСТРОЕНИЕ', fill=WHITE, col=INK)
    txt(c, MR, H - 16, FOOT, M, 5.6, (0.85, 0.80, 0.77), cs=1.5, align='r')
    c.showPage()
def end_premium(c, sec, items):
    """Ten cards: the two free cells of the last row carry a narrow dark frame and the closing line."""
    chrome(c, sec, items); cards(c, sec, items)
    x0, t, x1, b = cell_box(1, 3, 2)
    c.drawImage(toned(f'{D}/notes/amber.jpg', PW, PH, 'tile_amber', sat=0.62, tint=(0.95, 0.74, 0.62), gain=0.62, focus=(0.4, 0.5), dpi=300), x0, H - b, PW, PH)
    tx = x0 + PW + 26
    y = heading(c, tx, t + 14, 'ETIB PARFUM', ['АРОМАТ —', 'НЕВИДИМАЯ', 'ЧАСТЬ ОБРАЗА,', 'КОТОРУЮ ПОМНЯТ', 'ДОЛЬШЕ ВСЕГО'], 31, lead=32)
    hline(c, tx, x1, b - 30, INK, 0.6); button(c, tx, b - 21, 'ПОПРОБУЙТЕ ЛЮБОЙ АРОМАТ ПРЯМО СЕЙЧАС')
    c.showPage()

# ---------------------------------------------------------------- awards + poster spread
import cv2
def medals_staged(depth=0.22, op=0.26):   # v70: fainter reflection
    """v69: the medals over a mirror floor. The soft drop shadow baked into medals.png is removed; each column of the
    solid medal is mirrored from its own lowest point (a crisp reflection), fading out; a thin contact shadow."""
    out = f'{D}/awards/medals_staged77_{int(depth*100)}_{int(op*100)}.png'
    if not os.path.exists(out):
        im = Image.open(f'{D}/awards/medals_v77.png').convert('RGBA'); a = np.array(im).astype(float); h, w, _ = a.shape
        solid = a[..., 3] > 200
        from scipy import ndimage as nd
        solid = nd.binary_fill_holes(solid)
        a[..., 3] = np.where(solid, a[..., 3], 0)                                   # drop the baked blur shadow
        soft = cv2.GaussianBlur(solid.astype(np.float32), (0, 0), 1.0); a[..., 3] = np.maximum(a[..., 3]*solid, 0) + 0
        a[..., 3] = np.where(solid, 255, 0)*np.clip(soft*1.6, 0, 1)
        has = solid.any(axis=0); yb = np.where(has, h - 1 - np.argmax(solid[::-1], axis=0), 0)
        R = int(h*depth); cv = np.zeros((h + R, w, 4))
        for x in np.where(has)[0]:
            b = int(yb[x]); n = min(R, b + 1)
            col = a[b - n + 1:b + 1, x][::-1].copy(); col[:, :3] *= 0.85; col[:, 3] *= op*np.clip(1 - np.arange(n)/R, 0, 1)**1.5
            cv[b + 1:b + 1 + n, x] = col
        refl = Image.fromarray(np.clip(cv, 0, 255).astype('uint8'), 'RGBA')
        sh = np.zeros((h + R, w), np.float32)
        for x in np.where(has)[0]: sh[int(yb[x]) - 3:int(yb[x]) + 4, x] = 1
        sh = cv2.GaussianBlur(sh, (0, 0), 6)*0.55
        shadow = Image.new('RGBA', refl.size, (40, 14, 6, 0)); shadow.putalpha(Image.fromarray((np.clip(sh, 0, 1)*255).astype('uint8')))
        img = Image.new('RGBA', refl.size, (0, 0, 0, 0)); img.alpha_composite(shadow); img.alpha_composite(refl)
        img.alpha_composite(Image.fromarray(np.clip(a, 0, 255).astype('uint8'), 'RGBA'), (0, 0)); img.save(out)
    return out
def awards_page(c):
    c.drawImage(terra_bg(), 0, 0, W, H); topbar(c, WHITE, SOFT, (1, 1, 1))
    lines = ['ПОБЕДИТЕЛЬ', 'МЕЖДУНАРОДНЫХ', 'ПРЕМИЙ']; sz = fit_size(lines, XB, W - 2*ML, 110); y = 150.0
    txt(c, ML, y, 'ETIB PARFUM  ·  НАГРАДЫ', B, 8, SOFT, cs=2.2); y += sz*0.78 + 22
    for ln in lines: txt(c, ML - sz*0.045, y, ln, XB, sz, WHITE, cs=-0.03*sz); y += sz*1.00   # v73: more leading, the breve of Й no longer touches Н
    mw = W - 2*ML + 16; med = Image.open(f'{D}/awards/medals_v77.png'); mh = mw*med.height/med.width; mt = y - sz*1.00 + 62
    ms = medals_staged(); mh2 = mw*Image.open(ms).height/med.width            # v68: medals stand on a mirror floor
    c.drawImage(ms, ML - 8, H - mt - mh2, mw, mh2, mask='auto')
    data = [('2025', 'НОМЕР ОДИН', 'Бренд парфюмерии белорусского производства №\u00a01'),
            ('2025', 'НАРОДНЫЙ ВЫБОР', 'Магазин парфюмерной косметики'),
            ('2026', 'НАРОДНЫЙ ВЫБОР', 'Магазин парфюмерной косметики')]
    ty = mt + mh + 58; cw = (W - 2*ML - 2*24)/3
    for i, (yr, prize, nom) in enumerate(data):
        x = ML + i*(cw + 24); hline(c, x, x + cw, ty, (1, 1, 1), 0.6)
        txt(c, x, ty + 20, f'0{i+1}', B, 8, SOFT, cs=1.6); txt(c, x + cw, ty + 20, 'ПРЕМИЯ', B, 6.6, SOFT, cs=1.8, align='r')
        txt(c, x - 2, ty + 78, yr, XB, 56, WHITE, cs=-2)
        txt(c, x, ty + 104, prize, B, 11, (1.0, 0.86, 0.66), cs=2.4)
        txt(c, x, ty + 128, 'НОМИНАЦИЯ', B, 6.2, SOFT, cs=1.8); para(c, x, ty + 146, nom, R, 11, cw - 10, 16, (0.93, 0.91, 0.89))
    fy = ty + 208; hline(c, ML, MR, fy, (0.35, 0.33, 0.32))
    for i, (big_, cap) in enumerate([('3', 'международные награды'), ('№1', 'бренд парфюмерии белорусского производства'), ('2', 'года подряд — «Народный выбор»')]):
        x = ML + i*(cw + 24); txt(c, x - 2, fy + 74, big_, XB, 62, (1.0, 0.86, 0.66), cs=-2)
        para(c, x, fy + 100, cap.upper(), B, 7.2, cw - 30, 12, (0.93, 0.91, 0.89), cs=1.6)
    txt(c, ML, H - 16, 'ETIB PARFUM  ·  ПАРФЮМЕРИЯ БЕЛОРУССКОГО ПРОИЗВОДСТВА', M, 5.6, SOFT, cs=1.5); hline(c, ML, MR, H - 30, (0.35, 0.33, 0.32))
    c.showPage()
def poster_page(c):
    out = f'{D}/poster_wood_soft_v71.jpg'                                      # v71: owner's new photo, same clean-up and grade (scripts/soften_poster.py)
    im = Image.open(out); k = max(W/im.width, H/im.height); w_, h_ = im.width*k, im.height*k
    c.drawImage(out, (W - w_)/2, (H - h_)/2, w_, h_); c.showPage()

# ---------------------------------------------------------------- shops spread
def tile_photo(c, src, x, top, w_, h_, tag, **kw): c.drawImage(toned(src, w_, h_, tag, dpi=220, **kw), x, H - top - h_, w_, h_)
def shops_a(c):
    c.setFillColorRGB(1, 1, 1); c.rect(0, 0, W, H, stroke=0, fill=1); topbar(c)
    txt(c, ML, 62, 'ETIB PARFUM  ·  БЕЛАРУСЬ', B, 8, GREY, cs=2.2)
    sz = 104; txt(c, ML - sz*0.045, 150, 'НАШИ', XB, sz, cs=-0.03*sz); txt(c, ML - sz*0.045, 150 + sz*0.90, 'МАГАЗИНЫ', XB, sz, cs=-0.03*sz)
    y = para(c, 560, 262, 'Фирменные магазины и островки ETIB PARFUM — место, где каждый аромат из каталога можно послушать, сравнить и выбрать свой.', R, 9.5, MR - 560, 14.5, (0.2, 0.2, 0.2))
    g = 15.0; T0 = 300.0
    shop_tile(c, 'black', ML, T0, 513.5, 372, depth=0.10, base=0.87)
    shop_tile(c, 'white', 560, T0 + 52, MR - 560, 250); shop_tile(c, 'corner', 560, T0 + 52 + 250 + g, MR - 560, 250)
    shop_tile(c, 'glass', ML, T0 + 372 + g, 249.25, 250); shop_tile(c, 'island1', ML + 249.25 + g, T0 + 372 + g, 249.25, 250)
    tile_photo(c, f'{D}/poster_toned.jpg', 560, T0 + 52 + 2*(250 + g), MR - 560, H - 46 - (T0 + 52 + 2*(250 + g)), 'tile_poster', sat=0.9, tint=(1.0, 0.94, 0.88), gain=0.80, focus=(0.5, 0.42))
    t2 = T0 + 372 + 250 + 2*g; shop_tile(c, 's6_a3', ML, t2, 513.5, H - 46 - t2, pad=0.09, base=0.84)
    footer(c); c.showPage()
def shops_b(c):
    c.setFillColorRGB(1, 1, 1); c.rect(0, 0, W, H, stroke=0, fill=1); topbar(c)
    g = 15.0; cw = (MR - ML - 2*g)/3; T0 = 62.0
    shop_tile(c, 'island2', ML, T0, 2*cw + g, 330, base=0.86); tile_photo(c, f'{D}/notes/vanilla.jpg', ML + 2*(cw + g), T0, cw, 330, 'tile_vanilla', sat=0.6, tint=(0.98, 0.84, 0.72), gain=0.62)
    r2 = T0 + 330 + g
    for i, n in enumerate(('s5_5', 's5_7', 's6_b')): shop_tile(c, n, ML + i*(cw + g), r2, cw, 215, pad=0.10, base=0.86)
    r3 = r2 + 215 + g
    tile_photo(c, f'{D}/z1/flower.jpg', ML, r3, cw, 330, 'tile_flower', sat=0.85, tint=(1.05, 0.86, 0.74), gain=0.80, focus=(0.5, 0.3)); shop_tile(c, 'island5', ML + cw + g, r3, 2*cw + g, 330, base=0.84)
    r4 = r3 + 330 + g; hb = H - 46 - r4
    for i, n in enumerate(('s6_d', 's5_3')): shop_tile(c, n, ML + i*(cw + g), r4, cw, hb, pad=0.10, base=0.84)
    x = ML + 2*(cw + g); c.setFillColorRGB(*BLACK); c.rect(x, 46, cw, hb, stroke=0, fill=1)
    c.drawImage(f'{D}/logo_hi.png', x + 18, H - r4 - 18 - 44, 42, 44, mask='auto')
    txt(c, x + 18, r4 + hb - 62, 'ЖДЁМ ВАС', XB, 24, WHITE, cs=-0.7); txt(c, x + 18, r4 + hb - 38, 'В ETIB PARFUM', XB, 24, WHITE, cs=-0.7)
    txt(c, x + 18, r4 + hb - 18, 'ПАРФЮМЕРИЯ БЕЛОРУССКОГО ПРОИЗВОДСТВА', B, 5.4, SOFT, cs=1.2)
    footer(c); c.showPage()

# ---------------------------------------------------------------- build
SEC_PH = {ORDER[0]: ('z1/flower.jpg', dict(sat=0.85, tint=(1.05, 0.86, 0.74), gain=0.95, focus=(0.5, 0.2))),
          ORDER[1]: ('v20/cardamom.jpg', dict(sat=0.58, tint=(1.02, 0.80, 0.62), gain=0.70, focus=(0.5, 0.3))),
          ORDER[2]: ('notes/amber.jpg', dict(sat=0.72, tint=(0.98, 0.76, 0.62), gain=0.70, focus=(0.5, 0.3))),
          ORDER[3]: ('notes/vanilla.jpg', dict(sat=0.60, tint=(0.98, 0.84, 0.72), gain=0.66, focus=(0.5, 0.4)))}
def ink_logo(col, tag):
    """Brand logo recoloured (the original file is cream, for dark grounds)."""
    out = f'{D}/ed/logo_hi_{tag}.png'
    if not os.path.exists(out):
        lg = Image.open(f'{D}/logo_hi.png').convert('RGBA'); a_ = lg.getchannel('A')
        im = Image.new('RGBA', lg.size, tuple(int(v*255) for v in col) + (0,)); im.putalpha(a_); im.save(out)
    return out
COVER = dict(bg=(1, 1, 1), ink=INK, sub=GREY, line=INK)   # v41: white, like the inner pages
def cover_page(c, st=None):
    st = st or COVER; ink, sub, line = st['ink'], st['sub'], st['line']
    if st.get('img'): c.drawImage(st['img'], 0, 0, W, H)
    else: c.setFillColorRGB(*st['bg']); c.rect(0, 0, W, H, stroke=0, fill=1)
    topbar(c, ink, sub, line, right='')
    lines = ['ETIB', 'PARFUM']; sz = fit_size(lines, XB, W - 2*ML, 200); y = 92 + sz*0.80
    txt(c, ML, 78, 'КАТАЛОГ АРОМАТОВ', B, 8, sub, cs=2.2)
    for ln in lines: txt(c, ML - sz*0.045, y, ln, XB, sz, ink, cs=-0.03*sz); y += sz*0.90
    g = 12.0; fw = (W - 2*ML - 3*g)/4; ft = y - sz*0.90 + 52; fh = 470.0
    for i, sec in enumerate(ORDER):
        src, kw = SEC_PH[sec]; x = ML + i*(fw + g)
        c.drawImage(toned(f'{D}/{src}', fw, fh, f'cov_{i}', dpi=220, **kw), x, H - ft - fh, fw, fh)
        hline(c, x, x + fw, ft + fh + 16, line, 0.6)
        txt(c, x, ft + fh + 34, f'0{i+1}', B, 7.5, sub, cs=1.6); 
        txt(c, x, ft + fh + 56, SEC[sec]['title'].split()[0].upper(), XB, 15, ink, cs=-0.3)
    yb = H - 70                                                               # v58: no fragrance counts on the cover
    lg = f'{D}/logo_hi.png' if sum(ink) > 2.5 else ink_logo(ink, 'ink%d' % int(sum(ink)*100))
    lab_y = ft + fh + 56; free0, free1 = lab_y + 18, H - 30           # v61: logo centred and larger in the space under the section labels
    lh = min(118.0, (free1 - free0)*0.78); lw = lh*348/365; ly = (free0 + free1)/2 - lh/2
    c.drawImage(lg, W/2 - lw/2, H - ly - lh, lw, lh, mask='auto')
    c.showPage()
def intro_page(c, gap=0.0):
    c.setFillColorRGB(1, 1, 1); c.rect(0, 0, W, H, stroke=0, fill=1); topbar(c)
    pw = 318.0; c.drawImage(toned(f'{D}/notes/jasmine.jpg', pw, H - 46 - 62, 'intro_jasmine', sat=0.8, tint=(1.04, 0.90, 0.78), gain=0.86, focus=(0.5, 0.4), dpi=200), ML, 46, pw, H - 46 - 62)
    x = ML + pw + 34; tw = MR - x
    y = heading(c, x, 110, 'ETIB PARFUM  ·  О НАС', ['ДУХИ', 'НА МАСЛЯНОЙ', 'ОСНОВЕ'], 44, lead=44)
    y = para(c, x, y + 34, 'Вся наша продукция — духи на масляной основе. ETIB PARFUM — парфюмерия белорусского производства, ароматы создаются в Минске.', R, 10.4, tw, 16, (0.2, 0.2, 0.2))
    y = para(c, x, y + 8, 'Вы платите за сам аромат: мы не разрабатываем отдельный флакон для каждой позиции, не закладываем в цену имя бренда и не тратим огромные деньги на рекламу.', R, 10.4, tw, 16, (0.2, 0.2, 0.2))
    y += 18 + gap; hline(c, x, MR, y, INK, 0.6); y += 24
    txt(c, x, y, 'ИЗ ЧЕГО СОЗДАНЫ АРОМАТЫ', B, 6.6, GREY, cs=1.8); y += 20
    txt(c, x, y, 'Масла трёх европейских парфюмерных домов', B, 12.5, cs=-0.1); y += 12
    for i, (nm, country, yr) in enumerate([('MANE', 'Франция', '1871'), ('ARGEVILLE', 'Франция', '1932'), ('LUZI', 'Швейцария', '1926')]):
        y += 12 + gap*0.25; hline(c, x, MR, y); y += 30
        txt(c, x, y, f'0{i+1}', B, 7.5, GREY, cs=1.6); txt(c, x + 26, y + 1, nm, XB, 23, cs=-0.6)
        txt(c, MR, y - 9, country.upper(), B, 6.6, GREY, cs=1.8, align='r'); txt(c, MR, y + 3, f'основан в {yr}', XB, 11, align='r')
    y += 14 + gap*0.25; hline(c, x, MR, y); y += 34 + gap
    txt(c, x, y, 'ДВА ВИДА АРОМАТОВ', B, 6.6, GREY, cs=1.8); y += 20
    txt(c, x, y, 'Клубные и селективные ароматы', B, 12.5, cs=-0.1); y += 26
    c1 = x + 96; c2 = c1 + (MR - c1)/2 + 6; cw = (MR - c1)/2 - 12
    txt(c, c1, y, 'КЛУБНЫЕ', XB, 11, cs=0.2); txt(c, c2, y, 'СЕЛЕКТИВНЫЕ', XB, 11, cs=0.2); y += 9; hline(c, x, MR, y, INK, 0.6)
    for k_, a_, b_ in [('МАСЛА', '20–30%', 'свыше 40%'), ('НА КОЖЕ', 'около 12 часов', 'около суток'), ('НА ОДЕЖДЕ', 'около суток', '3–4 дня'),
                       ('ВДОХНОВЕНИЕ', 'Chanel, Dior, Versace, Armani и другие', 'Byredo, Tom Ford, Creed, Kilian, MFK и другие')]:
        y += 19; txt(c, x, y, k_, B, 6.2, GREY, cs=1.4)
        ya = para(c, c1, y, a_, R, 9.4, cw, 13); yb2 = para(c, c2, y, b_, R, 9.4, cw, 13); y = max(ya, yb2) - 13 + 8; hline(c, x, MR, y)
    y = para(c, x, y + 22, 'Клубные — ароматы по мотивам известных парфюмов модных домов: узнаваемые и универсальные, на каждый день.', R, 9.4, tw, 14, (0.2, 0.2, 0.2))
    y = para(c, x, y + 6, 'Селективные — ароматы по мотивам нишевой парфюмерии: сложные композиции из редких компонентов с ярким характером и высокой стойкостью.', R, 9.4, tw, 14, (0.2, 0.2, 0.2))
    footer(c); c.showPage(); return y
def back_page(c):
    ink, sub, line = COVER['ink'], COVER['sub'], COVER['line']                 # same white as the front cover
    c.setFillColorRGB(*COVER['bg']); c.rect(0, 0, W, H, stroke=0, fill=1)
    lw = 250.0; lh = lw*365/348; top = 215.0; c.drawImage(ink_logo(ink, 'ink%d' % int(sum(ink)*100)), W/2 - lw/2, H - top - lh, lw, lh, mask='auto')   # v66: logo and type larger still
    txt(c, W/2, top + lh + 72, 'ETIB PARFUM', M, 44, ink, cs=17, align='c')
    hline(c, W/2 - 210, W/2 + 210, top + lh + 112, line, 0.8)
    txt(c, W/2, top + lh + 156, 'ПАРФЮМЕРИЯ БЕЛОРУССКОГО ПРОИЗВОДСТВА', B, 12.5, sub, cs=3.0, align='c')
    txt(c, W/2, top + lh + 186, 'ПОБЕДИТЕЛЬ МЕЖДУНАРОДНЫХ ПРЕМИЙ  ·  2025  ·  2026', B, 12.5, sub, cs=3.0, align='c')
    t_ = 'СПАСИБО, ЧТО ВЫБИРАЕТЕ НАС'; bw = tw_(t_, B, 11, 1.6) - 1.6 + 48; button(c, W/2 - bw/2, top + lh + 232, t_, fill=ink, col=COVER['bg'], sz=11, pad=24, h=38)
    hline(c, ML, MR, H - 30, line, 0.4); txt(c, W/2, H - 16, FOOT, M, 5.6, sub, cs=1.5, align='c')
    c.showPage()
ENDS = {ORDER[0]: end_women, ORDER[1]: end_men, ORDER[2]: end_unisex, ORDER[3]: end_premium}
tmp = f'{D}/ed_cards.pdf'; c = canvas.Canvas(tmp, pagesize=(W, H), pageCompression=1); c.setTitle('ETIB PARFUM — каталог ароматов'); n_pages = 0
cover_page(c)
_dummy = canvas.Canvas(io.BytesIO(), pagesize=(W, H)); _end = intro_page(_dummy)
intro_page(c, gap=min(64.0, max(0.0, (H - 64 - _end)/2.75))); n_pages += 2
for sec in ORDER:
    items = section(sec); pages = [items[i:i+12] for i in range(0, len(items), 12)]; print(sec, len(items), 'cards,', len(pages), 'pages')
    opener(c, sec, items); n_pages += 1
    for i, pg in enumerate(pages):
        if i == len(pages) - 1 and len(pg) < 12: ENDS[sec](c, sec, pg)
        else: chrome(c, sec, pg); cards(c, sec, pg); c.showPage()
        n_pages += 1
    if sec == ORDER[0]: awards_page(c); poster_page(c); n_pages += 2
# the 'Наши магазины' spread was removed in v2 at the owner's request
back_page(c); n_pages += 1
c.save()
print('shifted >2pt:', [x for x in SHIFTS if abs(x[2]) > 2])
w = pypdf.PdfWriter(clone_from=tmp)
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
w.write(OUT_REAL)
print('pages', n_pages, os.path.getsize(OUT_REAL)//1024, 'KB')
