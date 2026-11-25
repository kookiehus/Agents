"""Transparent bottle cut-outs for the «новинки»-style site cards (same cut-outs and colour work as the catalogue).
Usage: python3 site_bottle_cutouts.py <copy of assets/data> <assets/fonts> <out dir>   -> <out>/<SEC>_<code>.webp + list.json"""
import sys, os, json
here = os.path.dirname(os.path.abspath(__file__))
D_ARG, FONTS_ARG, OUTDIR = sys.argv[1:4]
src = open(os.path.join(here, 'build_editorial_v147.py'), encoding='utf-8').read()
src = src[:src.index("tmp = f'{D}/ed_cards.pdf'")]
sys.argv = [os.path.join(here, 'build_editorial_v147.py'), D_ARG, FONTS_ARG, 'none', '/dev/null']
__file__ = sys.argv[0]
exec(compile(src, sys.argv[0], 'exec'))
from PIL import Image as _I
os.makedirs(OUTDIR, exist_ok=True); done = []
for sec in ORDER:
    for it in section(sec):
        pb = prep_bottle(it['img'][0], it['code'])
        im = _I.open(pb).convert('RGBA'); im = im.crop((0, 0, im.width, round(im.height * base_frac(pb))))   # no reflection
        bb = im.getchannel('A').point(lambda v: 255 if v > 8 else 0).getbbox()
        im = im.crop(bb); k = 640 / im.height; im = im.resize((max(1, round(im.width * k)), 640), _I.LANCZOS)
        name = f"{sec[:3]}_{it['code']}.webp"; im.save(f'{OUTDIR}/{name}', 'WEBP', quality=82, method=6)
        done.append(dict(sec=sec[:3], code=it['code'], file=name, w=im.width, h=im.height))
json.dump(done, open(f'{OUTDIR}/list.json', 'w'), ensure_ascii=False)
print(len(done))
