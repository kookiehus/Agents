"""v107: owner's photo for L22 Louis Vuitton Symphony (busy outdoor scene with fruit).
Glass = exact geometry measured on the photo: collar rim, neck, elliptical shoulders, slightly tapering sides and
an elliptical base (the mirror reflection on the marble is cut off). The silver sculpture cap comes from the rembg
cut-out above the collar. The garden and fruit seen through the clear glass are neutralised to the bottle's own
lavender (Lab a/b set to the glass colour, lightness kept), then levels and a light sharpen.
Usage: prepare_bottles_v107.py <L22.jpg> <rembg png> <out dir>"""
import sys, os, numpy as np, cv2
from PIL import Image, ImageFilter, ImageEnhance
from scipy import ndimage as nd
SRC, CUT, OUT = sys.argv[1:4]; os.makedirs(OUT, exist_ok=True)
rgb = np.array(Image.open(SRC).convert('RGB')).astype(np.float32)/255; h, w = rgb.shape[:2]
SS = 4
yy, xx = (np.mgrid[0:h*SS, 0:w*SS] + 0.5)/SS

def inside(x, y):
    m = np.zeros_like(x, bool)
    # collar rim and neck
    m |= (x >= 525) & (x <= 716) & (y >= 459) & (y <= 489)
    m |= (x >= 542.5) & (x <= 700) & (y >= 486) & (y <= 572)
    # shoulders: quarter ellipses, then sides tapering to the base
    lx = np.where(y < 665, 540 - 79*np.sqrt(np.clip(1 - ((665 - y)/105)**2, 0, 1)), 461 + (y - 665)*(16/435))
    rx = np.where(y < 665, 707 + 86*np.sqrt(np.clip(1 - ((665 - y)/105)**2, 0, 1)), 793 - (y - 665)*(18/435))
    base = 1100 + 47*np.sqrt(np.clip(1 - ((x - 626)/149)**2, 0, 1))
    m |= (y >= 560) & (x >= lx) & (x <= rx) & (y <= np.where(y >= 1100, base, 1e9))
    return m

glass = cv2.resize(inside(xx, yy).astype(np.float32), (w, h), interpolation=cv2.INTER_AREA)
del xx, yy
cut = np.array(Image.open(CUT))[..., 3].astype(np.float32)/255
capm = cut > 0.5; capm[462:] = False; capm[:, :350] = False; capm[:, 840:] = False
lab_, n = nd.label(capm); c = np.bincount(lab_.ravel()); c[0] = 0; capm = nd.binary_fill_holes(nd.binary_closing(lab_ == np.argmax(c), iterations=2))   # the sculpture is solid: dark reflections are not holes
cap = cv2.GaussianBlur(capm.astype(np.float32), (0, 0), 0.8); cap = np.clip((cap - 0.5)*2.4 + 0.5, 0, 1)
ring = np.zeros_like(cap); ring[438:462, 532:708] = 1; cap = np.maximum(cap, ring)
a = np.maximum(glass, cap); a[463:] = glass[463:]

# glass colour: lavender of the bottle body, lightness kept
lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
body = (glass > 0.99); body[:600] = False
A0, B0 = np.median(lab[..., 1][body]), np.median(lab[..., 2][body]); print('glass a,b', A0, B0)
g = (glass > 0)[..., None] & (np.arange(h)[:, None, None] >= 486)
L = lab[..., 0]; Ln = cv2.GaussianBlur(L, (0, 0), 1.0)
neutral = np.dstack([L, lab[..., 1]*0.25 + A0*0.75, lab[..., 2]*0.25 + B0*0.75])
dark = (L < 35)[..., None]                                         # black stopper inside the neck stays neutral
neutral = np.where(dark, np.dstack([L, lab[..., 1]*0.3, lab[..., 2]*0.3]), neutral)
lab = np.where(g, neutral, lab)
rgb = np.clip(cv2.cvtColor(lab, cv2.COLOR_LAB2RGB), 0, 1)
# silver cap: neutralise the green garden reflected in the chrome
capz = (cap > 0)[..., None] & (np.arange(h)[:, None, None] < 462)
grey = rgb.mean(2, keepdims=True)
rgb = np.where(capz, rgb*0.12 + grey*np.array([1.0, 1.0, 1.015])*0.88, rgb)
# edge colours from 2 px inside
inner = cv2.erode((a > 0.99).astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
gi = nd.distance_transform_edt(~inner, return_distances=False, return_indices=True)
rgb = np.where(((a > 0.01) & ~inner)[..., None], rgb[gi[0], gi[1]], rgb)

ys, xs = np.where(a > 0.02); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
img = Image.fromarray((np.dstack([np.clip(rgb, 0, 1), np.clip(a, 0, 1)])[y0:y1, x0:x1]*255).astype(np.uint8), 'RGBA')
k = 900/img.height; img = img.resize((round(img.width*k), 900), Image.LANCZOS)
c3 = ImageEnhance.Contrast(img.convert('RGB')).enhance(1.06).filter(ImageFilter.UnsharpMask(1.4, 50, 2))
Image.merge('RGBA', (*c3.split(), img.getchannel('A'))).save(f'{OUT}/L22_УНИ.png'); print('L22_УНИ.png', img.size)
