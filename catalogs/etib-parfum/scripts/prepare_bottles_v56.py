"""v56: the owner's new black ETIB PARFUM bottle (black speckled glass, silver logo, clear square cap) for the black
house-bottle cards (E3, E4). Photo on black: rembg cut-out, holes filled, smooth outline, cut just under the bright
bottom edge (the reflection starts right below it); thin even warm-grey rim so the black glass stands off the dark panel.
Same edge clean-up and levels as prepare_bottles_v49.py.
Usage: prepare_bottles_v56.py <uploads dir with ETIBB.jpg> <out dir>"""
import sys, os
here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, 'prepare_bottles_v49.py'), encoding='utf-8').read()
exec(src[:src.index('# D24 Dior Homme Sport')])          # helpers: load, fit, box, smooth_part, finish ...

rgb, cut = load('ETIBB'); h, w = cut.shape
lum = rgb[:, w//3:2*w//3].mean(axis=(1, 2))
yedge = 1200 + int(np.argmax(lum[1200:1340]))             # bright line along the bottom edge of the glass
ybot = yedge + 2
cut[ybot:] = 0
m = nd.binary_fill_holes(cut > 0.35); m = nd.binary_opening(m, iterations=2)
a = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.4); a = np.clip((a - 0.5)*2.2 + 0.5, 0, 1); a[ybot:] = 0
own = (cut > 0.6) & (a > 0.5); ni = nd.distance_transform_edt(~own, return_distances=False, return_indices=True)
rgb = np.where(((a > 0.02) & ~own)[..., None], rgb[ni[0], ni[1]], rgb)
finish(rgb, a, 'ETIB_black.png', rim=0.22, lift=1.0)
