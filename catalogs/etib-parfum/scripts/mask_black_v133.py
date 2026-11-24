"""v133: AND the column-wise top edge (each column starts at its own topmost highlight), so the dip of the shoulders
beside the cap is not filled with backdrop.
v132: silhouette of a black bottle on pure black from per-row extents of its rim highlights (no morphological closing,
so no backdrop is bridged in beside the cap or at the bottom corners). Rows from the cap top to the foot.
Usage: mask_black_v132.py <photo> <foot row> <out.png>"""
import sys, numpy as np, cv2
from PIL import Image
from scipy import ndimage as nd
src, foot, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
im = Image.open(src).convert('RGB'); L = nd.median_filter(np.array(im).astype(int).max(2), 3); h, w = L.shape
rows = [y for y in range(foot) if (L[y] > 7).any()]; Y = np.arange(rows[0], foot)
lx = np.array([np.where(L[y] > 7)[0].min() if (L[y] > 7).any() else np.nan for y in Y], float)
rx = np.array([np.where(L[y] > 7)[0].max() + 1 if (L[y] > 7).any() else np.nan for y in Y], float)
ok = ~np.isnan(lx); lx = np.interp(Y, Y[ok], lx[ok]); rx = np.interp(Y, Y[ok], rx[ok])
lx = nd.median_filter(lx, 7); rx = nd.median_filter(rx, 7)
poly = np.r_[np.c_[lx, Y], np.c_[rx, Y][::-1]]
m = np.zeros((h, w), np.uint8); cv2.fillPoly(m, [np.round(poly).astype(np.int32)], 255)
top = np.array([np.argmax(L[:foot, x] > 60) if (L[:foot, x] > 60).any() else foot for x in range(w)], float)   # the rim highlight itself
top = nd.median_filter(top, 9)
cap = (L[:foot] > 60).any(0); cx = np.where(top < top.min() + 40)[0]          # cap columns: their top is the cap's top ellipse
c0, c1 = cx.min() + 4, cx.max() - 4; top[c0:c1] = nd.minimum_filter1d(top, 41)[c0:c1]   # no slit where the cap is dark
top = nd.gaussian_filter1d(top, 1.5)
colm = np.arange(h)[:, None] >= top[None, :] - 0.5
m = np.where(colm, m, 0).astype(np.uint8)
o = im.convert('RGBA'); o.putalpha(Image.fromarray(m)); o.save(out); print(out, (m > 0).sum())
