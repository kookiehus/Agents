"""v145: owner's photo for Z1 Zadig & Voltaire This Is Her (white bottle on a white-cloud banner): exact geometry measured
on the photo — cap x 415.5..519, y 416..540; body x 312..638.5, y 537..1051, rounded corners. Edge colours from 3 px inside, light contrast and sharpening.
Usage: prepare_bottles_v145_z1.py <photo> <out dir>"""
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
a = np.maximum(rrect(415.5, 416.0, 519.0, 540.0, 4, 0), rrect(312.0, 537.0, 638.5, 1051.0, 8, 14))
inner = cv2.erode((a > 0.99).astype(np.uint8), np.ones((7, 7), np.uint8)).astype(bool)
gi = nd.distance_transform_edt(~inner, return_distances=False, return_indices=True)
rgb = np.where(((a > 0.01) & ~inner)[..., None], rgb[gi[0], gi[1]], rgb)
yy, xx = np.where(a > 0.02); Y0, Y1, X0, X1 = yy.min(), yy.max() + 1, xx.min(), xx.max() + 1
img = Image.fromarray((np.dstack([np.clip(rgb, 0, 1), a])[Y0:Y1, X0:X1]*255).astype(np.uint8), 'RGBA')
k = 900/img.height; img = img.resize((round(img.width*k), 900), Image.LANCZOS)
c3 = ImageEnhance.Color(img.convert('RGB')).enhance(1.08)
c3 = ImageEnhance.Contrast(c3).enhance(1.08).filter(ImageFilter.UnsharpMask(1.2, 40, 2))
Image.merge('RGBA', (*c3.split(), img.getchannel('A'))).save(f'{OUT}/Z1.png'); print('Z1.png', img.size)
