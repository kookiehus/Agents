"""v50: G10 Giorgio Armani Si from the owner's photo (white background).
Body = straight-sided glass block fitted to the cut-out (anti-aliased, softly rounded bottom corners); cap, gold collar
and the bevelled shoulders kept from the cut-out (smoothed). Same edge clean-up and levels as prepare_bottles_v49.py.
Usage: prepare_bottles_v50.py <uploads dir> <out dir>"""
import sys, os
here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, 'prepare_bottles_v49.py'), encoding='utf-8').read()
UP, OUT = sys.argv[1:3]
exec(src[:src.index('# D24 Dior Homme Sport')])          # helpers: load, fit, box, smooth_part, finish ...
rgb, cut = load('G10'); h, w = cut.shape
pl, pr = fit(cut, range(380, 920, 4), 'l'), fit(cut, range(380, 920, 4), 'r')
body = box(h, w, pl, pr, 346.0, 952.5, 7)
top = smooth_part(cut, 30, 350, 1.3)
a = np.maximum(body, top)
own = (cut > 0.6) & (a > 0.5); ni = nd.distance_transform_edt(~own, return_distances=False, return_indices=True)
rgb = np.where(((a > 0.02) & ~own)[..., None], rgb[ni[0], ni[1]], rgb)
finish(rgb, a, 'G10_ЖЕН.png', lift=0.98)
