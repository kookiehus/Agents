"""v49: owner's photos for D24 Dior Homme Sport, P17 Black XS L'Exces, T12 Trussardi Uomo.
Outlines are exact geometry measured on each photo (drawn anti-aliased at 4x): straight sides fitted to the cut-out,
rounded corners, the domed cap of Black XS and the flared cap of Trussardi kept from the cut-out (smoothed).
Edge pixels take the colour found just inside (no white / black / pink fringe); gentle levels like the rest.
Usage: prepare_bottles_v49.py <uploads dir> <out dir>"""
import sys, os, numpy as np, cv2
from PIL import Image, ImageFilter
from scipy import ndimage as nd
from rembg import remove, new_session
UP, OUT = sys.argv[1:3]; os.makedirs(OUT, exist_ok=True)
sess = new_session('isnet-general-use'); K = 4

def load(name):
    im = Image.open(f'{UP}/{name}.jpg').convert('RGB')
    cut = np.array(remove(im, session=sess).getchannel('A')).astype(np.float32)/255
    return np.array(im).astype(np.float32)/255, cut

def fit(cut, rows, side):
    m = cut > 0.5; xs = [np.where(m[y])[0][0 if side == 'l' else -1] for y in rows if m[y].any()]
    ys = [y for y in rows if m[y].any()]; return np.polyfit(ys, xs, 1)

def poly_mask(h, w, poly, r):
    m = np.zeros((h*K, w*K), np.uint8); cv2.fillPoly(m, [np.round(np.array(poly)*K).astype(np.int32)], 255)
    if r > 0:
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2*r*K + 1, 2*r*K + 1)); m = cv2.morphologyEx(m, cv2.MORPH_OPEN, k)
    return m

def down(m, h, w): return cv2.resize(m.astype(np.float32)/255, (w, h), interpolation=cv2.INTER_AREA)

def smooth_part(cut, y0, y1, sigma=1.5):
    p = np.zeros_like(cut); p[y0:y1] = (cut[y0:y1] > 0.5)
    p = cv2.GaussianBlur(p, (0, 0), sigma); return np.clip((p - 0.5)*2.2 + 0.5, 0, 1)

def box(h, w, pl, pr, y0, y1, r):
    X = lambda p, y, d: np.polyval(p, y) + d
    return down(poly_mask(h, w, [(X(pl, y0, -.5), y0), (X(pr, y0, .5), y0), (X(pr, y1, .5), y1), (X(pl, y1, -.5), y1)], r), h, w)

def finish(rgb, a, name, rim=0.0, lift=1.0):
    core = nd.binary_erosion(a > 0.5, iterations=4)
    idx = nd.distance_transform_edt(~core, return_distances=False, return_indices=True)
    d = nd.distance_transform_edt(a > 0.5)
    wgt = np.clip((4 - d)/3, 0, 1)[..., None]*(np.abs(rgb - rgb[idx[0], idx[1]]).max(axis=2, keepdims=True) > 0.10)
    rgb = rgb*(1 - wgt) + rgb[idx[0], idx[1]]*wgt
    if rim:                                                     # thin even warm-grey rim so a black bottle stands off the dark panel
        sol = (a > 0.5).astype(np.uint8)
        rr = cv2.GaussianBlur((sol - cv2.erode(sol, np.ones((3, 3), np.uint8), iterations=2)).astype(np.float32), (0, 0), 0.8)*(a > 0.3)
        rgb = rgb*(1 - rim*rr[..., None]) + np.array([0.62, 0.60, 0.58])*rim*rr[..., None]
    solid = a > 0.6; bi = nd.distance_transform_edt(~solid, return_distances=False, return_indices=True)
    rgb = np.where(solid[..., None], rgb, rgb[bi[0], bi[1]])
    lum = rgb.mean(axis=2); lo, hi = np.percentile(lum[a > 0.9], 0.8), np.percentile(lum[a > 0.9], 99.5)
    rgb = np.clip((rgb - lo)/(hi - lo)*0.97*lift + 0.01, 0, 1); rgb = rgb + 0.2*(rgb*rgb*(3 - 2*rgb) - rgb)
    u8 = (np.clip(rgb, 0, 1)*255).astype(np.uint8); rgb = cv2.fastNlMeansDenoisingColored(u8, None, 3, 3, 5, 15).astype(np.float32)/255
    ys, xs = np.where(a > 0.02); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    img = Image.fromarray((np.dstack([np.clip(rgb, 0, 1), np.clip(a, 0, 1)])[y0:y1, x0:x1]*255).astype(np.uint8), 'RGBA')
    k = 900/img.height; img = img.resize((round(img.width*k), 900), Image.LANCZOS)
    c = img.convert('RGB').filter(ImageFilter.UnsharpMask(1.2, 40, 2))
    Image.merge('RGBA', (*c.split(), img.getchannel('A'))).save(f'{OUT}/{name}'); print(name, img.size)

