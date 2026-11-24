"""v124: handle openings found by flood fill of the plain backdrop inside each handle (no leftover blobs), widened 2 px
and smoothed; the rest as v121.
v121: owner's photo for P15 Paco Rabanne Invictus (trophy bottle on light grey).
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
L = rgb.mean(2)*255; sat = (rgb.max(2) - rgb.min(2))*255
sd = np.sqrt(np.maximum(cv2.blur(L*L, (5, 5)) - cv2.blur(L, (5, 5))**2, 0))
bgl = (np.abs(L - 242) < 9) & (sat < 10) & (sd < 4)
lab2, n2 = nd.label(bgl); keep = (lab2 == lab2[380, 745]) | (lab2 == lab2[380, 1420])   # the two openings
keep = nd.binary_closing(keep, iterations=3); keep = nd.binary_dilation(keep, iterations=2)
keep = cv2.GaussianBlur(keep.astype(np.float32), (0, 0), 1.5) > 0.5
m = nd.binary_fill_holes(m) & ~keep
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
