"""Photos for the staff website (etibparfum-catalog): each fragrance's bottle on the catalogue's dark warm-graphite panel,
3:4 portrait, same cut-outs, colour work, reflections and common base line as catalogue v76 (was v50). Also writes the note pyramids.
Usage: python3 site_card_photos.py <copy of assets/data> <assets/fonts> <out dir>"""
import sys, os, json
here = os.path.dirname(os.path.abspath(__file__))
D_ARG, FONTS_ARG, OUTDIR = sys.argv[1:4]
src = open(os.path.join(here, 'build_editorial_v134.py'), encoding='utf-8').read()
src = src[:src.index("tmp = f'{D}/ed_cards.pdf'")]
sys.argv = [os.path.join(here, 'build_editorial_v134.py'), D_ARG, FONTS_ARG, 'none', '/dev/null']
__file__ = sys.argv[0]
exec(compile(src, sys.argv[0], 'exec'))
from reportlab.pdfgen import canvas as _cv
W2, H2 = 180.0, 240.0
os.makedirs(OUTDIR, exist_ok=True)
pdf = f'{OUTDIR}/panels.pdf'; c2 = _cv.Canvas(pdf, pagesize=(W2, H2)); order = []
for sec in ORDER:
    for it in section(sec):
        c2.drawImage(panel_img(), 0, 0, W2, H2)
        p, bx, by, bw_, bh = it['img']; k = min(1.5, 140.0/bw_, 196.0/bh); bw2, bh2 = bw_*k, bh*k
        pb = prep_bottle(p, it['code']); off = 0.0 if it['code'] in WHOLE_SHAPE else body_offset(pb)*bw2
        fr = base_frac(pb); base_y = H2 - 34
        c2.drawImage(pb, W2/2 - bw2/2 - off, H2 - (base_y + bh2*(1 - fr)), bw2, bh2, mask='auto')
        c2.showPage()
        order.append(dict(code=it['code'], sec=sec[:3], name=it['name'], ru=it.get('ru', ''), notes=[list(n) for n in it['notes']], tags=it.get('tags', []), pos=it.get('pos')))
c2.save()
json.dump(order, open(f'{OUTDIR}/items.json', 'w'), ensure_ascii=False, indent=1)
print(len(order))
