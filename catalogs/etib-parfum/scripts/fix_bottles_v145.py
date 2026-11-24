"""v145: outline fixes on existing cut-outs.
D14 Sauvage Elixir: dark junk beside the cap base removed (cap rectangle + body rounded rectangle, measured).
V22 Incredible: ragged bottom replaced by smoothed, symmetric row extents.
D8 Devotion: cap top follows the photo's own curved top (no white corners).
Usage: fix_bottles_v145.py <data dir> <D8 photo> <D8 rembg> <out dir>"""
import sys, os, numpy as np, cv2
from PIL import Image
from scipy import ndimage as nd
D, D8SRC, D8RB, OUT = sys.argv[1:5]; os.makedirs(OUT, exist_ok=True); K = 4
def rrect(h, w, x0, y0, x1, y1, rt, rb):
    m = np.zeros((h*K, w*K), np.uint8); q = lambda v: int(round(v*K))
    cv2.rectangle(m, (q(x0), q(y0 + rt)), (q(x1), q(y1 - rb)), 255, -1)
    cv2.rectangle(m, (q(x0 + rt), q(y0)), (q(x1 - rt), q(y0 + rt)), 255, -1)
    cv2.rectangle(m, (q(x0 + rb), q(y1 - rb)), (q(x1 - rb), q(y1)), 255, -1)
    for cx, cy, r in ((x0 + rt, y0 + rt, rt), (x1 - rt, y0 + rt, rt), (x0 + rb, y1 - rb, rb), (x1 - rb, y1 - rb, rb)):
        if r > 0: cv2.circle(m, (q(cx), q(cy)), q(r), 255, -1, lineType=cv2.LINE_AA)
    return cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32)/255

# D14
im = np.array(Image.open(f'{D}/bottles_site/D14_МУЖ.png').convert('RGBA')).astype(np.float32); h, w = im.shape[:2]
clip = np.maximum(rrect(h, w, 109.5, 0, 387.5, 306, 3, 0), rrect(h, w, 2.5, 305.5, 500.0, 906, 16, 40))
im[..., 3] *= clip; Image.fromarray(np.clip(im, 0, 255).astype(np.uint8), 'RGBA').save(f'{OUT}/D14_МУЖ.png')

# V22
im = np.array(Image.open(f'{D}/bottles_v33/V22_ЖЕН.png').convert('RGBA')).astype(np.float32); h, w = im.shape[:2]
A = im[..., 3] > 128; Y = np.arange(560, h)
lx = np.array([np.where(A[y])[0].min() if A[y].any() else np.nan for y in Y]); rx = np.array([np.where(A[y])[0].max() + 1 if A[y].any() else np.nan for y in Y])
ok = ~np.isnan(lx); cx = np.median((lx[ok][:60] + rx[ok][:60])/2)
hw = np.where(ok, (rx - lx)/2, 0); hw = nd.gaussian_filter1d(nd.median_filter(hw, 9), 3.0)
ybot = Y[ok].max(); sel = Y <= ybot - 1
poly = np.r_[np.c_[cx - hw[sel], Y[sel]], np.c_[cx + hw[sel], Y[sel]][::-1]]
m = np.zeros((h*K, w*K), np.uint8); cv2.fillPoly(m, [np.round(poly*K).astype(np.int32)], 255)
low = cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32)/255
clip = np.ones((h, w), np.float32); clip[560:] = low[560:]
im[..., 3] *= clip; Image.fromarray(np.clip(im, 0, 255).astype(np.uint8), 'RGBA').save(f'{OUT}/V22_ЖЕН.png')
print('D14, V22 done')

# post-pass on the v145 outputs (run with argv[5] == 'post')
if len(sys.argv) > 5 and sys.argv[5] == 'post':
    p = f'{OUT}/D23.png'; im = np.array(Image.open(p)).astype(np.float32)          # neck between cap and shoulders: symmetric about the bottle axis
    xx = np.arange(im.shape[1])[None, :]; band = (xx >= 206.5) & (xx <= 357.5)
    im[202:231, :, 3] *= band; Image.fromarray(im.astype(np.uint8), 'RGBA').save(p)
    p = f'{OUT}/G25.png'; im = np.array(Image.open(p)).astype(np.float32)          # cap: outline pulled in 2 px (no light rim)
    er = cv2.erode(im[..., 3], np.ones((5, 5), np.uint8)); im[:300, :, 3] = np.minimum(im[:300, :, 3], er[:300])
    Image.fromarray(im.astype(np.uint8), 'RGBA').save(p)
    p = f'{OUT}/D8.png'; im = np.array(Image.open(p)).astype(np.float32)           # cap top: pulled in 2 px
    er = cv2.erode(im[..., 3], np.ones((5, 5), np.uint8)); im[:60, :, 3] = np.minimum(im[:60, :, 3], er[:60])
    Image.fromarray(im.astype(np.uint8), 'RGBA').save(p); print('post done')
