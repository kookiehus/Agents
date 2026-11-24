"""v145: cap top intersected with the rembg cut-out (argv[3]).
v143: owner's photo for D8 Dolce&Gabbana Devotion: exact geometry measured on the photo — cap rectangle
x 977.5..1181.5, y 191..516 with a rounded top; body x 858.5..1309, y 518..1294 with rounded corners. Edge colours from 3 px inside, light contrast and sharpening.
Usage: prepare_bottles_v143.py <photo> <out dir>"""
import sys, os, numpy as np, cv2
from PIL import Image, ImageFilter, ImageEnhance
from scipy import ndimage as nd
SRC, OUT = sys.argv[1:3]; os.makedirs(OUT, exist_ok=True); K = 4
rgb = np.array(Image.open(SRC).convert('RGB')).astype(np.float32)/255; h, w = rgb.shape[:2]
def rrect(x0, y0, x1, y1, rt, rb):
    m = np.zeros((h*K, w*K), np.uint8); q = lambda v: int(round(v*K))
    cv2.rectangle(m, (q(x0), q(y0 + rt)), (q(x1), q(y1 - rb)), 255, -1)
    cv2.rectangle(m, (q(x0 + rt), q(y0)), (q(x1 - rt), q(y0 + rt)), 255, -1)
    cv2.rectangle(m, (q(x0 + rb), q(y1 - rb)), (q(x1 - rb), q(y1)), 255, -1)
    for cx, cy, r in ((x0 + rt, y0 + rt, rt), (x1 - rt, y0 + rt, rt), (x0 + rb, y1 - rb, rb), (x1 - rb, y1 - rb, rb)):
        cv2.circle(m, (q(cx), q(cy)), q(r), 255, -1, lineType=cv2.LINE_AA)
    return cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32)/255
a = np.maximum(rrect(977.5, 191.0, 1181.5, 517.0, 12, 0), rrect(858.5, 518.0, 1309.0, 1294.0, 12, 26))
if len(sys.argv) > 3:                                                   # v145: cap top = the photo's own curved top (no white corners)
    rb = np.array(Image.open(sys.argv[3]))[..., 3].astype(np.float32)/255
    rb = cv2.GaussianBlur(nd.binary_erosion(rb > 0.6, iterations=2).astype(np.float32), (0, 0), 1.0)
    a[:240] = np.minimum(a[:240], rb[:240])
inner = cv2.erode((a > 0.99).astype(np.uint8), np.ones((7, 7), np.uint8)).astype(bool)
gi = nd.distance_transform_edt(~inner, return_distances=False, return_indices=True)
rgb = np.where(((a > 0.01) & ~inner)[..., None], rgb[gi[0], gi[1]], rgb)
yy, xx = np.where(a > 0.02); Y0, Y1, X0, X1 = yy.min(), yy.max() + 1, xx.min(), xx.max() + 1
img = Image.fromarray((np.dstack([np.clip(rgb, 0, 1), a])[Y0:Y1, X0:X1]*255).astype(np.uint8), 'RGBA')
k = 900/img.height; img = img.resize((round(img.width*k), 900), Image.LANCZOS)
c3 = ImageEnhance.Color(img.convert('RGB')).enhance(1.08)
c3 = ImageEnhance.Contrast(c3).enhance(1.08).filter(ImageFilter.UnsharpMask(1.2, 40, 2))
Image.merge('RGBA', (*c3.split(), img.getchannel('A'))).save(f'{OUT}/D8.png'); print('D8.png', img.size)
