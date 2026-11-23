"""v64: C27 Carolina Herrera CH Hearts (limited edition) from the owner's photo (dark background with a reflection).
Cut just under the glass base (the photo's own reflection starts right below it), holes filled, smooth outline,
cap kept straight-sided (fitted lines). Same edge clean-up and levels as prepare_bottles_v49.py.
Usage: prepare_bottles_v64.py <uploads dir with C27.jpg> <out dir>"""
import sys, os
here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, 'prepare_bottles_v49.py'), encoding='utf-8').read()
exec(src[:src.index('# D24 Dior Homme Sport')])          # helpers: load, fit, box, smooth_part, finish ...

rgb, cut = load('C27'); h, w = cut.shape
m = cut > 0.5; wd = np.array([np.ptp(np.where(r)[0]) if r.any() else 0 for r in m])
ybot = 790 + int(np.argmax(wd[790:840] < wd[790] - 12))     # first row where the base narrows into the reflection
cut[ybot:] = 0
mm = nd.binary_fill_holes(cut > 0.4); mm = nd.binary_opening(mm, iterations=2)
a = cv2.GaussianBlur(mm.astype(np.float32), (0, 0), 1.5); a = np.clip((a - 0.5)*2.2 + 0.5, 0, 1); a[ybot:] = 0
capbox = box(h, w, fit(cut, range(260, 400, 4), 'l'), fit(cut, range(260, 400, 4), 'r'), 200.0, 470.0, 0)
ys_ = np.arange(h)[:, None]; capzone = (ys_ >= 244) & (ys_ < 415)
a = np.where(capzone, np.minimum(a, capbox), a)
own = (cut > 0.6) & (a > 0.5); ni = nd.distance_transform_edt(~own, return_distances=False, return_indices=True)
rgb = np.where(((a > 0.02) & ~own)[..., None], rgb[ni[0], ni[1]], rgb)
finish(rgb, a, 'C27_ЖЕН.png'); print('cut at', ybot)
