import sys, os
SRC_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build_v47.py')
code = open(SRC_SCRIPT).read(); code = code[:code.index('ORDER = list(SEC)')]
OUT_REAL = sys.argv[4]
exec(compile(code, SRC_SCRIPT, 'exec'))
for f in ('Montserrat-ExtraBold', 'Montserrat-Bold'): pdfmetrics.registerFont(TTFont(f, f'{FONTS}/{f}.ttf'))
XB, B = 'Montserrat-ExtraBold', 'Montserrat-Bold'
import numpy as np
INK = (0.07, 0.07, 0.07); GREY = (0.42, 0.42, 0.42)
def panel_img():
    out = f'{D}/demo_panel.jpg'
    if not os.path.exists(out):
        hh, ww = 765, 354; yy, xx = np.mgrid[0:hh, 0:ww]
        a = np.array([0.44, 0.20, 0.13]); b = np.array([0.13, 0.065, 0.05])          # terracotta -> espresso
        t = np.clip(((xx/ww)*0.45 + (yy/hh)*0.75), 0, 1)[..., None]
        glow = np.exp(-(((xx-ww*0.35)/(ww*0.6))**2 + ((yy-hh*0.55)/(hh*0.45))**2))[..., None]*0.22
        rgb = np.clip(a*(1-t) + b*t + glow*np.array([0.6, 0.3, 0.2]), 0, 1)
        Image.fromarray((rgb*255).astype('uint8')).save(out, quality=92)
    return out
def txt(c, x, y, s, f, sz, col=INK, cs=0):
    t = c.beginText(x, H-y); t.setFont(f, sz); t.setFillColorRGB(*col); t.setCharSpace(cs); t.textOut(s); t.setCharSpace(0); c.drawText(t)
def wrap(text, f, sz, width, cs=0):
    out, cur = [], ''
    for w_ in text.split(' '):
        t = (cur + ' ' + w_).strip()
        if sw(t, f, sz) + cs*len(t) <= width or not cur: cur = t
        else: out.append(cur); cur = w_
    return out + ([cur] if cur else [])
def card2(c, it, gx, gt):
    x0, top = gx + 15.5, gt + 14.5; PW = 118.0
    c.drawImage(panel_img(), x0, H - top - 255, PW, 255)
    p, bx, by, bw_, bh = it['img']; dx = (x0 + PW/2) - (gx + 76)
    c.drawImage(p, gx + bx + dx, H - (gt + by + bh) + 6, bw_, bh, mask='auto')
    txt(c, x0 + 12, top + 28, it['code'], XB, 19, (1, 1, 1), cs=-0.4)
    tx = x0 + PW + 14; tw = 250 - PW - 16; y = top + 13
    for ln in wrap(it['name'], XB, 9.6, tw)[:3]: txt(c, tx, y + 7, ln, XB, 9.6, cs=-0.1); y += 11.6
    y += 1; txt(c, tx, y + 6, it['ru'][:34], R, 6.3, GREY); y += 15
    pos = SCALE.get(it['type'], 0.5)                                                   # fresh <-> sweet: one thin line
    txt(c, tx, y + 2, 'СВЕЖИЙ', M, 4.8, GREY, cs=0.8); l0 = tx + 31; l1 = tx + tw - 36
    c.setStrokeColorRGB(*INK); c.setLineWidth(0.5); c.line(l0, H - y, l1, H - y)
    c.setFillColorRGB(*INK); c.circle(l0 + (l1-l0)*pos, H - y, 2.6, stroke=0, fill=1)
    txt(c, l1 + 5, y + 2, 'СЛАДКИЙ', M, 4.8, GREY, cs=0.8); y += 13
    tags = [t for t in it['tags'] if t not in DROP]
    for ln in wrap('  /  '.join(t.upper() for t in tags), SB, 5.2, tw - 4, cs=0.9)[:2]: txt(c, tx, y + 2, ln, SB, 5.2, cs=0.9); y += 8.5
    y += 5; c.setStrokeColorRGB(0.82, 0.82, 0.82); c.setLineWidth(0.4); c.line(tx, H - y, tx + tw, H - y); y += 6
    fs = 7.2
    while True:
        blocks = [(h, wrap_notes(t, fs, tw)) for h, t in it['notes']]
        need = sum(10.5 + len(b)*fs*1.22 for _, b in blocks) + 5*(len(blocks)-1)
        if need <= (top + 255) - y - 2 or fs <= 5.8: break
        fs -= 0.2
    for i, (h, b) in enumerate(blocks):
        txt(c, tx, y + 6, f'0{i+1}', XB, 5.4); txt(c, tx + 12, y + 6, h, SB, 5.2, GREY, cs=0.9); y += 10.5
        for ln in b: txt(c, tx, y + fs*0.72, ln, R, fs); y += fs*1.22
        y += 5
def page2(c, sec, items, idx):
    c.setFillColorRGB(1, 1, 1); c.rect(0, 0, W, H, stroke=0, fill=1)
    txt(c, 31.5, 28, 'ETIB PARFUM', M, 10, cs=5.2); t_ = 'КАТАЛОГ АРОМАТОВ  ·  2026'; txt(c, W - 31.5 - sw(t_, M, 6) - 1.6*len(t_), 27, t_, M, 6, GREY, cs=1.6)
    c.setStrokeColorRGB(*INK); c.setLineWidth(0.6); c.line(31.5, H - 38, W - 31.5, H - 38)
    txt(c, 31.5, 54, f'РАЗДЕЛ 0{idx}', B, 6, cs=1.4)
    txt(c, 30, 82, SEC[sec]['title'].upper(), XB, 30, cs=-0.9)
    rng = f"{items[0]['code']} — {items[-1]['code']}"; txt(c, W - 31.5 - sw(rng, XB, 13), 81, rng, XB, 13)
    for i, it in enumerate(items): card2(c, it, XS[i % 3], YS[i//3] + 6)
    c.setStrokeColorRGB(0.82, 0.82, 0.82); c.setLineWidth(0.4); c.line(31.5, 30, W - 31.5, 30)
    s_ = 'ВСЕ ФЛАКОНЫ АРОМАТОВ ИЗГОТОВЛЕНЫ В ФИРМЕННОМ СТИЛЕ ETIB PARFUM'; txt(c, 31.5, H - 16, s_, M, 5.6, GREY, cs=1.5)
    c.showPage()
c = canvas.Canvas(OUT_REAL, pagesize=(W, H), pageCompression=1)
page2(c, 'ЖЕНСКИЕ АРОМАТЫ', section('ЖЕНСКИЕ АРОМАТЫ')[:12], 1)
page2(c, 'МУЖСКИЕ АРОМАТЫ', section('МУЖСКИЕ АРОМАТЫ')[:12], 2)
c.save(); print('ok')
