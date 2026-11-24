"""v113: owner's photo for C7 Carolina Herrera Good Girl (stiletto bottle on white).
rembg cut-out kept as is (the gap between the heel and the shoe stays open), holes inside the bottle filled, outline
lightly smoothed; edge colours from 2 px inside (no white halo), light contrast and sharpening.
Usage: prepare_bottles_v113.py <src> <rembg png> <out dir>"""
import sys, os, numpy as np, cv2
from PIL import Image, ImageFilter, ImageEnhance
from scipy import ndimage as nd
SRC, CUT, OUT = sys.argv[1:4]; os.makedirs(OUT, exist_ok=True)
im = Image.open(SRC).convert('RGB'); w0, h0 = im.size; S = 2                     # work at 2x for a smooth edge
rgb = np.array(im.resize((w0*S, h0*S), Image.LANCZOS)).astype(np.float32)/255
A = np.array(Image.open(CUT).getchannel('A').resize((w0*S, h0*S), Image.BILINEAR)) > 128
lab, n = nd.label(A); c = np.bincount(lab.ravel()); c[0] = 0; A = nd.binary_fill_holes(lab == np.argmax(c))
a = cv2.GaussianBlur(A.astype(np.float32), (0, 0), 1.4); a = np.clip((a - 0.5)*2.2 + 0.5, 0, 1)
inner = cv2.erode((a > 0.99).astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
gi = nd.distance_transform_edt(~inner, return_distances=False, return_indices=True)
rgb = np.where(((a > 0.01) & ~inner)[..., None], rgb[gi[0], gi[1]], rgb)
yy, xx = np.where(a > 0.02); Y0, Y1, X0, X1 = yy.min(), yy.max() + 1, xx.min(), xx.max() + 1
img = Image.fromarray((np.dstack([np.clip(rgb, 0, 1), a])[Y0:Y1, X0:X1]*255).astype(np.uint8), 'RGBA')
k = 900/img.height; img = img.resize((round(img.width*k), 900), Image.LANCZOS)
c3 = ImageEnhance.Color(img.convert('RGB')).enhance(1.08)
c3 = ImageEnhance.Contrast(c3).enhance(1.06).filter(ImageFilter.UnsharpMask(1.4, 50, 2))
Image.merge('RGBA', (*c3.split(), img.getchannel('A'))).save(f'{OUT}/C7_ЖЕН.png'); print('C7_ЖЕН.png', img.size)
