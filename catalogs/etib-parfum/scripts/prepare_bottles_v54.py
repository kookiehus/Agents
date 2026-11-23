"""v54: the owner's new ETIB PARFUM bottle (white sparkling glass, clear square cap) for the house-bottle cards
(B18, E2, E20, S7). Photo on black: rembg cut-out, holes filled, smooth outline, reflection under the base cut off.
Same edge clean-up and levels as prepare_bottles_v49.py.
Usage: prepare_bottles_v54.py <uploads dir with ETIB.jpg> <out dir>"""
import sys, os
here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, 'prepare_bottles_v49.py'), encoding='utf-8').read()
exec(src[:src.index('# D24 Dior Homme Sport')])          # helpers: load, fit, box, smooth_part, finish ...

rgb, cut = load('ETIB'); h, w = cut.shape
lum = rgb[:, w//3:2*w//3].mean(axis=(1, 2))
ybot = 1200 + int(np.argmin(lum[1200:1400]))              # dark gap between the base and its reflection
cut[ybot - 1:] = 0
m = nd.binary_fill_holes(cut > 0.35); m = nd.binary_opening(m, iterations=2)
a = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.4); a = np.clip((a - 0.5)*2.2 + 0.5, 0, 1); a[ybot - 1:] = 0
own = (cut > 0.6) & (a > 0.5); ni = nd.distance_transform_edt(~own, return_distances=False, return_indices=True)
rgb = np.where(((a > 0.02) & ~own)[..., None], rgb[ni[0], ni[1]], rgb)
finish(rgb, a, 'ETIB_white.png', lift=0.97)
