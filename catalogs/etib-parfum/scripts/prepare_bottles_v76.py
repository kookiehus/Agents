"""v76: exact outlines for three bottles the owner flagged.
H4/H14 Hugo Woman: round flask = fitted circle (smooth edge), cap from the cut-out, red strap + metal ball from the cut-out
WITHOUT hole filling (the gap between strap and flask stays transparent).
G4 Acqua di Gioia: v75 outline pulled in 2 px and the light photo edge recoloured from inside (no white outline).
L8 La Vie Est Belle: cap down to its real bottom edge; ribbon = only pixels that differ from the grey backdrop, smoothed
(no grey leftovers between ribbon and bottle).
Usage: prepare_bottles_v76.py <data dir> <uploads v74 dir> <out dir>"""
import sys, os, numpy as np, cv2
from PIL import Image, ImageFilter, ImageEnhance
from scipy import ndimage as nd
D, UP, OUT = sys.argv[1:4]; os.makedirs(OUT, exist_ok=True); K = 4
def poly_mask(h, w, poly, r):
    m = np.zeros((h*K, w*K), np.uint8); cv2.fillPoly(m, [np.round(np.array(poly)*K).astype(np.int32)], 255)
    if r > 0:
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2*r*K + 1, 2*r*K + 1)); m = cv2.morphologyEx(m, cv2.MORPH_OPEN, k)
    return cv2.resize(m.astype(np.float32)/255, (w, h), interpolation=cv2.INTER_AREA)
def soft(m, sigma):
    p = cv2.GaussianBlur(m.astype(np.float32), (0, 0), sigma); return np.clip((p - 0.5)*2.2 + 0.5, 0, 1)
def fill_from(rgb, good, where):
    gi = nd.distance_transform_edt(~good, return_distances=False, return_indices=True)
    return np.where(where[..., None], rgb[gi[0], gi[1]], rgb)
def save(rgb, a, name, contrast=1.0):
    ys, xs = np.where(a > 0.02); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    img = Image.fromarray((np.dstack([np.clip(rgb, 0, 1), np.clip(a, 0, 1)])[y0:y1, x0:x1]*255).astype(np.uint8), 'RGBA')
    k = 900/img.height; img = img.resize((round(img.width*k), 900), Image.LANCZOS)
    c = ImageEnhance.Contrast(img.convert('RGB')).enhance(contrast).filter(ImageFilter.UnsharpMask(1.2, 40, 2))
    Image.merge('RGBA', (*c.split(), img.getchannel('A'))).save(f'{OUT}/{name}'); print(name, img.size)

# ---- H4 / H14 Hugo Woman
src = np.array(Image.open(f'{D}/bottles_site/H4_ЖЕН.png').convert('RGBA')).astype(np.float32)/255
rgb, al = src[..., :3], src[..., 3]; h, w = al.shape; m = al > 0.5
pts = []
for y in range(330, 830, 4):
    xs = np.where(m[y, :])[0]
    if len(xs): pts += [(xs[0], y), (xs[-1], y)]
P = np.array(pts, float); A = np.c_[2*P[:, 0], 2*P[:, 1], np.ones(len(P))]; bvec = (P**2).sum(1)
cx, cy, c0 = np.linalg.lstsq(A, bvec, rcond=None)[0]; R = np.sqrt(c0 + cx**2 + cy**2); print('circle', cx, cy, R)
big = np.zeros((h*K, w*K), np.uint8); cv2.circle(big, (int(cx*K), int(cy*K)), int((R - 0.5)*K), 255, -1, lineType=cv2.LINE_AA)
circ = cv2.resize(big.astype(np.float32)/255, (w, h), interpolation=cv2.INTER_AREA)
capm = m.copy(); capm[255:] = False; capm[:, :225] = False; capm[:, 445:] = False
cap = soft(nd.binary_opening(capm, iterations=2), 1.2)
yy, xx = np.mgrid[0:h, 0:w]
strap = m & (circ < 0.5) & (yy < 440) & (xx > 380)                                  # red strap + metal ball, gaps stay open
strap &= rgb.mean(axis=2) > 0.22                                                    # black specks of the old background
strap = nd.binary_opening(strap, iterations=1)
lab, n = nd.label(strap); sizes = np.bincount(lab.ravel()); sizes[0] = 0; strap = np.isin(lab, np.where(sizes > 400)[0])
a = np.maximum.reduce([circ, cap, soft(strap, 1.0)])
inside = (circ > 0.5) & (al < 0.5)                                                 # holes in the old cut-out inside the flask (label edges)
rgb = fill_from(rgb, m & (circ > 0.5), inside)
d = nd.distance_transform_edt(circ > 0.5); ring = (d < 4) & (circ > 0.5)          # ragged old edge -> colour from just inside
rgb = fill_from(rgb, (d >= 4) & m, ring & (al < 0.9))
save(rgb, a, 'H4_ЖЕН.png'); save(rgb, a, 'H14_ЖЕН.png')

# ---- G4 Acqua di Gioia: tighter outline, edge recoloured from inside
g = np.array(Image.open(f'{D}/bottles_v75/G4_ЖЕН.png').convert('RGBA')).astype(np.float32)/255
rgb, al = g[..., :3], g[..., 3]
core = al > 0.5; core = nd.binary_erosion(core, iterations=5)
a = soft(core, 1.0)
d = nd.distance_transform_edt(a > 0.5); band = 9
idx = nd.distance_transform_edt(~(d > band), return_distances=False, return_indices=True)
t = np.clip((band + 1 - d)/band, 0, 1)[..., None]
rgb = rgb*(1 - t) + rgb[idx[0], idx[1]]*0.88*t
rgb = rgb*(1 - 0.35*np.clip((3 - d)/3, 0, 1)[..., None])
save(rgb, a, 'G4_ЖЕН.png')

# ---- L8 La Vie Est Belle
im = np.array(Image.open(f'{UP}/L8.jpg').convert('RGB')).astype(np.float32)/255; h, w = im.shape[:2]
bg = np.median(im[:20, :20].reshape(-1, 3), axis=0); diff = np.abs(im - bg).max(axis=2)
body = poly_mask(h, w, [(545.5, 381.0), (1061.5, 381.0), (1061.5, 949.5), (545.5, 949.5)], 22)
cap = poly_mask(h, w, [(712.0, 147.0), (890.5, 147.0), (890.5, 300.0), (712.0, 300.0)], 4)
neck = poly_mask(h, w, [(737.0, 296.0), (865.0, 296.0), (865.0, 384.0), (737.0, 384.0)], 2)
rib = (diff > 16/255); rib[:236] = False; rib[395:] = False; rib[:, :868] = False
rib = nd.binary_opening(rib, iterations=2); lab, n = nd.label(rib); rib = lab == (np.argmax(np.bincount(lab.ravel())[1:]) + 1)
rib = nd.binary_fill_holes(nd.binary_closing(rib, iterations=2))
rib = soft(rib, 2.2)
a = np.maximum.reduce([body, cap, neck, rib])
save(im, a, 'L8_ЖЕН.png', contrast=1.08)
