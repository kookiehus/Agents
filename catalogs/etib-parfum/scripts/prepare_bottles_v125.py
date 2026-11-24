"""v125: owner's new photo for T12 Trussardi Uomo (black bottle on black). rembg cannot see the black body, so the body is
exact geometry measured on the photo (rounded rectangle, x 164.5..862.5, top 475, bottom 1334); cap and neck from the
rembg cut-out above the shoulders. The gold (cap, crest, lettering) is toned to the deeper, more muted gold of the
previous T12 photo: Lab statistics of the gold pixels matched to the reference.
Usage: prepare_bottles_v125.py <new photo> <rembg png> <reference photo (old T12)> <out dir>"""
import sys, os, numpy as np, cv2
from PIL import Image, ImageFilter, ImageEnhance
from scipy import ndimage as nd
SRC, CUT, REF, OUT = sys.argv[1:5]; os.makedirs(OUT, exist_ok=True); K = 4
rgb = np.array(Image.open(SRC).convert('RGB')).astype(np.float32)/255; h, w = rgb.shape[:2]

def rrect(x0, y0, x1, y1, rt, rb):
    m = np.zeros((h*K, w*K), np.uint8); q = lambda v: int(round(v*K))
    cv2.rectangle(m, (q(x0), q(y0 + rt)), (q(x1), q(y1 - rb)), 255, -1)
    cv2.rectangle(m, (q(x0 + rt), q(y0)), (q(x1 - rt), q(y0 + rt)), 255, -1)
    cv2.rectangle(m, (q(x0 + rb), q(y1 - rb)), (q(x1 - rb), q(y1)), 255, -1)
    for cx, cy, r in ((x0 + rt, y0 + rt, rt), (x1 - rt, y0 + rt, rt), (x0 + rb, y1 - rb, rb), (x1 - rb, y1 - rb, rb)):
        cv2.circle(m, (q(cx), q(cy)), q(r), 255, -1, lineType=cv2.LINE_AA)
    return cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32)/255

body = rrect(164.5, 475.0, 862.5, 1334.0, 42, 22)
al = np.array(Image.open(CUT))[..., 3].astype(np.float32)/255
cap = (al > 0.5); cap[478:] = False
lab_, n = nd.label(cap); c = np.bincount(lab_.ravel()); c[0] = 0; cap = nd.binary_fill_holes(lab_ == np.argmax(c))
capa = cv2.GaussianBlur(cap.astype(np.float32), (0, 0), 0.8); capa = np.clip((capa - 0.5)*2.4 + 0.5, 0, 1)
a = np.maximum(body, capa)

# noble gold: match the gold pixels' Lab mean/std to the reference photo's gold
def gold_mask(x):
    hsv = cv2.cvtColor((x*255).astype(np.uint8), cv2.COLOR_RGB2HSV)
    return (hsv[..., 0] >= 10) & (hsv[..., 0] <= 32) & (hsv[..., 1] > 70) & (hsv[..., 2] > 50)
ref = np.array(Image.open(REF).convert('RGB')).astype(np.float32)/255
lr = cv2.cvtColor(ref, cv2.COLOR_RGB2LAB); ln = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
gr, gn = gold_mask(ref), gold_mask(rgb) & (a > 0.5)
out = ln.copy()
for ch in range(3):
    mr, sr = lr[..., ch][gr].mean(), lr[..., ch][gr].std(); mn, sn = ln[..., ch][gn].mean(), ln[..., ch][gn].std()
    print('ch', ch, 'ref', round(mr, 1), round(sr, 1), 'new', round(mn, 1), round(sn, 1))
    out[..., ch] = (ln[..., ch] - mn)*(sr/sn if ch == 0 else 1.0) + mr
wgt = cv2.GaussianBlur(gold_mask(rgb).astype(np.float32), (0, 0), 1.2)[..., None]
toned = np.clip(cv2.cvtColor(out.astype(np.float32), cv2.COLOR_LAB2RGB), 0, 1)
rgb = rgb*(1 - wgt) + toned*wgt

inner = cv2.erode((a > 0.99).astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
gi = nd.distance_transform_edt(~inner, return_distances=False, return_indices=True)
rgb = np.where(((a > 0.01) & ~inner)[..., None], rgb[gi[0], gi[1]], rgb)
yy, xx = np.where(a > 0.02); Y0, Y1, X0, X1 = yy.min(), yy.max() + 1, xx.min(), xx.max() + 1
img = Image.fromarray((np.dstack([np.clip(rgb, 0, 1), a])[Y0:Y1, X0:X1]*255).astype(np.uint8), 'RGBA')
k = 900/img.height; img = img.resize((round(img.width*k), 900), Image.LANCZOS)
c3 = img.convert('RGB').filter(ImageFilter.UnsharpMask(1.2, 40, 2))
Image.merge('RGBA', (*c3.split(), img.getchannel('A'))).save(f'{OUT}/T12.png'); print('T12.png', img.size)
