"""v108: owner's photo for L10 Louis Vuitton Afternoon Swim (bottle lying diagonally on a plate, shot from above).
Rotated upright (-31.7 deg, the principal axis of the rembg cut-out), outline = per-row extents of the cut-out,
smoothed, with the straight body sides replaced by fitted lines, drawn as a polygon at 4x (anti-aliased).
Edge colours from 2 px inside; gold flakes seen through the inner column softened.
Usage: prepare_bottles_v108_l10.py <L10.jpg> <rembg png> <out dir>"""
import sys, os, numpy as np, cv2
from PIL import Image, ImageFilter, ImageEnhance
from scipy import ndimage as nd
SRC, CUT, OUT = sys.argv[1:4]; os.makedirs(OUT, exist_ok=True); ANG = -31.7; K = 4
im = Image.open(SRC).convert('RGB'); cut = np.array(Image.open(CUT))[..., 3] > 128
lab, n = nd.label(cut); c = np.bincount(lab.ravel()); c[0] = 0; m = nd.binary_fill_holes(lab == np.argmax(c))
rgb = np.array(im.rotate(ANG, Image.BICUBIC, expand=True, fillcolor=(255, 255, 255))).astype(np.float32)/255
A = np.array(Image.fromarray((m*255).astype(np.uint8)).rotate(ANG, Image.BICUBIC, expand=True)) > 128
h, w = A.shape
ys = np.where(A.any(1))[0]; y0, y1 = ys.min(), ys.max()
Y = np.arange(y0, y1 + 1)
lx = np.array([np.where(A[y])[0].min() for y in Y], float); rx = np.array([np.where(A[y])[0].max() + 1 for y in Y], float)
lx = nd.gaussian_filter1d(nd.median_filter(lx, 5), 1.2); rx = nd.gaussian_filter1d(nd.median_filter(rx, 5), 1.2)
# neck = straight sides, shoulders = quarter ellipses (same LV bottle as L22), measured on the cut-out
nk = (Y >= 522) & (Y < 596); lx[nk] = 730.0; rx[nk] = 915.5
sh = (Y >= 596) & (Y < 690); e = np.sqrt(np.clip(1 - ((690 - Y[sh])/95.0)**2, 0, 1))
lx[sh] = 730 - 79*e; rx[sh] = 915.5 + 79*e
S0, S1 = 690, 1135                                                  # straight body sides
sel = (Y >= S0) & (Y <= S1)
for arr in (lx, rx):
    p = np.polyfit(Y[sel], arr[sel], 1); arr[sel] = np.polyval(p, Y[sel])
poly = np.r_[np.c_[lx, Y], np.c_[rx, Y][::-1]]
big = np.zeros((h*K, w*K), np.uint8); cv2.fillPoly(big, [np.round(poly*K).astype(np.int32)], 255)
a = cv2.resize(big, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32)/255

inner = cv2.erode((a > 0.99).astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
gi = nd.distance_transform_edt(~inner, return_distances=False, return_indices=True)
rgb = np.where(((a > 0.01) & ~inner)[..., None], rgb[gi[0], gi[1]], rgb)

yy, xx = np.where(a > 0.02); Y0, Y1, X0, X1 = yy.min(), yy.max() + 1, xx.min(), xx.max() + 1
img = Image.fromarray((np.dstack([np.clip(rgb, 0, 1), a])[Y0:Y1, X0:X1]*255).astype(np.uint8), 'RGBA')
k = 900/img.height; img = img.resize((round(img.width*k), 900), Image.LANCZOS)
# soften the gold flakes on the plate seen through the inner glass column (text bands left untouched)
rgb9 = np.asarray(img.convert('RGB')).astype(np.float32)/255; hh, ww = rgb9.shape[:2]
bgm = cv2.GaussianBlur(cv2.medianBlur((rgb9*255).astype(np.uint8), 25).astype(np.float32)/255, (0, 0), 2)
dev = bgm.mean(2) - rgb9.mean(2)
reg = np.zeros((hh, ww), np.float32); reg[296:818, 122:274] = 1
for q0, q1 in ((470, 600), (655, 740)): reg[q0:q1] = 0
reg = cv2.GaussianBlur(reg, (0, 0), 3)
wg = cv2.GaussianBlur(np.clip((dev - 0.02)/0.06, 0, 1), (0, 0), 1.0)*reg*0.8
rgb9 = rgb9*(1 - wg[..., None]) + bgm*wg[..., None]
c3 = ImageEnhance.Color(Image.fromarray((np.clip(rgb9, 0, 1)*255).astype(np.uint8))).enhance(1.12)
c3 = ImageEnhance.Contrast(c3).enhance(1.10).filter(ImageFilter.UnsharpMask(1.3, 50, 2))
Image.merge('RGBA', (*c3.split(), img.getchannel('A'))).save(f'{OUT}/L10_УНИ.png'); print('L10_УНИ.png', img.size)
