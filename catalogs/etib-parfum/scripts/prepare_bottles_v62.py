"""v62: T20 Tiziana Terenzi Kirke from the owner's photo (white background).
Exact geometry: round black cap with straight sides and softly rounded corners, straight gold neck ring, cylindrical
gold body with straight sides (the rembg outline is kept only for the elliptical shoulder and base). Same edge
clean-up and levels as prepare_bottles_v49.py.
Usage: prepare_bottles_v62.py <uploads dir with T20.jpg> <out dir>"""
import sys, os
here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, 'prepare_bottles_v49.py'), encoding='utf-8').read()
exec(src[:src.index('# D24 Dior Homme Sport')])          # helpers: load, fit, box, smooth_part, finish ...

rgb, cut = load('T20'); h, w = cut.shape
cap = box(h, w, fit(cut, range(90, 250, 4), 'l'), fit(cut, range(90, 250, 4), 'r'), 60.5, 267.0, 10)
neck = box(h, w, fit(cut, range(272, 304, 2), 'l'), fit(cut, range(272, 304, 2), 'r'), 264.0, 312.0, 1)
pl, pr = fit(cut, range(360, 620, 4), 'l'), fit(cut, range(360, 620, 4), 'r')
sides = box(h, w, pl, pr, 300.0, 660.0, 0)
body = np.minimum(smooth_part(cut, 306, 660, 1.6), sides)
a = np.maximum(np.maximum(cap, neck), body)
own = (cut > 0.6) & (a > 0.5); ni = nd.distance_transform_edt(~own, return_distances=False, return_indices=True)
rgb = np.where(((a > 0.02) & ~own)[..., None], rgb[ni[0], ni[1]], rgb)
finish(rgb, a, 'T20_ПРЕ.png', rim=0.18)   # thin warm-grey rim: the black cap stands off the dark panel
