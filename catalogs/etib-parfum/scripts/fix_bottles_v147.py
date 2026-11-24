"""v147: B5 Byredo — cap sides straight, shoulder below the cap a smooth symmetric curve;
N1 Nishane Hacivat — cap right edge recoloured from the clean cap face, alpha edge made straight.
Usage: fix_bottles_v147.py <B5 src dir> <N1 src dir> <out dir>"""
import sys, os, numpy as np, cv2
from PIL import Image
B5D, N1D, OUT = sys.argv[1:4]; os.makedirs(OUT, exist_ok=True)
def load(p): return np.array(Image.open(p).convert('RGBA')).astype(np.float32)
def save(im, n): Image.fromarray(np.clip(im, 0, 255).astype(np.uint8), 'RGBA').save(f'{OUT}/{n}.png')
# B5: cap sides made straight (no grey stepped fringe); shoulder outline below the cap a smooth curve from the cap corner
im = load(f'{B5D}/B5.png'); h, w = im.shape[:2]; K = 8; AX = 307.5; XL = 122.5; Y0, Y2 = 320.0, 353.0
a = im[..., 3]
for y in range(150, 321):                                  # straight cap sides, 1 px soft edge
    a[y, :int(XL) - 1] = 0; a[y, int(XL) - 1] = 0; a[y, int(XL)] = np.minimum(a[y, int(XL)], 128)
    xr = int(round(2*AX - XL)); a[y, xr + 1:] = 0; a[y, xr] = np.minimum(a[y, xr], 128)
    im[y, int(XL):int(XL) + 3, :3] = im[y, int(XL) + 3:int(XL) + 4, :3]; im[y, xr - 2:xr + 1, :3] = im[y, xr - 3:xr - 2, :3]
pts = [(XL + 1 - (XL + 1 - 5.0) * ((y - Y0) / (Y2 - Y0)) ** 2.2, y) for y in np.arange(Y0, Y2 + 0.01, 0.25)]
poly = [(XL + 1, Y0 - 2)] + pts + [(2*AX - x, y) for x, y in reversed(pts)] + [(2*AX - XL - 1, Y0 - 2)]
m = np.zeros((h*K, w*K), np.uint8)
cv2.fillPoly(m, [np.round(np.array(poly)*K).astype(np.int32)], 255, lineType=cv2.LINE_AA)
clip = cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32)/255
band = slice(int(Y0) + 1, int(Y2)); a[band] = np.minimum(a[band], 255*clip[band]); im[..., 3] = a; save(im, 'B5')
# N1: rows 100..292, cap right edge x>=431 — colour from the clean face, straight alpha edge
im = load(f'{N1D}/N1.png'); ys = slice(100, 293)
ref = im[ys, 426:430, :3].mean(axis=1, keepdims=True)
im[ys, 431:441, :3] = ref
ref_a = im[60, 425:441, 3].copy(); im[100:276, 425:441, 3] = ref_a
save(im, 'N1'); print('ok')
