"""v111: owner's photo for J5 Jean Paul Gaultier Scandal (studio shot on light grey).
Legs = rembg cut-out above the cap ring, lightly smoothed. Cap ring, collar and glass = per-row extents of the cut-out,
smoothed, straight collar and body sides replaced by fitted lines (body symmetric), drawn as a polygon at 4x.
Edge colours from 3 px inside, light contrast and sharpening.
Usage: prepare_bottles_v111_j5.py <J5.jpg> <rembg png> <out dir>"""
import sys, os, numpy as np, cv2
from PIL import Image, ImageFilter, ImageEnhance
from scipy import ndimage as nd
SRC, CUT, OUT = sys.argv[1:4]; os.makedirs(OUT, exist_ok=True); K = 4; YC = 424
rgb = np.array(Image.open(SRC).convert('RGB')).astype(np.float32)/255; h, w = rgb.shape[:2]
A = np.array(Image.open(CUT))[..., 3] > 128
lab, n = nd.label(A); c = np.bincount(lab.ravel()); c[0] = 0; A = nd.binary_fill_holes(lab == np.argmax(c))
Y = np.arange(YC, np.where(A.any(1))[0].max() + 1)
lx = np.array([np.where(A[y])[0].min() for y in Y], float); rx = np.array([np.where(A[y])[0].max() + 1 for y in Y], float)
lx = nd.gaussian_filter1d(nd.median_filter(lx, 5), 1.0); rx = nd.gaussian_filter1d(nd.median_filter(rx, 5), 1.0)
sel = (Y >= 456) & (Y <= 516)                                         # collar: straight
for arr in (lx, rx): arr[sel] = np.polyval(np.polyfit(Y[sel], arr[sel], 1), Y[sel])
sel = (Y >= 660) & (Y <= 935)                                         # body: straight, symmetric
cx = np.median((lx[sel] + rx[sel])/2); hw = np.median((rx[sel] - lx[sel])/2) - 1.5
lx[sel] = cx - hw; rx[sel] = cx + hw
poly = np.r_[np.c_[lx, Y], np.c_[rx, Y][::-1]]
big = np.zeros((h*K, w*K), np.uint8); cv2.fillPoly(big, [np.round(poly*K).astype(np.int32)], 255)
a = cv2.resize(big, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32)/255
legs = A.copy(); legs[YC + 2:] = False
lg = cv2.GaussianBlur(legs.astype(np.float32), (0, 0), 0.9); lg = np.clip((lg - 0.5)*2.4 + 0.5, 0, 1)
a = np.maximum(a, lg)
inner = cv2.erode((a > 0.99).astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
inner[:YC] = legs[:YC] & cv2.erode(legs.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)[:YC]
gi = nd.distance_transform_edt(~inner, return_distances=False, return_indices=True)
rgb = np.where(((a > 0.01) & ~inner)[..., None], rgb[gi[0], gi[1]], rgb)
yy, xx = np.where(a > 0.02); Y0, Y1, X0, X1 = yy.min(), yy.max() + 1, xx.min(), xx.max() + 1
img = Image.fromarray((np.dstack([np.clip(rgb, 0, 1), np.clip(a, 0, 1)])[Y0:Y1, X0:X1]*255).astype(np.uint8), 'RGBA')
k = 900/img.height; img = img.resize((round(img.width*k), 900), Image.LANCZOS)
c3 = ImageEnhance.Color(img.convert('RGB')).enhance(1.08)
c3 = ImageEnhance.Contrast(c3).enhance(1.08).filter(ImageFilter.UnsharpMask(1.2, 40, 2))
Image.merge('RGBA', (*c3.split(), img.getchannel('A'))).save(f'{OUT}/J5_ЖЕН.png'); print('J5_ЖЕН.png', img.size)
