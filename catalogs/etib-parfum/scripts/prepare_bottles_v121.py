"""v121: owner's photo for P15 Paco Rabanne Invictus (trophy bottle on light grey).
Mask = rembg cut-out (low threshold, clear glass included) with every inner hole filled EXCEPT the two openings
between the handles and the body, which stay see-through; lightly smoothed. Edge colours from 3 px inside.
Usage: prepare_bottles_v121.py <src> <rembg png> <out dir>"""
import sys, os, numpy as np, cv2
from PIL import Image, ImageFilter, ImageEnhance
from scipy import ndimage as nd
SRC, CUT, OUT = sys.argv[1:4]; os.makedirs(OUT, exist_ok=True)
rgb = np.array(Image.open(SRC).convert('RGB')).astype(np.float32)/255
al = np.array(Image.open(CUT))[..., 3]
m = al > 20; lab, n = nd.label(m); c = np.bincount(lab.ravel()); c[0] = 0; m = lab == np.argmax(c)
holes = nd.binary_fill_holes(m) & ~m; hl, hn = nd.label(holes); keep = np.zeros_like(m)
for i in range(1, hn + 1):
    ys, xs = np.where(hl == i)
    if len(ys) > 5000 and (xs.max() < 800 or xs.min() > 1370) and ys.min() < 260: keep |= hl == i   # handle openings
m = (m | holes) & ~keep
m = nd.binary_opening(m, iterations=2)
a = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.3); a = np.clip((a - 0.5)*2.2 + 0.5, 0, 1)
inner = cv2.erode((a > 0.99).astype(np.uint8), np.ones((7, 7), np.uint8)).astype(bool)
gi = nd.distance_transform_edt(~inner, return_distances=False, return_indices=True)
rgb = np.where(((a > 0.01) & ~inner)[..., None], rgb[gi[0], gi[1]], rgb)
yy, xx = np.where(a > 0.02); Y0, Y1, X0, X1 = yy.min(), yy.max() + 1, xx.min(), xx.max() + 1
img = Image.fromarray((np.dstack([np.clip(rgb, 0, 1), a])[Y0:Y1, X0:X1]*255).astype(np.uint8), 'RGBA')
k = 900/img.height; img = img.resize((round(img.width*k), 900), Image.LANCZOS)
c3 = ImageEnhance.Contrast(img.convert('RGB')).enhance(1.10).filter(ImageFilter.UnsharpMask(1.2, 50, 2))
Image.merge('RGBA', (*c3.split(), img.getchannel('A'))).save(f'{OUT}/P15.png'); print('P15.png', img.size)
