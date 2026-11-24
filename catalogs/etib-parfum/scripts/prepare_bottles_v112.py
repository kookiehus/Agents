"""v112: owner's photos for L19 Lanvin Modern Princess and L17 Lacoste L.12.12 White (studio shots).
Outline = per-row extents of the rembg cut-out, median + Gaussian smoothed, straight sides replaced by fitted lines,
drawn as a polygon at 4x (anti-aliased). Edge colours from 3 px inside, light contrast and sharpening.
Usage: prepare_bottles_v112.py <L19 src> <L19 rembg> <L17 src> <L17 rembg> <out dir>"""
import sys, os, numpy as np, cv2
from PIL import Image, ImageFilter, ImageEnhance
from scipy import ndimage as nd
K = 4; OUT = sys.argv[5]; os.makedirs(OUT, exist_ok=True)

def cut(src, rb, name, straight=(), sig=1.2, color=1.06, contrast=1.06):
    rgb = np.array(Image.open(src).convert('RGB')).astype(np.float32)/255; h, w = rgb.shape[:2]
    A = np.array(Image.open(rb))[..., 3] > 128
    lab, n = nd.label(A); c = np.bincount(lab.ravel()); c[0] = 0; A = nd.binary_fill_holes(lab == np.argmax(c))
    ys = np.where(A.any(1))[0]; Y = np.arange(ys.min(), ys.max() + 1)
    lx = np.array([np.where(A[y])[0].min() for y in Y], float); rx = np.array([np.where(A[y])[0].max() + 1 for y in Y], float)
    lx = nd.gaussian_filter1d(nd.median_filter(lx, 7), sig); rx = nd.gaussian_filter1d(nd.median_filter(rx, 7), sig)
    for f0, f1 in straight:                                           # source rows with straight sides
        sel = (Y >= f0) & (Y <= f1)
        for arr, d in ((lx, 1.0), (rx, -1.0)):
            arr[sel] = np.polyval(np.polyfit(Y[sel], arr[sel], 1), Y[sel]) + d
    poly = np.r_[np.c_[lx, Y], np.c_[rx, Y][::-1]]
    big = np.zeros((h*K, w*K), np.uint8); cv2.fillPoly(big, [np.round(poly*K).astype(np.int32)], 255)
    a = cv2.resize(big, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32)/255
    e = max(5, int(round(h/350))*2 + 1)
    inner = cv2.erode((a > 0.99).astype(np.uint8), np.ones((e, e), np.uint8)).astype(bool)
    gi = nd.distance_transform_edt(~inner, return_distances=False, return_indices=True)
    rgb = np.where(((a > 0.01) & ~inner)[..., None], rgb[gi[0], gi[1]], rgb)
    yy, xx = np.where(a > 0.02); Y0, Y1, X0, X1 = yy.min(), yy.max() + 1, xx.min(), xx.max() + 1
    img = Image.fromarray((np.dstack([np.clip(rgb, 0, 1), a])[Y0:Y1, X0:X1]*255).astype(np.uint8), 'RGBA')
    k = 900/img.height; img = img.resize((round(img.width*k), 900), Image.LANCZOS)
    c3 = ImageEnhance.Color(img.convert('RGB')).enhance(color)
    c3 = ImageEnhance.Contrast(c3).enhance(contrast).filter(ImageFilter.UnsharpMask(1.2, 40, 2))
    Image.merge('RGBA', (*c3.split(), img.getchannel('A'))).save(f'{OUT}/{name}'); print(name, img.size)

cut(sys.argv[1], sys.argv[2], 'L19_ЖЕН.png', sig=2.0, color=1.10)
cut(sys.argv[3], sys.argv[4], 'L17_МУЖ.png', straight=((50, 200), (208, 228), (380, 650)), sig=1.0, color=1.05, contrast=1.10)