# D24 Dior Homme Sport: one glass block, straight sides, softly rounded corners
rgb, cut = load('D24'); h, w = cut.shape
pl, pr = fit(cut, range(500, 1440, 4), 'l'), fit(cut, range(500, 1440, 4), 'r')
a = np.maximum(box(h, w, pl, pr, 72.5, 1474.0, 0), 0)
top = poly_mask(h, w, [(np.polyval(pl, 72.5) - .5, 72.5), (np.polyval(pr, 72.5) + .5, 72.5), (np.polyval(pr, 1474) + .5, 1474), (np.polyval(pl, 1474) - .5, 1474)], 16)
a = down(top, h, w)
finish(rgb, a, 'D24_МУЖ.png')

# P17 Black XS L'Exces: straight sides (the right edge is lost in the black backdrop, so it is fitted where visible),
# the domed cap top from the cut-out, rounded bottom corners
rgb, cut = load('P17'); h, w = cut.shape
pl = fit(cut, list(range(112, 300, 3)) + list(range(437, 780, 3)), 'l')
pr = fit(cut, list(range(112, 300, 3)) + list(range(437, 780, 3)), 'r')
# domed top: an elliptic arc through the apex and two points measured on the cap edge
from scipy.optimize import brentq
apex, cx = 31.0, (np.polyval(pl, 60) + np.polyval(pr, 60))/2
def arc(A): return lambda dx: 1 - np.sqrt(max(0.0, 1 - (dx/A)**2))
A = brentq(lambda A: arc(A)(150)/arc(A)(185) - 25/45, 186, 2000); B = 25/arc(A)(150)
xl, xr = np.polyval(pl, 120), np.polyval(pr, 120)
pts = [(x, apex + B*arc(A)(abs(x - cx))) for x in np.linspace(xl - .5, xr + .5, 200)]
poly = pts + [(np.polyval(pr, 966.5) + .5, 966.5), (np.polyval(pl, 966.5) - .5, 966.5)]
a = down(poly_mask(h, w, poly, 20), h, w)
finish(rgb, a, 'P17_МУЖ.png', rim=0.55, lift=1.0)

# T12 Trussardi Uomo: body = rounded rectangle, gold cap kept from the cut-out (smoothed)
rgb, cut = load('T12'); h, w = cut.shape
pl, pr = fit(cut, range(250, 540, 3), 'l'), fit(cut, range(250, 540, 3), 'r')
body = box(h, w, pl, pr, 214.0, 562.5, 28)
capm = smooth_part(cut, 78, 214, 1.2); capm[:, :160] = 0; capm[:, 292:] = 0
a = np.maximum(body, capm)
# pixels the outline adds where the photo shows the lily backdrop take the nearest bottle colour
own = (cut > 0.6) & (a > 0.5); ni = nd.distance_transform_edt(~own, return_distances=False, return_indices=True)
rgb = np.where(((a > 0.02) & ~own)[..., None], rgb[ni[0], ni[1]], rgb)
# the glossy edge mirrors the pink / green lilies: the outer 9 px of the black body become neutral grey (same lightness)
dd = nd.distance_transform_edt(body > 0.5); band = (np.clip((10 - dd)/3, 0, 1)*(body > 0.02))[..., None]
g = rgb.mean(axis=2, keepdims=True)*np.array([1.0, 0.99, 1.0]); rgb = rgb*(1 - band) + g*band
finish(rgb, a, 'T12_МУЖ.png')
