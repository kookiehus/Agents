"""v132: silhouette of a black bottle on pure black from per-row extents of its rim highlights (no morphological closing,
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
o = im.convert('RGBA'); o.putalpha(Image.fromarray(m)); o.save(out); print(out, (m > 0).sum())
