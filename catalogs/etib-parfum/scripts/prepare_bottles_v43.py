"""v43: A20 Antonio Banderas Blue Seduction for Women from the owner's photo (black background).
Outline = exact geometry measured on the photo: rounded-rectangle cap + slightly tapering glass body, both drawn
anti-aliased at 4x; straight sides fitted to the cut-out, corners rounded by a morphological opening.
Edge pixels take the colour found just inside (no black fringe); gentle levels/contrast like the other bottles.
Usage: prepare_bottles_v43.py <photo> <out png>"""
import sys, numpy as np, cv2
from PIL import Image, ImageFilter
from scipy import ndimage as nd
from rembg import remove, new_session
src, out = sys.argv[1:3]
im = Image.open(src).convert('RGB'); rgb = np.array(im).astype(np.float32)/255; h, w = rgb.shape[:2]
cut = np.array(remove(im, session=new_session('isnet-general-use')).getchannel('A')) > 128
K = 4
def fit_side(rows, side):
    xs = [np.where(cut[y])[0][0 if side == 'l' else -1] for y in rows]
    return np.polyfit(rows, xs, 1)
def shape(poly, r):
    m = np.zeros((h*K, w*K), np.uint8); cv2.fillPoly(m, [np.round(np.array(poly)*K).astype(np.int32)], 255)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2*r*K + 1, 2*r*K + 1))
    return cv2.morphologyEx(m, cv2.MORPH_OPEN, k)
# cap: x from the rows of the cap, top / bottom from the cut-out
capy0, capy1 = 152.5, 397.0
cl, cr = np.polyval(fit_side(range(175, 380), 'l'), 0), np.polyval(fit_side(range(175, 380), 'r'), 0)
cap = shape([(cl - 0.5, capy0), (cr + 0.5, capy0), (cr + 0.5, capy1), (cl - 0.5, capy1)], 6)
# body: sides fitted on the straight part, top / bottom rows from the cut-out
pl, pr = fit_side(range(440, 820), 'l'), fit_side(range(440, 820), 'r')
by0, by1 = 396.0, 846.5
X = lambda p, y, d: np.polyval(p, y) + d
body = shape([(X(pl, by0, -0.5), by0), (X(pr, by0, 0.5), by0), (X(pr, by1, 0.5), by1), (X(pl, by1, -0.5), by1)], 24)
m = np.maximum(cap, body)
a = cv2.resize(m.astype(np.float32)/255, (w, h), interpolation=cv2.INTER_AREA)
# colour of the edge band (outer 3 px) from just inside, so the black backdrop never shows as a fringe
core = nd.binary_erosion(a > 0.5, iterations=4)
idx = nd.distance_transform_edt(~core, return_distances=False, return_indices=True)
d = nd.distance_transform_edt(a > 0.5)
wgt = np.clip((4 - d)/3, 0, 1)[..., None]*(np.abs(rgb - rgb[idx[0], idx[1]]).max(axis=2, keepdims=True) > 0.10)
rgb = rgb*(1 - wgt) + rgb[idx[0], idx[1]]*wgt
solid = a > 0.6; bi = nd.distance_transform_edt(~solid, return_distances=False, return_indices=True)
rgb = np.where(solid[..., None], rgb, rgb[bi[0], bi[1]])
# colour: levels + soft S-curve, slightly richer turquoise, like the rest of the catalogue
lum = rgb.mean(axis=2); lo, hi = np.percentile(lum[a > 0.9], 1), np.percentile(lum[a > 0.9], 99.3)
rgb = np.clip((rgb - lo)/(hi - lo)*0.96 + 0.015, 0, 1); rgb = rgb + 0.25*(rgb*rgb*(3 - 2*rgb) - rgb)
g = rgb.mean(axis=2, keepdims=True); rgb = np.clip(g + (rgb - g)*1.10, 0, 1)
u8 = (rgb*255).astype(np.uint8); rgb = cv2.fastNlMeansDenoisingColored(u8, None, 3, 3, 5, 15).astype(np.float32)/255
ys, xs = np.where(a > 0.02); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
img = Image.fromarray((np.dstack([np.clip(rgb, 0, 1), np.clip(a, 0, 1)])[y0:y1, x0:x1]*255).astype(np.uint8), 'RGBA')
k = 900/img.height; img = img.resize((round(img.width*k), 900), Image.LANCZOS)
c = img.convert('RGB').filter(ImageFilter.UnsharpMask(1.2, 40, 2)); Image.merge('RGBA', (*c.split(), img.getchannel('A'))).save(out); print(img.size)
